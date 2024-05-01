from datetime import datetime
from typing import Any, Dict, List, Optional, Annotated
import uuid
from pydantic import UUID4, Json
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Uuid,
    JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_json import MutableJson 

from ..util.func import get_utc_datetime
from ..schemas.instance import (
    InstancePipelineStepData,
    InstanceStatus,
)
from ..schemas.pipeline import PipelineStepStatus
from ..schemas.application import ApplicationType
from ..schemas.role import ProjectScopedPermission
from .database import Base

from sqlalchemy import (
    Column,
    DateTime,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    #    UUID,
    JSONB,
)

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    icon: Mapped[str]
    description: Mapped[str]
    version: Mapped[str]
    creator: Mapped[str]  # TODO: Check if this should be a relationship to the user
    applicationType: Mapped[ApplicationType] = mapped_column(Enum(ApplicationType))

    instances: Mapped[List["Instance"]] = relationship(back_populates="application")
    pipelines: Mapped["Pipeline"] = relationship("Pipeline")


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creator: Mapped[str]
    name: Mapped[str]
    comment: Mapped[Optional[str]]
    startTime: Mapped[Optional[str]]
    endTime: Mapped[Optional[str]]
    status: Mapped[InstanceStatus] = mapped_column(Enum(InstanceStatus))
    datasetId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("datasets.id"), nullable=False
    )
    selectedPipelineId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pipelines.id"), nullable=False
    )
    applicationId: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id"), nullable=False
    )
    configurationId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("configurations.id"), nullable=False
    )
    projectId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False
    )
    configurationRaw = Column(JSON)

    chartData: Mapped["InstanceChartData"] = relationship(
        back_populates="instance", uselist=False
    )
    pipelineStepStatuses: Mapped[List["InstancePipelineStepStatus"]] = relationship(
        back_populates="instance"
    )

    application: Mapped[Application] = relationship(
        back_populates="instances", uselist=False
    )
    project: Mapped["Project"] = relationship(uselist=False)
    dataset: Mapped["Dataset"] = relationship(uselist=False)
    configuration: Mapped["Configuration"] = relationship(back_populates="instances")


class InstanceChartData(Base):
    __tablename__ = "instance_chart_data"

    instanceId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instances.id"), primary_key=True
    )

    totalItems: Mapped[int] = mapped_column(default=0)
    ingestedItems: Mapped[int] = mapped_column(default=0)
    avgSize: Mapped[int] = mapped_column(default=0)
    totalSize: Mapped[int] = mapped_column(default=0)
    ingestedSize: Mapped[int] = mapped_column(default=0)
    ingestedChunks: Mapped[int] = mapped_column(default=0)

    instance: Mapped[Instance] = relationship(back_populates="chartData")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipeline_steps.id"))
    exit: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipeline_steps.id"))
    label: Mapped[str] = mapped_column()
    applicationId: Mapped[int] = mapped_column(ForeignKey("applications.id"))

    steps: Mapped[list["PipelineStep"]] = relationship(
        back_populates="pipeline",
        primaryjoin="Pipeline.id==PipelineStep.pipelineId",
    )


pipeline_step_deps = Table(
    "pipeline_step_deps",
    Base.metadata,
    Column("source_id", Uuid, ForeignKey("pipeline_steps.id")),
    Column("target_id", Uuid, ForeignKey("pipeline_steps.id")),
)


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"
    id: Mapped[UUID4] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str]
    pipelineId: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pipelines.id"))
    # parent_id = Column(String, ForeignKey("pipeline_steps.id"))

    data: Mapped[List["PipelineStepData"]] = relationship(
        back_populates="step", uselist=True
    )
    pipeline: Mapped[Pipeline] = relationship(
        back_populates="steps", foreign_keys=[pipelineId]
    )

    @hybrid_property
    def previousStepIds(self) -> List[UUID4]:
        return [x.id for x in self._dependsOn]

    @hybrid_property
    def nextStepIds(self) -> list[UUID4]:
        return [x.id for x in self._dependedOn]

    _dependsOn = relationship(
        "PipelineStep",
        secondary=pipeline_step_deps,
        primaryjoin=(pipeline_step_deps.c.target_id == id),
        secondaryjoin=(pipeline_step_deps.c.source_id == id),
        backref="_dependedOn",
    )
    # dependedOn = relationship("PipelineStepDependencies", back_populates="target")


