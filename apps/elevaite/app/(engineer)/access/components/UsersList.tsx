import {
  CommonModal,
  ElevaiteIcons,
  type CommonMenuItem,
} from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListHeader } from "../../../lib/components/ListHeader";
import {
  ListRow,
  specialHandlingListRowFields,
  type RowStructure,
} from "../../../lib/components/ListRow";
import { useRoles } from "../../../lib/contexts/RolesContext";
import {
  type ExtendedUserObject,
  type SortingObject,
} from "../../../lib/interfaces";
import { AddEditUser } from "./Add Edit Modals/AddEditUser";
import { AddEditUserRoles } from "./Add Edit Modals/AddEditUserRoles";
import { CreateUser } from "./Add Edit Modals/CreateUser";
import { UserCreatedConfirmation } from "./Add Edit Modals/UserCreatedConfirmation";
import { UserRolesListRow } from "./smallParts/UserRolesListRow";
import "./UsersList.scss";

enum menuActions {
  EDIT_NAMES = "Edit Names",
  EDIT_ROLES = "Edit Roles",
}

interface UsersListProps {
  isVisible: boolean;
}

export function UsersList(props: UsersListProps): JSX.Element {
  const rolesContext = useRoles();
  const [displayUsers, setDisplayUsers] = useState<ExtendedUserObject[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sorting, setSorting] = useState<SortingObject<ExtendedUserObject>>({
    field: undefined,
  });
  const [isNamesModalOpen, setIsNamesModalOpen] = useState(false);
  const [isRolesModalOpen, setIsRolesModalOpen] = useState(false);
  const [isCreateUserModalOpen, setIsCreateUserModalOpen] = useState(false);
  const [isUserCreatedModalOpen, setIsUserCreatedModalOpen] = useState(false);
  const [createdUserEmail, setCreatedUserEmail] = useState("");
  const [selectedUser, setSelectedUser] = useState<
    ExtendedUserObject | undefined
  >();

  const usersListStructure: RowStructure<ExtendedUserObject>[] = [
    { header: "First Name", field: "firstname", isSortable: true },
    { header: "Last Name", field: "lastname", isSortable: true },
    {
      header: "Email Address",
      field: "email",
      isSortable: true,
      specialHandling: specialHandlingListRowFields.EMAIL,
    },
    {
      header: "Roles",
      field: "displayRoles",
      isSortable: false,
      specialHandling: specialHandlingListRowFields.ROLES,
    },
  ];

  const usersListMenu: CommonMenuItem<ExtendedUserObject>[] = [
    {
      label: "Edit User name",
      onClick: (item: ExtendedUserObject) => {
        handleMenuClick(item, menuActions.EDIT_NAMES);
      },
    },
    {
      label: "Edit User roles",
      onClick: (item: ExtendedUserObject) => {
        handleMenuClick(item, menuActions.EDIT_ROLES);
      },
    },
  ];

  useEffect(() => {
    arrangeDisplayUsers();
  }, [rolesContext.users, searchTerm, sorting]);

  function arrangeDisplayUsers(): void {
    const usersClone = JSON.parse(
      JSON.stringify(rolesContext.users)
    ) as ExtendedUserObject[];

    // Add display roles

    // Search
    const searchedList: ExtendedUserObject[] = searchTerm ? [] : usersClone;
    if (searchTerm) {
      for (const item of usersClone) {
        if (item.firstname?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        if (item.lastname?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        if (item.email?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        // Add other checks here as desired.
      }
    }

    // Sort
    const sortedList: ExtendedUserObject[] = searchedList;
    if (sorting.field) {
      sortedList.sort((a, b) => {
        if (
          sorting.field &&
          typeof a[sorting.field] === "string" &&
          typeof b[sorting.field] === "string" &&
          !Array.isArray(a[sorting.field]) &&
          !Array.isArray(b[sorting.field])
        )
          return (a[sorting.field] as string).localeCompare(
            b[sorting.field] as string
          );
        return 0;
      });
      if (sorting.isDesc) {
        sortedList.reverse();
      }
    }

    // Set
    setDisplayUsers(sortedList);
  }

  function handleAddUser(): void {
    setIsCreateUserModalOpen(true);
  }

  function handleEditUser(user: ExtendedUserObject): void {
    setSelectedUser(user);
    setIsNamesModalOpen(true);
  }

  function handleEditUserRoles(user: ExtendedUserObject): void {
    setSelectedUser(user);
    setIsRolesModalOpen(true);
    // eslint-disable-next-line no-console -- Needed
    console.log("Editing user roles");
  }

  function handleNameModalClose(): void {
    setSelectedUser(undefined);
    setIsNamesModalOpen(false);
  }

  function handleRolesModalClose(): void {
    setSelectedUser(undefined);
    setIsRolesModalOpen(false);
  }

  function handleCreateUserModalClose(): void {
    setIsCreateUserModalOpen(false);
  }

  function handleUserCreatedModalClose(): void {
    setIsUserCreatedModalOpen(false);
  }

  function handleUserCreated(email: string): void {
    setCreatedUserEmail(email);
    setIsCreateUserModalOpen(false);
    setIsUserCreatedModalOpen(true);
  }

  function handleSearch(term: string): void {
    if (!props.isVisible) return;
    setSearchTerm(term);
  }

  function handleSort(field: keyof ExtendedUserObject): void {
    let sortingResult: SortingObject<ExtendedUserObject> = {};
    if (sorting.field !== field) sortingResult = { field };
    if (sorting.field === field) {
      if (sorting.isDesc) sortingResult = { field: undefined };
      else sortingResult = { field, isDesc: true };
    }
    setSorting(sortingResult);
  }

  function handleMenuClick(
    user: ExtendedUserObject,
    action: menuActions
  ): void {
    switch (action) {
      case menuActions.EDIT_NAMES:
        handleEditUser(user);
        break;
      case menuActions.EDIT_ROLES:
        handleEditUserRoles(user);
        break;
      default:
        break;
    }
  }

  return (
    <div className="users-list-container">
      <ListHeader
        label="Users List"
        addLabel="Add User"
        addIcon={<ElevaiteIcons.SVGCross />}
        addAction={handleAddUser}
        onSearch={handleSearch}
        searchPlaceholder="Search Users"
        isVisible={props.isVisible}
      />

      <div className="users-list-table-container">
        <ListRow<ExtendedUserObject>
          isHeader
          structure={usersListStructure}
          menu={usersListMenu}
          onSort={handleSort}
          sorting={sorting}
        />
        {displayUsers.length === 0 && rolesContext.loading.users ? (
          <div className="table-span empty">
            <ElevaiteIcons.SVGSpinner />
            <span>Loading...</span>
          </div>
        ) : displayUsers.length === 0 ? (
          <div className="table-span empty">There are no users to display.</div>
        ) : (
          displayUsers.map((user, index) => (
            <UserRolesListRow
              key={user.id}
              user={user}
              structure={usersListStructure}
              menu={usersListMenu}
              menuToTop={
                displayUsers.length > 4 && index > displayUsers.length - 4
              }
            />
          ))
        )}
      </div>

      {!isNamesModalOpen ? null : (
        <CommonModal onClose={handleNameModalClose}>
          <AddEditUser user={selectedUser} onClose={handleNameModalClose} />
        </CommonModal>
      )}
      {!isRolesModalOpen || !selectedUser ? null : (
        <CommonModal onClose={handleRolesModalClose}>
          <AddEditUserRoles
            user={selectedUser}
            onClose={handleRolesModalClose}
          />
        </CommonModal>
      )}
      {!isCreateUserModalOpen ? null : (
        <CommonModal onClose={handleCreateUserModalClose}>
          <CreateUser
            onClose={handleCreateUserModalClose}
            onSuccess={handleUserCreated}
          />
        </CommonModal>
      )}
      {!isUserCreatedModalOpen ? null : (
        <CommonModal onClose={handleUserCreatedModalClose}>
          <UserCreatedConfirmation
            email={createdUserEmail}
            onClose={handleUserCreatedModalClose}
          />
        </CommonModal>
      )}
    </div>
  );
}
