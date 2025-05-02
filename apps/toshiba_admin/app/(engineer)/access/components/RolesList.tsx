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
import { type RoleObject, type SortingObject } from "../../../lib/interfaces";
import {
  type DisplayPermission,
  getDisplayPermissions,
} from "../../../lib/rbacHelpers";
import "./RolesList.scss";

enum menuActions {
  EDIT = "Edit",
}

interface RolesListProps {
  isVisible: boolean;
}

export function RolesList(props: RolesListProps): JSX.Element {
  const rolesContext = useRoles();
  const [displayRoles, setDisplayRoles] = useState<RoleObject[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sorting, setSorting] = useState<SortingObject<RoleObject>>({
    field: undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<RoleObject | undefined>();
  const [selectedRolePermissions, setSelectedRolePermissions] = useState<
    DisplayPermission[]
  >([]);

  const rolesListStructure: RowStructure<RoleObject>[] = [
    { header: "Role Name", field: "name", isSortable: true },
    {
      header: "Create",
      field: "permissions",
      specialHandling: specialHandlingListRowFields.PERMISSIONS,
      formattingFunction: (role: RoleObject) => {
        const permissions = getDisplayPermissions(role);
        return permissions.length > 0 && permissions[0].canCreate ? (
          <div className="permission-field green">YES</div>
        ) : (
          <div className="permission-field red">NO</div>
        );
      },
    },
    {
      header: "Read",
      field: "permissions",
      specialHandling: specialHandlingListRowFields.PERMISSIONS,
      formattingFunction: (role: RoleObject) => {
        const permissions = getDisplayPermissions(role);
        return permissions.length > 0 && permissions[0].canRead ? (
          <div className="permission-field green">YES</div>
        ) : (
          <div className="permission-field red">NO</div>
        );
      },
    },
    {
      header: "Update",
      field: "permissions",
      specialHandling: specialHandlingListRowFields.PERMISSIONS,
      formattingFunction: (role: RoleObject) => {
        const permissions = getDisplayPermissions(role);
        return permissions.length > 0 && permissions[0].canUpdate ? (
          <div className="permission-field green">YES</div>
        ) : (
          <div className="permission-field red">NO</div>
        );
      },
    },
    {
      header: "Delete",
      field: "permissions",
      specialHandling: specialHandlingListRowFields.PERMISSIONS,
      formattingFunction: (role: RoleObject) => {
        const permissions = getDisplayPermissions(role);
        return permissions.length > 0 && permissions[0].canDelete ? (
          <div className="permission-field green">YES</div>
        ) : (
          <div className="permission-field red">NO</div>
        );
      },
    },
  ];

  const rolesListMenu: CommonMenuItem<RoleObject>[] = [
    {
      label: "Edit Role",
      onClick: (item: RoleObject) => {
        handleMenuClick(item, menuActions.EDIT);
      },
    },
  ];

  useEffect(() => {
    arrangeDisplayRoles();
  }, [rolesContext.roles, searchTerm, sorting]);

  function arrangeDisplayRoles(): void {
    // Search
    const searchedList: RoleObject[] = searchTerm ? [] : rolesContext.roles;
    if (searchTerm) {
      for (const item of rolesContext.roles) {
        if (item.name.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
      }
    }

    // Sort
    const sortedList: RoleObject[] = searchedList;
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
    setDisplayRoles(sortedList);
  }

  function handleAddRole(): void {
    setIsModalOpen(true);
  }

  function handleEditRole(role: RoleObject): void {
    setSelectedRole(role);
    setSelectedRolePermissions(getDisplayPermissions(role));
    setIsModalOpen(true);
  }

  function handleModalClose(): void {
    setSelectedRole(undefined);
    setSelectedRolePermissions([]);
    setIsModalOpen(false);
  }

  function handleSearch(term: string): void {
    if (!props.isVisible) return;
    setSearchTerm(term);
  }

  function handleSort(field: keyof RoleObject): void {
    let sortingResult: SortingObject<RoleObject> = {};
    if (sorting.field !== field) sortingResult = { field };
    if (sorting.field === field) {
      if (sorting.isDesc) sortingResult = { field: undefined };
      else sortingResult = { field, isDesc: true };
    }
    setSorting(sortingResult);
  }

  function handleMenuClick(role: RoleObject, action: menuActions): void {
    switch (action) {
      case menuActions.EDIT:
        handleEditRole(role);
        break;
      default:
        break;
    }
  }

  function renderRoleCard(): JSX.Element {
    return (
      <div className="role-card">
        <h3 className="text-lg font-semibold mb-4">Role Permissions</h3>
        {selectedRolePermissions.map((permission, index) => (
          <div key={index} className="permission-item mb-2">
            <div className="font-medium">{permission.entity}</div>
            <div className="flex gap-2 mt-1">
              <span className={`permission-tag ${permission.canCreate ? 'green' : 'red'}`}>
                Create: {permission.canCreate ? 'Yes' : 'No'}
              </span>
              <span className={`permission-tag ${permission.canRead ? 'green' : 'red'}`}>
                Read: {permission.canRead ? 'Yes' : 'No'}
              </span>
              <span className={`permission-tag ${permission.canUpdate ? 'green' : 'red'}`}>
                Update: {permission.canUpdate ? 'Yes' : 'No'}
              </span>
              <span className={`permission-tag ${permission.canDelete ? 'green' : 'red'}`}>
                Delete: {permission.canDelete ? 'Yes' : 'No'}
              </span>
            </div>
            {permission.type.length > 0 && (
              <div className="ml-4 mt-1">
                <div className="text-sm text-gray-500">Types:</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {permission.type.map((type, typeIndex) => (
                    <span key={typeIndex} className="type-tag">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="roles-list-container">
      <div className="roles-main-list">
        <ListHeader
          label="Roles List"
          addLabel="Add Role"
          addIcon={<ElevaiteIcons.SVGCross />}
          addAction={handleAddRole}
          onSearch={handleSearch}
          searchPlaceholder="Search Roles"
          isVisible={props.isVisible}
        />

        <div className="roles-list-table-container">
          <ListRow<RoleObject>
            isHeader
            structure={rolesListStructure}
            menu={rolesListMenu}
            onSort={handleSort}
            sorting={sorting}
          />
          {displayRoles.length === 0 && rolesContext.loading.roles ? (
            <div className="table-span empty">
              <ElevaiteIcons.SVGSpinner />
              <span>Loading...</span>
            </div>
          ) : displayRoles.length === 0 ? (
            <div className="table-span empty">
              There are no roles to display.
            </div>
          ) : (
            displayRoles.map((role, index) => (
              <ListRow<RoleObject>
                key={role.id}
                rowItem={role}
                structure={rolesListStructure}
                menu={rolesListMenu}
                menuToTop={
                  displayRoles.length > 4 && index > displayRoles.length - 4
                }
              />
            ))
          )}
        </div>
      </div>

      {!isModalOpen ? null : (
        <CommonModal onClose={handleModalClose}>
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">
              {selectedRole ? `Edit Role: ${selectedRole.name}` : "Add Role"}
            </h2>
            {selectedRole && renderRoleCard()}
            <p className="mt-4">This functionality is not fully implemented in this demo.</p>
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
