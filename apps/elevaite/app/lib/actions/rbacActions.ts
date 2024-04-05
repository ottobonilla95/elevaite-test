"use server";
import type { AccountObject, OrganizationObject, ProjectObject } from "../interfaces";
import { isGetAccountsResponse, isGetOrganizationResponse, isGetProjectsResponse } from "./rbacDiscriminators";




const RBAC_URL = process.env.RBAC_BACKEND_URL;



export async function getOrganization(authToken: string): Promise<OrganizationObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/organization/`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(url, {        
        method: "GET",
        headers,
    });
    if (!response.ok) {
        if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
        }
        throw new Error("Failed to fetch organization");
    }
    const data: unknown = await response.json();
    if (isGetOrganizationResponse(data)) return data;
    throw new Error("Invalid data type");
}



export async function getAccounts(organizationId: string, authToken: string): Promise<AccountObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/accounts/`);
    url.searchParams.set("org_id", organizationId);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(url, {        
        method: "GET",
        headers,
    });
    if (!response.ok) {
        if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
        }
        throw new Error("Failed to fetch accounts");
    }
    const data: unknown = await response.json();
    if (isGetAccountsResponse(data)) return data;
    throw new Error("Invalid data type");
}



export async function getProjects(accountId: string, authToken: string): Promise<ProjectObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/projects/`);
    url.searchParams.set("account_id", accountId);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(url, {        
        method: "GET",
        headers,
    });
    if (!response.ok) {
        if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
        }
        throw new Error("Failed to fetch projects");
    }
    const data: unknown = await response.json();
    if (isGetProjectsResponse(data)) return data;
    throw new Error("Invalid data type");
}









