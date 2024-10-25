"use server";
import { revalidateTag } from "next/cache";
import {
  type ContractObject,
  type CONTRACT_TYPES,
  type ContractProjectObject,
  ContractSettings,
  ContractObjectEmphasis,
  ContractObjectVerification,
  ContractObjectVerificationLineItem,
} from "../interfaces";
import {
  cacheTags,
  CONTRACT_PROJECTS_REVALIDATION_TIME,
} from "./actionConstants";
import {
  isCreateProjectResponse,
  isGetContractObjectEmphasisResponse,
  isGetContractObjectResponse,
  isGetContractObjectVerificationLineItemsResponse,
  isGetContractObjectVerificationResponse,
  isGetContractProjectByIdResponse,
  isGetContractProjectContractsResponse,
  isGetContractProjectSettingsByIdResponse,
  isGetContractProjectsListReponse,
  isReprocessContractResponse,
  isSubmitContractResponse,
} from "./contractDiscriminators";

// Helpers

function getBaseUrl(isAlt: boolean): string | undefined {
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  const CONTRACTS_IOPEX_URL = process.env.NEXT_PUBLIC_CONTRACTS_IOPEX_API_URL;

  return isAlt ? CONTRACTS_IOPEX_URL : CONTRACTS_URL;
}

// GETS
//////////////////

export async function getContractProjectsList(
  isAlt: boolean
): Promise<ContractProjectObject[]> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(`${baseUrl}/projects/`);
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract projects list");
  const data: unknown = await response.json();
  if (isGetContractProjectsListReponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractProjectById(
  projectId: string,
  isAlt: boolean
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(`${baseUrl}/projects/${projectId}`);
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractProjectByIdResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractProjectSettings(
  projectId: string,
  isAlt: boolean
): Promise<ContractSettings> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(`${baseUrl}/projects/${projectId}/settings`);
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractProjectSettingsByIdResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractProjectContracts(
  projectId: string,
  isAlt: boolean
): Promise<ContractObject[]> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(`${baseUrl}/projects/${projectId}/files`);
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractProjectContractsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractObjectById(
  projectId: string,
  contractId: string,
  isAlt: boolean
): Promise<ContractObject> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(`${baseUrl}/projects/${projectId}/files/${contractId}`);
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractObjectResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractObjectEmphasis(
  projectId: string,
  contractId: string,
  isAlt: boolean
): Promise<ContractObjectEmphasis> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(
    `${baseUrl}/projects/${projectId}/files/${contractId}/highlight`
  );
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractObjectEmphasisResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractObjectVerification(
  projectId: string,
  contractId: string,
  isAlt: boolean
): Promise<ContractObjectVerification> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(
    `${baseUrl}/projects/${projectId}/files/${contractId}/verification`
  );
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractObjectVerificationResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getContractObjectLineItems(
  projectId: string,
  contractId: string,
  isAlt: boolean
): Promise<ContractObjectVerificationLineItem[]> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const url = new URL(
    `${baseUrl}/projects/${projectId}/files/${contractId}/line_items`
  );
  const response = await fetch(url, {
    next: {
      revalidate: CONTRACT_PROJECTS_REVALIDATION_TIME,
      tags: [cacheTags.contractProjects],
    },
  });

  if (!response.ok) throw new Error("Failed to fetch contract project");
  const data: unknown = await response.json();
  if (isGetContractObjectVerificationLineItemsResponse(data)) return data;
  throw new Error("Invalid data type");
}

// POSTS
//////////////////

export async function reprocessContract(
  projectId: string,
  contractId: string,
  isAlt: boolean
): Promise<ContractObject> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");

  const url = new URL(
    `${baseUrl}/projects/${projectId}/files/${contractId}/process`
  );

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(url, {
    method: "POST",
    headers,
  });

  revalidateTag(cacheTags.contractProjects);
  if (!response.ok) {
    // if (response.status === 422) {
    const errorData: unknown = await response.json();
    // eslint-disable-next-line no-console -- Need this in case this breaks like that.
    console.dir(errorData, { depth: null });
    // }
    throw new Error("Failed to reprocess contract");
  }
  const data: unknown = await response.json();
  if (isReprocessContractResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function CreateProject(
  name: string,
  isAlt: boolean,
  description?: string
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");
  const dto = {
    name,
    description,
  };

  const url = new URL(`${baseUrl}/projects/`);

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

export async function submitContract(
  projectId: string,
  formData: FormData,
  type: CONTRACT_TYPES,
  isAlt: boolean
): Promise<ContractObject> {
  const baseUrl = getBaseUrl(isAlt);
  if (!baseUrl) throw new Error("Missing base url");

  const url = new URL(`${baseUrl}/projects/${projectId}/files/`);
  url.searchParams.set("content_type", type);

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  revalidateTag(cacheTags.contractProjects);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to submit contract");
  }
  const data: unknown = await response.json();
  if (isSubmitContractResponse(data)) return data;
  throw new Error("Invalid data type");
}
