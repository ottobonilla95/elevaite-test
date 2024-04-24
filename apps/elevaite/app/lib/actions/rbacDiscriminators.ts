import type { AccountObject, OrganizationObject, ProjectObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////


export function isGetOrganizationResponse(data: unknown): data is OrganizationObject {
    return isOrganizationObject(data);
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





// OBJECTS
///////////

export function isOrganizationObject(item: unknown): item is OrganizationObject {
    return isObject(item) &&
        "id" in item &&
        "name" in item &&
        "description" in item &&
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

export function isProjectObject(item: unknown): item is AccountObject {
    return isObject(item) &&
    "id" in item &&
    "account_id" in item &&
    "name" in item &&
    "description" in item &&
    "creator" in item &&
    "datasets" in item &&
    "created_at" in item &&
    "updated_at" in item;
}