class PipelineStepData(Base):
    __tablename__ = "pipeline_step_data"

    stepId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pipeline_steps.id"), primary_key=True
    )
    title: Mapped[str]
    value: Mapped[str]

    step: Mapped[PipelineStep] = relationship()


# class PipelineStepDependencies(Base):
#     __tablename__ = "pipeline_step_dependencies"

#     source_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)
#     target_id = Column(String, ForeignKey("pipeline_steps.id"), primary_key=True)

#     source = relationship("PipelineStep", back_populates="dependsOn")
#     target = relationship("PipelineStep", back_populates="dependedOn")


class InstancePipelineStepStatus(Base):
    __tablename__ = "instance_pipeline_step_statuses"

    instanceId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instances.id"), primary_key=True
    )
    stepId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pipeline_steps.id"), primary_key=True
    )
    status: Mapped[PipelineStepStatus] = mapped_column(Enum(PipelineStepStatus))
    startTime: Mapped[Optional[str]]
    endTime: Mapped[Optional[str]]
    meta: Mapped[list[InstancePipelineStepData]] = mapped_column(
        MutableJson, default=[]
    )

    instance = relationship("Instance", back_populates="pipelineStepStatuses")


class Configuration(Base):
    __tablename__ = "configurations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    applicationId: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    name: Mapped[str] = mapped_column(String, unique=True)
    createDate: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updateDate: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, onupdate=get_utc_datetime
    )
    isTemplate: Mapped[bool]
    raw: Mapped[Json] = mapped_column(JSONB)

    instances: Mapped[List[Instance]] = relationship(
        back_populates="configuration", uselist=True
    )
    application: Mapped[Application] = relationship("Application")


class DatasetTag(Base):
    __tablename__ = "dataset_tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]


dataset_dataset_tags = Table(
    "dataset_dataset_tags",
    Base.metadata,
    Column("dataset_id", Uuid, ForeignKey("datasets.id")),
    Column("tag_id", Uuid, ForeignKey("dataset_tags.id")),
)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    projectId: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id"))
    createDate: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updateDate: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, onupdate=get_utc_datetime
    )

    project: Mapped["Project"] = relationship(back_populates="datasets")
    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset")
    tags: Mapped[list["DatasetTag"]] = relationship(secondary=dataset_dataset_tags)


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    commitId: Mapped[str] = mapped_column()
    version: Mapped[int] = mapped_column()
    datasetId = mapped_column(ForeignKey("datasets.id"))
    createDate: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")


# ------------- Merged project defn -----------------
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )  # Project can only be created inside an account
    creator: Mapped[str] = mapped_column(String(254), nullable=False)
    parent_project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )  # Projects can have null parents when created directly from account
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    # --------- LOGICAL RELATIONSHIPS BASED ON FOREIGN KEYS-----------
    account = relationship(
        "Account", back_populates="projects", foreign_keys=[account_id]
    )  # many-to-one: many projects can belong to 1 account
    parent = relationship(
        "Project", remote_side=[id], back_populates="children", uselist=False
    )  # Self-referential many-to-one ; many children to one parent
    children = relationship(
        "Project", back_populates="parent"
    )  # Self-referential one-to-many; one parent to many children
    users = relationship(
        "User", secondary="user_project", back_populates="projects"
    )  # many-to-many: many users can have many projects

    datasets = relationship("Dataset", back_populates="project")
    collections = relationship("Collection", back_populates="project")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    projectId = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="collections")


