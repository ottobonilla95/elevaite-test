import {
  CommonModal,
  ElevaiteIcons,
  type CommonMenuItem,
} from "@repo/ui/components";
import { useEffect, useMemo, useState } from "react";
import { useSession } from "next-auth/react";
import { ListHeader } from "../../lib/components/ListHeader";
import {
  ListRow,
  specialHandlingListRowFields,
  type RowStructure,
} from "../../lib/components/ListRow";

import {
  type ExtendedUserObject,
  type SortingObject,
} from "../../lib/interfaces";

import { fetchCombinedUsers } from "../../lib/services/authUserService";
import { AddEditUser } from "./Add Edit Modals/AddEditUser";
import { AddEditUserRoles } from "./Add Edit Modals/AddEditUserRoles";
import { CreateUser } from "./Add Edit Modals/CreateUser";
import { ResetUserPassword } from "./Add Edit Modals/ResetUserPassword";
import { UserCreatedConfirmation } from "./Add Edit Modals/UserCreatedConfirmation";
import { UserRolesListRow } from "./smallParts/UserRolesListRow";

import "./UsersList.scss";

interface UsersListProps {
  isVisible: boolean;
  isSuperAdmin?: boolean;
}

export function UsersList(props: UsersListProps): JSX.Element {
  const { data: session } = useSession();
  const [displayUsers, setDisplayUsers] = useState<ExtendedUserObject[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sorting, setSorting] = useState<SortingObject<ExtendedUserObject>>({
    field: undefined,
  });
  const [isNamesModalOpen, setIsNamesModalOpen] = useState(false);
  const [isRolesModalOpen, setIsRolesModalOpen] = useState(false);
  const [isResetPasswordModalOpen, setIsResetPasswordModalOpen] =
    useState(false);
  const [isCreateUserModalOpen, setIsCreateUserModalOpen] = useState(false);
  const [isUserCreatedModalOpen, setIsUserCreatedModalOpen] = useState(false);
  const [createdUserEmail, setCreatedUserEmail] = useState("");
  const [createdUserMessage, setCreatedUserMessage] = useState("");
  const [selectedUser, setSelectedUser] = useState<
    ExtendedUserObject | undefined
  >();
  const [actionNotification, setActionNotification] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

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

  // Handler for action execution results
  const handleActionExecuted = (
    _actionId: string,
    success: boolean,
    message: string
  ) => {
    setActionNotification({
      message,
      type: success ? "success" : "error",
    });

    // Clear notification after 5 seconds
    setTimeout(() => {
      setActionNotification(null);
    }, 5000);

    // Refresh user list if action was successful
    if (success) {
      // Don't show loading spinner for refresh operations
      const refreshUsers = async () => {
        try {
          const users = await fetchCombinedUsers([]);
          setCombinedUsers(users);
        } catch (error) {
          console.error("Failed to refresh users:", error);
        }
      };
      void refreshUsers();
    }
  };

  // Generate dynamic menu for each user using the actual backend API
  const isCurrentUserSuperuser =
    props.isSuperAdmin ?? (session?.user as any)?.is_superuser === true;
  const isCurrentUserApplicationAdmin =
    (session?.user as any)?.application_admin === true;
  const isCurrentUserAnyAdmin =
    isCurrentUserSuperuser || isCurrentUserApplicationAdmin;

  const generateUserMenu = (
    user: ExtendedUserObject
  ): CommonMenuItem<ExtendedUserObject>[] => {
    const menuItems: CommonMenuItem<ExtendedUserObject>[] = [];

    // Both superusers and application admins can perform these actions
    menuItems.push({
      label: "Reset password",
      onClick: async () => {
        if (
          window.confirm(
            `Are you sure you want to reset the password for ${user.email}?`
          )
        ) {
          try {
            const { userActionsService } = await import(
              "../../lib/services/userActionsService"
            );
            const newPassword = userActionsService.generateSecurePassword();
            const result = await userActionsService.resetUserPassword(
              user,
              newPassword,
              true
            );

            handleActionExecuted(
              "reset-password",
              result.success,
              result.message
            );
          } catch (error) {
            handleActionExecuted(
              "reset-password",
              false,
              `Failed to reset password: ${error instanceof Error ? error.message : "Unknown error"}`
            );
          }
        }
      },
    });

    menuItems.push({
      label: "Unlock Account",
      onClick: async () => {
        if (
          window.confirm(
            `Are you sure you want to unlock the account for ${user.email}?`
          )
        ) {
          try {
            const { userActionsService } = await import(
              "../../lib/services/userActionsService"
            );
            const result = await userActionsService.unlockUserAccount(user);

            handleActionExecuted(
              "unlock-account",
              result.success,
              result.message
            );
          } catch (error) {
            handleActionExecuted(
              "unlock-account",
              false,
              `Failed to unlock account: ${error instanceof Error ? error.message : "Unknown error"}`
            );
          }
        }
      },
    });

    // Superuser-only actions
    if (isCurrentUserSuperuser) {
      menuItems.push({
        label: "Revoke MFA Devices",
        onClick: async () => {
          if (
            window.confirm(
              `Are you sure you want to revoke all MFA devices for ${user.email}? This will require them to set up MFA again.`
            )
          ) {
            try {
              const { userActionsService } = await import(
                "../../lib/services/userActionsService"
              );
              const result =
                await userActionsService.revokeUserMfaDevices(user);

              handleActionExecuted(
                "revoke-mfa-devices",
                result.success,
                result.message
              );
            } catch (error) {
              handleActionExecuted(
                "revoke-mfa-devices",
                false,
                `Failed to revoke MFA devices: ${error instanceof Error ? error.message : "Unknown error"}`
              );
            }
          }
        },
      });
    }

    return menuItems;
  };

  // Memoize per-user menus to stabilize menu options
  const rowMenus: Record<string, CommonMenuItem<ExtendedUserObject>[]> =
    useMemo(() => {
      const menus: Record<string, CommonMenuItem<ExtendedUserObject>[]> = {};
      for (const u of displayUsers) menus[u.id] = generateUserMenu(u);
      return menus;
    }, [displayUsers, isCurrentUserAnyAdmin, props.isVisible]);

  // State to store combined users (RBAC + Native Auth API)
  const [combinedUsers, setCombinedUsers] = useState<ExtendedUserObject[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  // Function to load users from auth API
  const loadUsers = async (): Promise<void> => {
    try {
      setIsLoadingUsers(true);
      const users = await fetchCombinedUsers([]);
      setCombinedUsers(users);
      setHasLoadedOnce(true);
    } catch (error) {
      console.error("Failed to load users:", error);
      // Even on error, we've attempted to load
      setHasLoadedOnce(true);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  // Update display users when combined users, search term, or sorting changes
  useEffect(() => {
    arrangeDisplayUsers();
  }, [
    combinedUsers,
    searchTerm,
    sorting,
    (session?.user as any)?.is_superuser,
    props.isVisible,
  ]);

  function arrangeDisplayUsers(): void {
    const usersClone = JSON.parse(
      JSON.stringify(combinedUsers)
    ) as ExtendedUserObject[];

    // Client-side permission filter:
    // - Superusers see everyone
    // - Application admins should not see superusers
    const isCurrentUserSuper = (session?.user as any)?.is_superuser === true;
    const baseList = isCurrentUserSuper
      ? usersClone
      : usersClone.filter((u) => !(u as any).is_superadmin);

    // Search
    const searchedList: ExtendedUserObject[] = searchTerm ? [] : baseList;
    if (searchTerm) {
      for (const item of baseList) {
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
    setIsCreateUserModalOpen(true);
  }

  function handleNameModalClose(): void {
    setSelectedUser(undefined);
    setIsNamesModalOpen(false);
  }

  function handleRolesModalClose(): void {
    setSelectedUser(undefined);
    setIsRolesModalOpen(false);
  }

  function handleResetPasswordModalClose(): void {
    setSelectedUser(undefined);
    setIsResetPasswordModalOpen(false);
  }

  function handleCreateUserModalClose(): void {
    setIsCreateUserModalOpen(false);
  }

  function handleUserCreatedModalClose(): void {
    setIsUserCreatedModalOpen(false);
  }

  function handleUserCreated(email: string, message?: string): void {
    setCreatedUserEmail(email);
    if (message) {
      setCreatedUserMessage(message);
    } else {
      setCreatedUserMessage("");
    }
    setIsCreateUserModalOpen(false);
    setIsUserCreatedModalOpen(true);

    // Refresh the users list to include the newly created user
    const refreshUsers = async () => {
      try {
        const users = await fetchCombinedUsers([]);
        setCombinedUsers(users);
      } catch (error) {
        console.error("Failed to refresh users after creation:", error);
      }
    };
    void refreshUsers();
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

      {actionNotification && (
        <div className={`action-notification ${actionNotification.type}`}>
          {actionNotification.message}
        </div>
      )}

      <div className="users-list-table-container">
        <ListRow<ExtendedUserObject>
          isHeader
          structure={usersListStructure}
          menu={[]}
          onSort={handleSort}
          sorting={sorting}
        />
        {isLoadingUsers || (!hasLoadedOnce && displayUsers.length === 0) ? (
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
              menu={rowMenus[user.id] || []}
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
            message={createdUserMessage}
          />
        </CommonModal>
      )}
      {!isResetPasswordModalOpen || !selectedUser ? null : (
        <CommonModal onClose={handleResetPasswordModalClose}>
          <ResetUserPassword
            user={selectedUser}
            onClose={handleResetPasswordModalClose}
            onSuccess={handleUserCreated}
          />
        </CommonModal>
      )}
    </div>
  );
}
