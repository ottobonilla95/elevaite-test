"use client";
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
import "./UsersList.scss";

enum menuActions {
  EDIT_NAMES = "Edit Names",
  EDIT_ROLES = "Edit Roles",
  RESET_PASSWORD = "Reset Password",
}

interface UsersListProps {
  isVisible: boolean;
}

export function UsersList(props: UsersListProps): JSX.Element {
  const rolesContext = useRoles();
  const [displayUsers, setDisplayUsers] = useState<ExtendedUserObject[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCurrentUserAdmin, setIsCurrentUserAdmin] = useState(false);
  const [sorting, setSorting] = useState<SortingObject<ExtendedUserObject>>({
    field: undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState<string>("");
  const [selectedUser, setSelectedUser] = useState<ExtendedUserObject | undefined>();

  const usersListStructure: RowStructure<ExtendedUserObject>[] = [
    { header: "First Name", field: "firstname", isSortable: true },
    { header: "Last Name", field: "lastname", isSortable: true },
    { header: "Email", field: "email", isSortable: true, specialHandling: specialHandlingListRowFields.EMAIL },
    { header: "Roles", field: "displayRoles", isSortable: false },
  ];

  const usersListMenu: CommonMenuItem<ExtendedUserObject>[] = [
    {
      label: "Edit Names",
      onClick: (item: ExtendedUserObject) => {
        handleMenuClick(item, menuActions.EDIT_NAMES);
      },
    },
    {
      label: "Edit Roles",
      onClick: (item: ExtendedUserObject) => {
        handleMenuClick(item, menuActions.EDIT_ROLES);
      },
    },
    {
      label: "Reset Password",
      onClick: (item: ExtendedUserObject) => {
        handleMenuClick(item, menuActions.RESET_PASSWORD);
      },
    },
  ];

  useEffect(() => {
    // For demo purposes, set admin to true
    setIsCurrentUserAdmin(true);
    arrangeDisplayUsers();
  }, [rolesContext.users, searchTerm, sorting]);

  function arrangeDisplayUsers(): void {
    const extendedUsers = getUsersWithRoleDetails(rolesContext.users);

    // Search
    const searchedList: ExtendedUserObject[] = searchTerm ? [] : extendedUsers;
    if (searchTerm) {
      for (const item of extendedUsers) {
        if (item.firstname?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        if (item.lastname?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        if (item.email.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
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
    setModalType("create");
    setIsModalOpen(true);
  }

  function handleModalClose(): void {
    setSelectedUser(undefined);
    setIsModalOpen(false);
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
    setSelectedUser(user);
    switch (action) {
      case menuActions.EDIT_NAMES:
        setModalType("edit_names");
        setIsModalOpen(true);
        break;
      case menuActions.EDIT_ROLES:
        setModalType("edit_roles");
        setIsModalOpen(true);
        break;
      case menuActions.RESET_PASSWORD:
        setModalType("reset_password");
        setIsModalOpen(true);
        break;
      default:
        break;
    }
  }

  function getUsersWithRoleDetails(
    users: ExtendedUserObject[]
  ): ExtendedUserObject[] {
    // This is a simplified version for the demo
    return users.map(user => ({
      ...user,
      displayRoles: user.is_superadmin 
        ? [{ roleLabel: "Admin" }] 
        : user.roles?.map(role => ({ roleLabel: role.name })) || []
    }));
  }

  function renderUserRoles(user: ExtendedUserObject): JSX.Element {
    if (user.is_superadmin) {
      return <div className="role-tag admin">Admin</div>;
    }
    
    return (
      <>
        {user.displayRoles?.map((role, index) => (
          <div key={index} className="role-tag">
            {role.roleLabel}
            {role.roleParent ? ` (${role.roleParent})` : ""}
          </div>
        ))}
      </>
    );
  }

  // Custom row component to display roles properly
  function UserRolesListRow(props: {
    user: ExtendedUserObject;
    structure: RowStructure<ExtendedUserObject>[];
    menu?: CommonMenuItem<ExtendedUserObject>[];
    menuToTop?: boolean;
  }): JSX.Element {
    const modifiedStructure = [...props.structure];
    
    // Replace the roles field with a custom rendering function
    const rolesIndex = modifiedStructure.findIndex(item => item.field === "displayRoles");
    if (rolesIndex >= 0) {
      modifiedStructure[rolesIndex] = {
        ...modifiedStructure[rolesIndex],
        formattingFunction: (user: ExtendedUserObject) => renderUserRoles(user)
      };
    }

    return (
      <ListRow<ExtendedUserObject>
        rowItem={props.user}
        structure={modifiedStructure}
        menu={props.menu}
        menuToTop={props.menuToTop}
      />
    );
  }

  return (
    <div className="users-list-container">
      <ListHeader
        label="Users List"
        addLabel={isCurrentUserAdmin ? "Add User" : undefined}
        addIcon={isCurrentUserAdmin ? <ElevaiteIcons.SVGCross /> : undefined}
        addAction={isCurrentUserAdmin ? handleAddUser : undefined}
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

      {!isModalOpen ? null : (
        <CommonModal onClose={handleModalClose}>
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">
              {modalType === "create" ? "Add User" : 
               modalType === "edit_names" ? "Edit User Names" :
               modalType === "edit_roles" ? "Edit User Roles" :
               modalType === "reset_password" ? "Reset User Password" : "User Action"}
            </h2>
            <p>This functionality is not implemented in this demo.</p>
            <button 
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={handleModalClose}
            >
              Close
            </button>
          </div>
        </CommonModal>
      )}
    </div>
  );
}
