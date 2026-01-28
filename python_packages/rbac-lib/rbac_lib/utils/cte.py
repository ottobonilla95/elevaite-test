from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, select, Integer, literal_column
from typing import List, Union
from uuid import UUID

from elevaitelib.orm.db import models


def is_user_project_association_till_root(
    db: Session, starting_project_id: UUID, user_id: UUID
):
    try:
        # Base part of the CTE: start from the given project and ensure there's a User_Project association
        base_cte = (
            select(
                models.Project.id.label("project_id"),
                models.Project.parent_project_id,
                literal_column("1", Integer).label("height"),  # Start height at 1
            )
            .join(
                models.User_Project,
                and_(
                    models.User_Project.project_id == models.Project.id,
                    models.User_Project.user_id == user_id,
                ),
            )
            .filter(models.Project.id == starting_project_id)
            .cte(name="ancestor_path", recursive=True)
        )

        # Aliases for the recursive part
        ancestor_cte = aliased(base_cte, name="ancestor")
        project_alias = aliased(models.Project, name="project")

        # Recursive part: move upwards in the project hierarchy, ensuring User_Project association at each step
        recursive_part = select(
            project_alias.id,
            project_alias.parent_project_id,
            (ancestor_cte.c.height + 1).label(
                "height"
            ),  # Increment height at each step
            # (ancestor_cte.c.read_permission_count + read_permission_case).label('read_permission_count') # conditionally increment read permission count if it exists
        ).select_from(
            ancestor_cte.join(
                project_alias, project_alias.id == ancestor_cte.c.parent_project_id
            ).join(
                models.User_Project,
                and_(
                    models.User_Project.project_id == project_alias.id,
                    models.User_Project.user_id == user_id,
                ),
            )
        )

        base_cte = base_cte.union_all(recursive_part)

        # Query the CTE, order by height to get the project with the greatest height
        last_project = db.query(base_cte).order_by(base_cte.c.height.desc()).first()

        # if last_project:
        #    print(f"last_project.height = {last_project.height}")

        # all_projects = db.query(base_cte).order_by(base_cte.c.height.desc()).all()
        # for project in all_projects:
        #    print(f'project.id = {project[0]}')
        #    print(f'project.parent_project_id = {project[1]}')
        #    print(f'project.height = {project[2]}')
        #    print('-------------------------')
        # if last_project:
        #    print(f'last_project.id = {last_project[0]}')
        #    print(f'last_project.parent_project_id = {last_project[1]}')
        #    print(f'last_project.height = {last_project[2]}')
        # Check if the last project (greatest height) is the root

        if last_project and last_project.parent_project_id is None:
            return True
        else:
            return False
    except SQLAlchemyError as e:
        db.rollback()
        print(f"INSIDE is_user_project_association_till_root method, DB Error : {e}")
        raise e
    except Exception as e:
        db.rollback()  # Roll back the transaction on any unexpected error
        print(
            f"INSIDE is_user_project_association_till_root method, unexpected error : {e}"
        )
        raise e


def delete_user_project_associations_for_subprojects_of_user_list(
    db: Session, starting_project_id: UUID, user_ids: List[UUID]
):
    delete_user_project_associations_for_subprojects(db, starting_project_id, user_ids)


def delete_user_project_associations_for_subprojects_of_user(
    db: Session, starting_project_id: UUID, user_id: UUID
):
    delete_user_project_associations_for_subprojects(db, starting_project_id, user_id)


def delete_user_project_associations_for_subprojects(
    db: Session, starting_project_id: UUID, user_id_or_user_ids: Union[List[UUID], UUID]
):
    try:
        # Define the base part of the CTE
        cte = (
            select(
                models.Project.id.label("project_id"),
            )
            .where(models.Project.id == starting_project_id)
            .cte(name="descendants", recursive=True)
        )

        # Define aliases for recursive part
        descendant_alias = aliased(cte, name="d")
        project_alias = aliased(models.Project, name="p")

        # Recursive part of the CTE
        union_query = select(
            project_alias.id.label("project_id"),
        ).select_from(
            descendant_alias.join(
                project_alias,
                project_alias.parent_project_id == descendant_alias.c.project_id,
            )
        )

        # Combine base and recursive parts
        cte = cte.union_all(union_query)

        if isinstance(user_id_or_user_ids, list):
            # If user_id_or_user_ids is a list, use the `in_` operator
            delete_query = db.query(models.User_Project).filter(
                models.User_Project.user_id.in_(user_id_or_user_ids),
                models.User_Project.project_id.in_(db.query(cte.c.project_id)),
            )
        else:
            # If user_id_or_user_ids is a single UUID, use the `==` operator
            delete_query = db.query(models.User_Project).filter(
                models.User_Project.user_id == user_id_or_user_ids,
                models.User_Project.project_id.in_(db.query(cte.c.project_id)),
            )
        delete_query.delete(synchronize_session=False)
        # print(f'deleted User_Project count = {delete_count}')
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print(
            f"INSIDE delete_user_project_associations_for_subprojects method, DB Error : {e}"
        )
        raise e
    except Exception as e:
        db.rollback()  # Roll back the transaction on any unexpected error
        print(
            f"INSIDE delete_user_project_associations_for_subprojects method, unexpected error : {e}"
        )
        raise e


