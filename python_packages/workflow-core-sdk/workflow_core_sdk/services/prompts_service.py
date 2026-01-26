from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import Session, select

from ..db.models import Prompt

if TYPE_CHECKING:  # for type checkers only, avoids runtime import cycles and F821
    from ..db.models import PromptCreate, PromptUpdate


@dataclass
class PromptsQuery:
    organization_id: Optional[str] = None
    app_name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tag: Optional[str] = None
    q: Optional[str] = None
    limit: int = 100
    offset: int = 0


class PromptsService:
    @staticmethod
    def list_prompts(session: Session, params: PromptsQuery) -> List[Prompt]:
        query = select(Prompt)
        if params.organization_id:
            query = query.where(Prompt.organization_id == params.organization_id)
        if params.app_name:
            query = query.where(Prompt.app_name == params.app_name)
        if params.provider:
            query = query.where(Prompt.ai_model_provider == params.provider)
        if params.model:
            query = query.where(Prompt.ai_model_name == params.model)
        if params.tag:
            # JSON/ARRAY contains (Postgres); safe no-op on other DBs if unsupported in PoC
            query = query.where(Prompt.tags.__contains__([params.tag]))
        if params.q:
            # Basic substring match; portable LIKE
            query = query.where(Prompt.prompt_label.like(f"%{params.q}%"))

        return session.exec(query.offset(params.offset).limit(params.limit)).all()

    @staticmethod
    def create_prompt(session: Session, prompt: PromptCreate) -> Prompt:
        # uniqueness by unique_label within org
        from ..db.models import (
            PromptCreate as _PC,
        )  # local import to avoid cycles in type hints

        data = prompt.model_dump() if isinstance(prompt, _PC) else dict(prompt)

        if data.get("organization_id"):
            existing = session.exec(
                select(Prompt).where(
                    Prompt.unique_label == data["unique_label"],
                    Prompt.organization_id == data["organization_id"],
                )
            ).first()
        else:
            existing = session.exec(
                select(Prompt)
                .where(Prompt.unique_label == data["unique_label"])
                .limit(1)
            ).first()
        if existing:
            raise ValueError("Prompt with this unique_label already exists")

        db_prompt = Prompt(**data)
        session.add(db_prompt)
        session.commit()
        session.refresh(db_prompt)
        return db_prompt

    @staticmethod
    def get_prompt(session: Session, prompt_id: str) -> Optional[Prompt]:
        from uuid import UUID

        return session.exec(select(Prompt).where(Prompt.id == UUID(prompt_id))).first()

    @staticmethod
    def update_prompt(
        session: Session, prompt_id: str, payload: PromptUpdate
    ) -> Prompt:
        from uuid import UUID
        from ..db.models import PromptUpdate as _PU

        db_prompt = session.exec(
            select(Prompt).where(Prompt.id == UUID(prompt_id))
        ).first()
        if not db_prompt:
            raise ValueError("Prompt not found")

        updates = (
            payload.model_dump(exclude_unset=True)
            if isinstance(payload, _PU)
            else dict(payload)
        )
        for k, v in updates.items():
            setattr(db_prompt, k, v)

        session.add(db_prompt)
        session.commit()
        session.refresh(db_prompt)
        return db_prompt

    @staticmethod
    def delete_prompt(session: Session, prompt_id: str) -> bool:
        from uuid import UUID

        db_prompt = session.exec(
            select(Prompt).where(Prompt.id == UUID(prompt_id))
        ).first()
        if not db_prompt:
            return False
        session.delete(db_prompt)
        session.commit()
        return True
