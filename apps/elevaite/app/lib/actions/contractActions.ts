"use server";
import { revalidateTag } from "next/cache";
import { type ContractObject, type CONTRACT_TYPES, type ContractProjectObject } from "../interfaces";
import { cacheTags, CONTRACT_PROJECTS_REVALIDATION_TIME } from "./actionConstants";
import { isCreateProjectResponse, isGetContractProjectByIdResponse, isGetContractProjectsListReponse, isSubmitContractResponse } from "./contractDiscriminators";



const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;




// GETS
//////////////////


export async function getContractProjectsList(): Promise<ContractProjectObject[]> {
  if (!CONTRACTS_URL) throw new Error("Missing base url");
  const url = new URL(`${CONTRACTS_URL}/projects/`);
  const response = await fetch(url, { next: { revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME, tags: [cacheTags.contractProjects] } });

  if (!response.ok) throw new Error("Failed to fetch contract projects list");
  const data: unknown = await response.json();
  if (isGetContractProjectsListReponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function getContractProjectById(projectId: string): Promise<ContractProjectObject> {
  if (!CONTRACTS_URL) throw new Error("Missing base url");
  const url = new URL(`${CONTRACTS_URL}/projects/${projectId}`);
  const response = await fetch(url, { cache: "no-store", next: { revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME, tags: [cacheTags.contractProjects] } });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractProjectByIdResponse(data)) return data;
  throw new Error("Invalid data type");
}






// POSTS
//////////////////





export async function CreateProject(name: string, description?: string): Promise<ContractProjectObject> {
  if (!CONTRACTS_URL) throw new Error("Missing base url");
  const dto = {
    name,
    description,
  };

  const url = new URL(`${CONTRACTS_URL}/projects/`);

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
  });

  revalidateTag(cacheTags.contractProjects);
  if (!response.ok) {
    // if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    // }
    throw new Error("Failed to create contract project");
  }
  const data: unknown = await response.json();
  if (isCreateProjectResponse(data)) return data;
  throw new Error("Invalid data type");
}




export async function submitContract(projectId: string, formData: FormData, type: CONTRACT_TYPES): Promise<ContractObject> {
  if (!CONTRACTS_URL) throw new Error("Missing base url");

  const url = new URL(`${CONTRACTS_URL}/project/${projectId}/files/`);
  url.searchParams.set("content_type", type);

  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort();
  }, 360000); // 6 minutes
  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    revalidateTag(cacheTags.contractProjects);

    if (!response.ok) {
      // if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
      // }
      throw new Error("Failed to submit contract");
    }

    const data: unknown = await response.json();
    if (isSubmitContractResponse(data)) return data;
    throw new Error("Invalid data type");
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw error;
  } finally {
    clearTimeout(timeout); // clear the timeout once the request completes
  }
}
