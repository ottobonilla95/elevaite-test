import type { AccountObject, OrganizationObject, ProjectObject, RoleObject, RolePermission, UserObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////


export function isGetOrganizationResponse(data: unknown): data is OrganizationObject {
    return isOrganizationObject(data);
}

export function isGetOrganizationUsersResponse(data: unknown): data is UserObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isUserObject(item)) return false;
    }
    return true;
}

export function isGetRolesResponse(data: unknown): data is RoleObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isRoleObject(item)) return false;
    }
    return true;
}

export function isGetAccountsResponse(data: unknown): data is AccountObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isAccountObject(item)) return false;
    }
    return true;
}

export function isGetProjectsResponse(data: unknown): data is ProjectObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isProjectObject(item)) return false;
    }
    return true;
}

export function isAddEditAccountResponse(data: unknown): data is AccountObject {
    return isAccountObject(data);
}

export function isAddEditProjectResponse(data: unknown): data is ProjectObject {
    return isProjectObject(data);
}

export function isAddEditUserResponse(data: unknown): data is UserObject {
    return isUserObject(data);
}

export function isGetUserProfileResponse(data: unknown): data is UserObject {
    return isUserObject(data);
}





// OBJECTS
///////////

export function isRolePermission(item: unknown): item is RolePermission {
    return (
        isObject(item) &&
        Object.values(item).filter(
            (permission) => permission !== "Allow" && permission !== "Deny" && !isRolePermission(permission)
        ).length !== 0
    );
}

export function isOrganizationObject(item: unknown): item is OrganizationObject {
    return isObject(item) &&
        "id" in item &&
        "name" in item &&
        "description" in item &&
        "created_at" in item &&
        "updated_at" in item;
}

export function isUserObject(item: unknown): item is UserObject {
    return isObject(item) &&
        "id" in item &&
        "organization_id" in item &&
        "firstname" in item &&
        "lastname" in item &&
        "email" in item &&
        "is_superadmin" in item &&
        "created_at" in item &&
        "updated_at" in item;
}

export function isRoleObject(item: unknown): item is RoleObject {
    return isObject(item) &&
        "id" in item &&
        "name" in item &&
        "permissions" in item &&
        "created_at" in item &&
        "updated_at" in item;
}

export function isAccountObject(item: unknown): item is AccountObject {
    return isObject(item) &&
        "id" in item &&
        "organization_id" in item &&
        "name" in item &&
        "description" in item &&
        "created_at" in item &&
        "updated_at" in item;
}

export function isProjectObject(item: unknown): item is ProjectObject {
    return isObject(item) &&
    "id" in item &&
    "account_id" in item &&
    "name" in item &&
    "description" in item &&
    "creator_id" in item &&
    "datasets" in item &&
    "created_at" in item &&
    "updated_at" in item;
}

