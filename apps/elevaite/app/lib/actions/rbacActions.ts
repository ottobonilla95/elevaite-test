"use server";
import { revalidateTag } from "next/cache";
import type { AccountObject, OrganizationObject, ProjectObject, RoleObject, UserObject } from "../interfaces";
import { RBAC_REVALIDATION_TIME, cacheTags } from "./actionConstants";
import { isAddEditAccountResponse, isAddEditProjectResponse, isAddEditUserResponse, isGetAccountsResponse, isGetOrganizationResponse, isGetOrganizationUsersResponse, isGetProjectsResponse, isGetRolesResponse, isGetUserProfileResponse } from "./rbacDiscriminators";


const RBAC_URL = process.env.RBAC_BACKEND_URL;


// GETS
//////////////////


export async function getOrganization(authToken: string): Promise<OrganizationObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/organization/`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.rbac] }
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


export async function getOrganizationUsers(authToken: string, forceRevalidation?: boolean): Promise<UserObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/organization/users`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    if (forceRevalidation) revalidateTag(cacheTags.users);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.users] }
    });
    if (!response.ok) {
        if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
        }
        throw new Error("Failed to fetch users of organization");
    }
    const data: unknown = await response.json();
    if (isGetOrganizationUsersResponse(data)) return data;
    throw new Error("Invalid data type");
}


export async function getRoles(authToken: string, forceRevalidation?: boolean): Promise<RoleObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/roles/`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    if (forceRevalidation) revalidateTag(cacheTags.rbac);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.rbac] }
    });
    if (!response.ok) {
        if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
        }
        throw new Error("Failed to fetch roles");
    }
    const data: unknown = await response.json();
    if (isGetRolesResponse(data)) return data;
    throw new Error("Invalid data type");
}



export async function getAccounts(authToken: string, forceRevalidation?: boolean): Promise<AccountObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/accounts/`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    if (forceRevalidation) revalidateTag(cacheTags.rbac);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.rbac] }
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



export async function getProjects(accountId: string, authToken: string, forceRevalidation?: boolean): Promise<ProjectObject[]> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/projects/`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    headers.append("X-elevAIte-AccountId", accountId);
    if (forceRevalidation) revalidateTag(cacheTags.rbac);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.rbac] }
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



export async function getUserProfile(authToken: string, userId: string): Promise<UserObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const url = new URL(`${RBAC_URL}/users/${userId}/profile`);
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(url, {        
        method: "GET",
        headers,
        next: { revalidate: RBAC_REVALIDATION_TIME, tags: [cacheTags.users] }
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
    if (isGetUserProfileResponse(data)) return data;
    throw new Error("Invalid data type");
}








// POSTS and PUTS and PATCHES
//////////////////

export async function addAccount(authToken: string, orgId: string|number, accountName: string, accountDescription: string): Promise<AccountObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const dto = {
        organization_id: orgId,
        name: accountName,
        description: accountDescription
    };
  
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(`${RBAC_URL}/accounts/`, {
      method: "POST",
      body: JSON.stringify(dto),
      headers,
    });
    revalidateTag(cacheTags.rbac);
    if (!response.ok) {
      if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      }
      throw new Error("Failed to add account");
    }
    const data: unknown = await response.json();
    if (isAddEditAccountResponse(data)) return data;
    throw new Error("Invalid data type");
}


export async function editAccount(authToken: string, accountId: string, accountName: string, accountDescription?: string): Promise<AccountObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const dto = {
        name: accountName,
        description: accountDescription
    };
  
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(`${RBAC_URL}/accounts/${accountId}`, {
      method: "PATCH",
      body: JSON.stringify(dto),
      headers,
    });
    revalidateTag(cacheTags.rbac);
    if (!response.ok) {
      if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      }
      throw new Error("Failed to add account");
    }
    const data: unknown = await response.json();
    if (isAddEditAccountResponse(data)) return data;
    throw new Error("Invalid data type");
}

export async function addProject(authToken: string, accountId: string, projectName: string, projectDescription: string, parentProjectId?: string): Promise<ProjectObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const dto = {
        name: projectName,
        description: projectDescription
    };
  
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    headers.append("X-elevAIte-AccountId", accountId);
    if (parentProjectId) headers.append("X-elevAIte-ProjectId", parentProjectId);
    const response = await fetch(`${RBAC_URL}/projects/`, {
      method: "POST",
      body: JSON.stringify(dto),
      headers,
    });
    revalidateTag(cacheTags.rbac);
    if (!response.ok) {
      if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      }
      throw new Error("Failed to add project");
    }
    const data: unknown = await response.json();
    if (isAddEditProjectResponse(data)) return data;
    throw new Error("Invalid data type");
}


export async function editProject(authToken: string, projectId: string, projectName: string, projectDescription?: string): Promise<ProjectObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const dto = {
        name: projectName,
        description: projectDescription
    };
  
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(`${RBAC_URL}/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(dto),
      headers,
    });
    revalidateTag(cacheTags.rbac);
    if (!response.ok) {
      if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      }
      throw new Error("Failed to add account");
    }
    const data: unknown = await response.json();
    if (isAddEditProjectResponse(data)) return data;
    throw new Error("Invalid data type");
}


export async function editUser(authToken: string, userId: string, firstName: string, lastName: string): Promise<UserObject> {
    if (!RBAC_URL) throw new Error("Missing base url");
    const dto = {
        firstname: firstName,
        lastname: lastName
    };
  
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append("Authorization", `Bearer ${authToken}`);
    const response = await fetch(`${RBAC_URL}/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(dto),
      headers,
    });
    revalidateTag(cacheTags.users);
    if (!response.ok) {
      if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      }
      throw new Error("Failed to add account");
    }
    const data: unknown = await response.json();
    if (isAddEditUserResponse(data)) return data;
    throw new Error("Invalid data type");
}







// DELETES
//////////////////



