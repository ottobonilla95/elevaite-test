import { ROLE_PERMISSIONS, type RoleObject, type RolePermission } from "./interfaces";

export interface DisplayPermission {
    entity: string;
    type: string[];
    canCreate: boolean;
    canRead: boolean;
    canUpdate: boolean;
    canDelete: boolean;
}

export function getDisplayPermissions(role: RoleObject): DisplayPermission[] {
    return getDisplayPermissionRecursively(role.permissions);
}

function getDisplayPermissionRecursively(permission: RolePermission, passedLabels?: string[]): DisplayPermission[] {
    const displayPermissions: DisplayPermission[] = [];
    const labels = passedLabels ?? [];
    let hasCurrentPermission = false;
    const currentPermission: DisplayPermission = {
        entity: passedLabels && passedLabels.length > 0 ? passedLabels[0] : "Unknown",
        type: passedLabels && passedLabels.length > 1 ? passedLabels.slice(1) : [],
        canCreate: false,
        canRead: false,
        canUpdate: false,
        canDelete: false,
    };

    for (const key of Object.keys(permission)) {
        if (Object.values<string>(ROLE_PERMISSIONS).includes(key)) {
            hasCurrentPermission = true;
            switch (key as ROLE_PERMISSIONS) {
                case ROLE_PERMISSIONS.ACTION_CREATE: currentPermission.canCreate = permission[key] === "Allow"; break;
                case ROLE_PERMISSIONS.ACTION_READ: currentPermission.canRead = permission[key] === "Allow"; break;
                case ROLE_PERMISSIONS.ACTION_UPDATE: currentPermission.canUpdate = permission[key] === "Allow"; break;
                case ROLE_PERMISSIONS.ACTION_DELETE: currentPermission.canDelete = permission[key] === "Allow"; break;
            }
        } else if (key.startsWith("ACTION_")) {
            displayPermissions.push({
                entity: labels.length > 0 ? labels[0] : "Unknown",
                type: labels.length > 1 ? [...labels.slice(1), getLabelFromKey(key)] : [getLabelFromKey(key)],
                canCreate: permission[key] === "Allow",
                canRead: permission[key] === "Allow",
                canUpdate: permission[key] === "Allow",
                canDelete: permission[key] === "Allow",
            });
        } else {
            displayPermissions.push(
                ...getDisplayPermissionRecursively(permission[key] as RolePermission, [...labels, getLabelFromKey(key)].filter(Boolean))
            );
        }
    }

    if (hasCurrentPermission) displayPermissions.unshift(currentPermission);
    
    return displayPermissions;
}

function getLabelFromKey(key: string): string {
    let result = "";
    const splitKey = key.split("_");
    if (splitKey[0] !== "TYPENAMES" && splitKey[1]) {
        result = splitKey[1].charAt(0).toUpperCase() + splitKey[1].slice(1).toLowerCase();
    }
    return result;
}
