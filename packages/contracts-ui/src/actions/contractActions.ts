"use server";
import { revalidateTag } from "next/cache";
import {
  type CONTRACT_TYPES,
  type ContractObject,
  type ContractObjectEmphasis,
  type ContractObjectVerification,
  type ContractObjectVerificationLineItem,
  type ContractProjectObject,
  type ContractSettings,
} from "../interfaces";
import {
  cacheTags,
  CONTRACT_PROJECTS_REVALIDATION_TIME,
} from "./actionConstants";
import {
  isCreateProjectResponse,
  isDeleteContractResponse,
  isDeleteProjectResponse,
  isEditProjectResponse,
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

const getBaseUrl = (): string | undefined =>
  process.env.NEXT_PUBLIC_CONTRACTS_API_URL;

// GETS
//////////////////

export async function getContractProjectsList(): Promise<
  ContractProjectObject[]
> {
  const baseUrl = getBaseUrl();
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
  projectId: string
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl();
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
  projectId: string
): Promise<ContractSettings> {
  const baseUrl = getBaseUrl();
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
  projectId: string
): Promise<ContractObject[]> {
  const baseUrl = getBaseUrl();
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
  contractId: string
): Promise<ContractObject> {
  const baseUrl = getBaseUrl();
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
  contractId: string
): Promise<ContractObjectEmphasis> {
  const baseUrl = getBaseUrl();
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
  contractId: string
): Promise<ContractObjectVerification> {
  const baseUrl = getBaseUrl();
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
  contractId: string
): Promise<ContractObjectVerificationLineItem[]> {
  const baseUrl = getBaseUrl();
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
  contractId: string
): Promise<ContractObject> {
  const baseUrl = getBaseUrl();
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
  description?: string
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl();
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

export async function EditProject(
  projectId: string,
  name: string,
  description?: string
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl();
  if (!baseUrl) throw new Error("Missing base url");
  const dto = {
    name,
    description,
  };

  const url = new URL(`${baseUrl}/projects/${projectId}`);

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(url, {
    method: "PUT",
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
    throw new Error("Failed to edit contract project");
  }
  const data: unknown = await response.json();
  if (isEditProjectResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function DeleteProject(
  projectId: string
): Promise<ContractProjectObject> {
  const baseUrl = getBaseUrl();
  if (!baseUrl) throw new Error("Missing base url");

  const url = new URL(`${baseUrl}/projects/${projectId}`);

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(url, {
    method: "DELETE",
    headers,
  });

  revalidateTag(cacheTags.contractProjects);
  if (!response.ok) {
    // if (response.status === 422) {
    const errorData: unknown = await response.json();
    // eslint-disable-next-line no-console -- Need this in case this breaks like that.
    console.dir(errorData, { depth: null });
    // }
    throw new Error("Failed to delete contract project");
  }
  const data: unknown = await response.json();
  if (isDeleteProjectResponse(data)) return data;
  throw new Error("Invalid data type");
}

async function actionSubmitContract(
  submittedPdf: File,
  type: CONTRACT_TYPES,
  projectId: string | number,
  name?: string
): Promise<void> {
  const formData = new FormData();
  formData.append("file", submittedPdf);
  if (name) formData.append("label", name);
  await submitContract(projectId.toString(), formData, type);
}

async function submitContract(
  projectId: string,
  formData: FormData,
  type: CONTRACT_TYPES
): Promise<ContractObject> {
  const baseUrl = getBaseUrl();
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

export async function submitCurrentContractPdf(
  pdf: File | undefined,
  type: CONTRACT_TYPES,
  projectId: string | number,
  name?: string
): Promise<void> {
  if (pdf) {
    await actionSubmitContract(pdf, type, projectId, name);
  }
}

export async function deleteContract(
  projectId: string,
  contractId: string
): Promise<ContractObject> {
  const baseUrl = getBaseUrl();
  if (!baseUrl) throw new Error("Missing base url");

  const url = new URL(`${baseUrl}/projects/${projectId}/files/${contractId}`);

  const response = await fetch(url, {
    method: "DELETE",
  });

  revalidateTag(cacheTags.contractProjects);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to delete contract");
  }
  const data: unknown = await response.json();
  if (isDeleteContractResponse(data)) return data;
  throw new Error("Invalid data type");
}
