"use server";
import { revalidateTag } from "next/cache";
import type { AppInstanceLogObject, AppInstanceObject, ApplicationConfigurationDto, ApplicationConfigurationObject, ApplicationDto, ApplicationObject, ChartDataObject, CollectionChunkWrapper, CollectionObject, PipelineObject, RbacDatasetObject } from "../interfaces";
import { APP_REVALIDATION_TIME, INSTANCE_REVALIDATION_TIME, cacheTags } from "./actionConstants";
import { isCreateCollectioneResponse, isCreateConfigurationResponse, isCreateInstanceResponse, isGetApplicationListReponse, isGetApplicationPipelinesResponse, isGetApplicationResponse, isGetApplicationconfigurationsResponse, isGetCollectionScrollResponse, isGetCollectionsOfProjectResponse, isGetDatasetsOfProjectResponse, isGetInstanceChartDataResponse, isGetInstanceListResponse, isGetInstanceLogDataResponse, isGetInstanceResponse } from "./applicationDiscriminators";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const COLLECTION_SCROLL_PAGE_LIMIT = 10;


// GETS
//////////////////


export async function getApplicationList(): Promise<ApplicationObject[]> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch appllication list");
  const data: unknown = await response.json();
  if (isGetApplicationListReponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationById(id: string): Promise<ApplicationObject | undefined> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${id}`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch application");
  const data: unknown = await response.json();
  if (isGetApplicationResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationInstanceList(id: string): Promise<AppInstanceObject[]> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${id}/instance`);
  const response = await fetch(url, { next: { revalidate: INSTANCE_REVALIDATION_TIME, tags: [cacheTags.instance] } });

  if (!response.ok) throw new Error("Failed to fetch application instance list");
  const data: unknown = await response.json();
  if (isGetInstanceListResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationInstanceById(appId: string, instanceId: string): Promise<AppInstanceObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${appId}/instance/${instanceId}`);
  const response = await fetch(url, { next: { revalidate: INSTANCE_REVALIDATION_TIME, tags: [cacheTags.instance] } });

  if (!response.ok) throw new Error("Failed to fetch application instance");
  const data: unknown = await response.json();
  if (isGetInstanceResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationPipelines(id: string): Promise<PipelineObject[]> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${id}/pipelines`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME, tags: [cacheTags.pipeline] } });

  if (!response.ok) throw new Error("Failed to fetch application pipelines");
  const data: unknown = await response.json();
  if (isGetApplicationPipelinesResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getInstanceChartData(appId: string, instanceId: string): Promise<ChartDataObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${appId}/instance/${instanceId}/chart`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch instance chart data");
  const data: unknown = await response.json();
  if (isGetInstanceChartDataResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getInstanceLogData(appId: string, instanceId: string): Promise<AppInstanceLogObject[]> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${appId}/instance/${instanceId}/log`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch instance log data");
  const data: unknown = await response.json();
  if (isGetInstanceLogDataResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationConfigurations(id: string): Promise<ApplicationConfigurationObject[] | undefined> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/application/${id}/configuration`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME, tags: [cacheTags.configuration] } });

  if (!response.ok) throw new Error("Failed to fetch application configurations");
  const data: unknown = await response.json();
  if (isGetApplicationconfigurationsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getCollectionsOfProject(projectId: string): Promise<CollectionObject[] | undefined> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/project/${projectId}/collection`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch collections of project");
  const data: unknown = await response.json();
  if (isGetCollectionsOfProjectResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getDatasetsOfProject(projectId: string): Promise<RbacDatasetObject[]> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/project/${projectId}/datasets`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch datasets of project");
  const data: unknown = await response.json();
  if (isGetDatasetsOfProjectResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getCollectionScroll(projectId: string, collectionId: string, nextEntryId?: string): Promise<CollectionChunkWrapper> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const url = new URL(`${BACKEND_URL}/project/${projectId}/collection/${collectionId}/scroll`);
  url.searchParams.set("limit", COLLECTION_SCROLL_PAGE_LIMIT.toString());
  url.searchParams.set("with_payload", "true");
  url.searchParams.set("with_vectors", "true");
  if (nextEntryId) url.searchParams.set("after", nextEntryId);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch collection scroll");
  const data: unknown = await response.json();
  if (isGetCollectionScrollResponse(data)) return data;
  throw new Error("Invalid data type");
}






// POSTS and PUTS
//////////////////


export async function createApplicationInstance(id: string, dto: ApplicationDto): Promise<AppInstanceObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${BACKEND_URL}/application/${id}/instance/`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
  });
  revalidateTag(cacheTags.instance);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to upload application instance");
  }
  const data: unknown = await response.json();
  if (isCreateInstanceResponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function createApplicationConfiguration(appId: string, dto: ApplicationConfigurationDto): Promise<ApplicationConfigurationObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${BACKEND_URL}/application/${appId}/configuration/`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
  });
  revalidateTag(cacheTags.configuration);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to upload application configuration");
  }
  const data: unknown = await response.json();
  if (isCreateConfigurationResponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function updateApplicationConfiguration(appId: string, configId: string, dto: Omit<ApplicationConfigurationDto, "applicationId">): Promise<ApplicationConfigurationObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${BACKEND_URL}/application/${appId}/configuration/${configId}`, {
    method: "PUT",
    body: JSON.stringify(dto),
    headers,
  });
  revalidateTag(cacheTags.configuration);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to update application configuration");
  }
  const data: unknown = await response.json();
  if (isCreateConfigurationResponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function createCollection(projectId: string, collectionName: string, collectionDimensions: string): Promise<CollectionObject> {
  if (!BACKEND_URL) throw new Error("Missing base url");
  const dto = { name: collectionName, size: collectionDimensions };
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${BACKEND_URL}/project/${projectId}/collection`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
  });
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to create collection");
  }
  const data: unknown = await response.json();
  if (isCreateCollectioneResponse(data)) return data;
  throw new Error("Invalid data type");
}


