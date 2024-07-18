import { CommonButton, type CommonMenuItem, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useRoles } from "../../../lib/contexts/RolesContext";
import { type RoleObject } from "../../../lib/interfaces";
import { type DisplayPermission, getDisplayPermissions } from "../../../lib/rbacHelpers";
import "./RolesList.scss";
import { ListHeader } from "./smallParts/ListHeader";
import { ListRow, specialHandlingListRowFields, type RowStructure } from "./smallParts/ListRow";
import { RoleCard } from "./smallParts/RoleCard";





enum menuActions {
    EDIT = "Edit",
};





interface RolesListProps {
    isVisible: boolean;
}

export function RolesList(props: RolesListProps): JSX.Element {
    const rolesContext = useRoles();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [searchRoleTerm, setSearchRoleTerm] = useState("");
    const [searchPermissionTerm, setSearchPermissionTerm] = useState("");
    const [displayRoles, setDisplayRoles] = useState<RoleObject[]>([]);
    const [selectedRole, setSelectedRole] = useState<RoleObject|undefined>();
    const [displayPermissions, setDisplayPermissions] = useState<DisplayPermission[]>([]);

    const permissionsListStructure: RowStructure<DisplayPermission>[] = [
        { header: "Entity", field: "entity" },
        { header: "Entity Type", field: "type", leftBorder: "header", specialHandling: specialHandlingListRowFields.PERMISSIONS_LABEL },
        { header: "Create", field: "canCreate", leftBorder: "header", capitalize: true, align: "center", specialHandling: specialHandlingListRowFields.PERMISSIONS },
        { header: "Read", field: "canRead", leftBorder: "header", capitalize: true, align: "center", specialHandling: specialHandlingListRowFields.PERMISSIONS },
        { header: "Update", field: "canUpdate", leftBorder: "header", capitalize: true, align: "center", specialHandling: specialHandlingListRowFields.PERMISSIONS },
        { header: "Delete", field: "canDelete", leftBorder: "header", capitalize: true, align: "center", specialHandling: specialHandlingListRowFields.PERMISSIONS },
    ];

    const permissionsListMenu: CommonMenuItem<DisplayPermission>[] = [
        { label: "Edit Permissions", onClick: (item: DisplayPermission) => { handleMenuClick(item, menuActions.EDIT); } },
    ];


    useEffect(() => {        
        arrangeDisplayRoles();
    }, [rolesContext.roles, searchRoleTerm]);

    useEffect(() => {
        arrangeDisplayPermissions();
    }, [selectedRole, searchPermissionTerm]);



    function arrangeDisplayRoles(): void {
        const rolesClone = JSON.parse(JSON.stringify(rolesContext.roles)) as RoleObject[];

        // Search
        const searchedList: RoleObject[] = searchRoleTerm ? [] : rolesClone;
        if (searchRoleTerm) {
            for (const item of rolesClone) {
                if (item.name.toLowerCase().includes(searchRoleTerm.toLowerCase())) { searchedList.push(item); continue; }
                // Add other checks here as desired.
            }
        }

        // Set
        setDisplayRoles(searchedList);
    }

    function arrangeDisplayPermissions(): void {
        if (!selectedRole) { setDisplayPermissions([]); return; }
        // Format        
        const allPermissions = getDisplayPermissions(selectedRole);

        // Search
        const searchedPermissions: DisplayPermission[] = searchPermissionTerm ? [] : allPermissions;
        if (searchPermissionTerm) {
            for (const item of allPermissions) {
                if (item.entity.toLowerCase().includes(searchPermissionTerm.toLowerCase())) { searchedPermissions.push(item); continue; }
                if (item.type.find(permission => permission.toLowerCase().includes(searchPermissionTerm.toLowerCase()))) { searchedPermissions.push(item); continue; }
                // Add other checks here as desired.
            }
        }

        // Set
        setDisplayPermissions(searchedPermissions);
    }




    function handleAddRole(): void {
        console.log("Adding Role");
    }

    function handleListSearch(term: string): void {
        if (!props.isVisible) return;
        setSearchRoleTerm(term);
    }
    
    function handlePermissionSearch(term: string): void {
        if (!props.isVisible) return;
        setSearchPermissionTerm(term);
    }

    function switchSidebar(): void {
        setIsSidebarOpen(current => !current);
    }

    function onRoleClick(role: RoleObject): void {
        setSelectedRole(current => current?.id === role.id ? undefined : role);
    }


    function handleEditPermission(permission: DisplayPermission): void {
        console.log("Editing permission", permission);        
    }


    function handleMenuClick(permission: DisplayPermission, action: menuActions): void {
        switch (action) {
            case menuActions.EDIT: handleEditPermission(permission); break;
            default: break;
        }
    }


    return (
        <div className="roles-list-container">

            <div className={["roles-sidebar", isSidebarOpen ? "open" : undefined].filter(Boolean).join(" ")}>
                <ListHeader
                    label={
                        <div className={["swinging-header-label icon-left", isSidebarOpen ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <CommonButton
                                className="swinging-button"
                                onClick={switchSidebar}
                                noBackground
                            >
                                <ElevaiteIcons.SVGSideArrow />
                            </CommonButton>
                            <span>Roles List</span>
                        </div>
                    }
                    absoluteSearchPositioning
                    searchPlaceholder="Search Roles"
                    onSearch={handleListSearch}
                    isVisible={props.isVisible}
                />

                <div className="roles-sidebar-scroller">
                    {rolesContext.loading.roles ?                    
                        <div className="empty">
                            <ElevaiteIcons.SVGSpinner/>
                            Loading...
                        </div>
                    : displayRoles.length === 0 ? 
                        <div className="empty">No roles</div>
                    :
                        displayRoles.map(role =>
                            <RoleCard
                                key={role.id}
                                role={role}
                                selectedRoleId={selectedRole?.id}
                                handleClick={onRoleClick}
                            />
                        )
                    }
                </div>
            </div>

            <div className="roles-main-list">
            
                <ListHeader
                    label={
                        <div className={["swinging-header-label", !isSidebarOpen ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <CommonButton
                                className="swinging-button"
                                onClick={switchSidebar}
                                noBackground
                            >
                                <ElevaiteIcons.SVGSideArrow />
                            </CommonButton>
                            <span>Role Permissions</span>
                        </div>
                    }
                    addLabel="Add Role"
                    addIcon={<ElevaiteIcons.SVGUser/>}
                    addAction={handleAddRole}
                    onSearch={handlePermissionSearch}
                    searchPlaceholder="Search Role Permissions"
                    isVisible={props.isVisible}
                />

                <div className="roles-list-table-container">

                    {rolesContext.loading.roles ?
                        <div className="table-span empty">
                            <ElevaiteIcons.SVGSpinner/>
                            <span>Loading...</span>
                        </div>
                    : displayRoles.length === 0 ? 
                        <div className="table-span empty">
                            There are no roles to display.
                        </div>
                    : !selectedRole ? 
                        <div className="table-span empty">
                            Select a role on the sidebar to see its permissions
                        </div>
                    : displayPermissions.length === 0 ?
                        // Replace this when you have a solution
                        <div className="table-span empty">
                            No Permissions to display 
                        </div>
                    :
                        <>
                            <ListRow<DisplayPermission>
                                isHeader
                                structure={permissionsListStructure}
                                menu={permissionsListMenu}
                            />
                            {displayPermissions.map((permission, index) => 
                                <ListRow<DisplayPermission>
                                    key={permission.entity + permission.type.join("/")}
                                    rowItem={permission}
                                    structure={permissionsListStructure}
                                    menu={permissionsListMenu}
                                    menuToTop={displayPermissions.length > 4 && index > (displayPermissions.length - 4) }
                                />
                            )}
                        </>
                    }
                </div>

            </div>

        </div>
    );
}