# Association table for the many-to-many relationship between User and Account; used for targeting a user in an account.
# Defined as a class and not a Table to allow for use of Mapped[] annotation for compatibility with static type checkers in orm-to-python conversions.
class User_Account(Base):
    __tablename__ = "user_account"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id")
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    __table_args__ = (
        UniqueConstraint("user_id", "account_id", name="_user_account_uc"),
    )  # Add a unique constraint for the combination of user_id and account_id

    role_user_accounts = relationship(
        "Role_User_Account",
        cascade="delete, delete-orphan",
        back_populates="user_account",
    )


# Association table for the many-to-many relationship between User and Project; used for targeting a user in a project
# Defined as a class and not a Table to allow for use of Mapped[] annotation for compatibility with static type checkers in orm-to-python conversions.
class User_Project(Base):

    __tablename__ = "user_project"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id")
    )
    permission_overrides: Mapped[Annotated[dict[str, Any], Column(JSONB)]] = (
        mapped_column(type_=JSONB, default=lambda: ProjectScopedPermission().dict())
    )  # Use JSONB for filterable and indexable JSON structure
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="_user_project_uc"),
    )  # Add a unique constraint for the combination of user_id and project_id


# Association table for the many-to-many relationship between Role and User_Account; used for connecting a specific user in an account to the role table to assign account-specific role-based permissions
# Defined as a class and not a Table to allow for use of Mapped[] annotation for compatibility with static type checkers in orm-to-python conversions.
class Role_User_Account(Base):
    __tablename__ = "role_user_account"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4()
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=False
    )
    user_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    __table_args__ = (
        UniqueConstraint("role_id", "user_account_id", name="_role_useracc_uc"),
    )  # Add a unique constraint for the combination of role_id and user_account_id

    user_account = relationship("User_Account", back_populates="role_user_accounts")


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    accounts = relationship(
        "Account", back_populates="organization"
    )  # One-to-many relationship: An organization can have multiple accounts


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )  # Adding FK to Organization
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "name", "organization_id", name="uc_account_name_organization_id"
        ),
    )

    # --------- LOGICAL RELATIONSHIPS BASED ON FOREIGN KEYS -----------
    organization = relationship(
        "Organization", back_populates="accounts", foreign_keys=[organization_id]
    )  # many-to-one: many accounts can belong to 1 organization
    users = relationship(
        "User", secondary="user_account", back_populates="accounts"
    )  #  many-to-many: A user can belong to multiple accounts, an account can have multiple users
    projects = relationship(
        "Project", back_populates="account"
    )  # one-to-many : one account can have many projects


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )  # Adding FK to Organization
    firstname: Mapped[str] = mapped_column(String(60), nullable=True)
    lastname: Mapped[str] = mapped_column(String(60), nullable=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    # --------- LOGICAL RELATIONSHIPS BASED ON FOREIGN KEYS-----------
    accounts = relationship(
        "Account", secondary="user_account", back_populates="users"
    )  # many-to-many: A user can belong to multiple accounts, an account can have multiple users
    projects = relationship(
        "Project", secondary="user_project", back_populates="users"
    )  # many-to-many: many users can have many projects
    # overriding_role = relationship('Role', back_populates='user_overrides', foreign_keys=[overriding_role_id]) # many-to-one: one role can be an override for multiple users
    api_keys = relationship("APIKey", back_populates="user")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )  # 'DATA_SCIENTIST'
    permissions = Column(JSONB)  # Use JSONB for filterable and indexable JSON structure
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    # --------- LOGICAL RELATIONSHIPS BASED ON FOREIGN KEYS-----------
    # user_account_overrides = relationship('User_Account', back_populates='overriding_role')
    # user_project_overrides = relationship('User_Project', back_populates='overriding_role')
    # user_overrides = relationship('User', back_populates='overriding_role')


class APIKey(Base):
    __tablename__ = "apikeys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )  # Assuming key should be unique
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    # --------- LOGICAL RELATIONSHIPS BASED ON FOREIGN KEYS-----------
    user = relationship("User", back_populates="api_keys")  #