def delete_unrooted_user_project_associations_in_account(
    db: Session,
    user_id: UUID,
    list_of_starting_project_ids: List[UUID],
    account_id: UUID,
):
    delete_unrooted_user_project_associations(
        db, user_id, list_of_starting_project_ids, account_id
    )


def delete_unrooted_user_project_associations_in_all_non_admin_accounts(
    db: Session, user_id: UUID, list_of_starting_project_ids: List[UUID]
):
    delete_unrooted_user_project_associations(db, user_id, list_of_starting_project_ids)


def delete_unrooted_user_project_associations(
    db: Session,
    user_id: UUID,
    list_of_starting_project_ids: List[UUID],
    account_id: Union[UUID, None] = None,
):
    try:
        # Define the base part of the CTE with multiple starting projects
        cte = (
            select(
                models.Project.id.label("project_id"),
            )
            .where(models.Project.id.in_(list_of_starting_project_ids))
            .cte(name="descendants", recursive=True)
        )

        # Define aliases for recursive part
        descendant_alias = aliased(cte, name="d")
        project_alias = aliased(models.Project, name="p")

        # Recursive part of the CTE: find all direct children of the current projects which user is associated with
        union_query = select(
            project_alias.id.label("project_id"),
        ).select_from(
            descendant_alias.join(
                project_alias,
                project_alias.parent_project_id == descendant_alias.c.project_id,
            ).join(
                models.User_Project,
                and_(
                    models.User_Project.project_id == project_alias.id,
                    models.User_Project.user_id == user_id,
                ),
            )
        )

        # Combine base and recursive parts
        cte = cte.union_all(union_query)

        # debug
        db.query(cte.c.project_id).all()
        # print("Rooted Project IDs:", [pid[0] for pid in associated_project_ids_from_top_level])

        # Perform a bulk delete for User_Project entries which are not a part of rooted user_project associations

        if (
            account_id
        ):  # if account_id exists, find the unrooted project associations in account
            subquery = (
                db.query(models.User_Project.id)
                .join(
                    models.Project, models.User_Project.project_id == models.Project.id
                )
                .filter(
                    models.User_Project.user_id == user_id,
                    models.Project.account_id == account_id,
                    models.User_Project.project_id.notin_(db.query(cte.c.project_id)),
                )
                .subquery()
            )
        else:  # if account_id does not exist, find the unrooted project associations in all non admin accounts
            subquery = (
                db.query(models.User_Project.id)
                .join(
                    models.Project, models.User_Project.project_id == models.Project.id
                )
                .join(
                    models.User_Account,
                    (
                        (models.User_Account.user_id == models.User_Project.user_id)
                        & (models.User_Account.account_id == models.Project.account_id)
                    ),
                )
                .filter(
                    models.User_Project.user_id == user_id,
                    not models.User_Account.is_admin,
                    models.User_Project.project_id.notin_(db.query(cte.c.project_id)),
                )
                .subquery()
            )

        # Debug subquery
        db.query(subquery.c.id).all()
        # print("Unrooted User-Project Association IDs to be deleted:", [upid[0] for upid in unrooted_project_association_ids])

        # Delete those User_Project entries using the IDs obtained above
        (
            db.query(models.User_Project)
            .filter(models.User_Project.id.in_(db.query(subquery.c.id)))
            .delete(synchronize_session=False)
        )

        db.commit()

        # print(f'deleted unrooted_user_project_association count = {deleted_unrooted_user_project_association_count}')
    except SQLAlchemyError as e:
        db.rollback()
        print(
            f"Inside delete_unrooted_user_project_associations - Error during bulk delete of User_Project entries : {e}"
        )
        raise e
    except Exception as e:
        db.rollback()
        print(
            f"Inside delete_unrooted_user_project_associations - Unexpected error: {e}"
        )
        raise e
