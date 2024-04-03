"use server";
import { revalidateTag } from "next/cache";
import type { AppInstanceObject, ApplicationConfigurationDto, ApplicationConfigurationObject, ApplicationObject, ChartDataObject, Initializers, PipelineObject } from "../interfaces";
import { isCreateConfigurationResponse, isCreateInstanceResponse, isGetApplicationListReponse, isGetApplicationPipelinesResponse, isGetApplicationResponse, isGetApplicationconfigurationsResponse, isGetInstanceChartDataResponse, isGetInstanceListResponse, isGetInstanceResponse } from "./applicationDiscriminators";
import { APP_REVALIDATION_TIME, INSTANCE_REVALIDATION_TIME, cacheTags } from "./actionConstants";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;


// GETS
//////////////////


export async function getApplicationList(): Promise<ApplicationObject[]> {
  const url = new URL(`${BACKEND_URL}/application`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationListReponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationById(id: string): Promise<ApplicationObject | undefined> {
  const url = new URL(`${BACKEND_URL}/application/${id}`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationInstanceList(id: string): Promise<AppInstanceObject[]> {
  const url = new URL(`${BACKEND_URL}/application/${id}/instance`);
  const response = await fetch(url, { next: { revalidate: INSTANCE_REVALIDATION_TIME, tags: [cacheTags.instance] } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetInstanceListResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationInstanceById(appId: string, instanceId: string): Promise<AppInstanceObject> {
  const url = new URL(`${BACKEND_URL}/application/${appId}/instance/${instanceId}`);
  const response = await fetch(url, { next: { revalidate: INSTANCE_REVALIDATION_TIME, tags: [cacheTags.instance] } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetInstanceResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationPipelines(id: string): Promise<PipelineObject[]> {
  const url = new URL(`${BACKEND_URL}/application/${id}/pipelines`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME, tags: [cacheTags.pipeline] } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationPipelinesResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getInstanceChartData(appId: string, instanceId: string): Promise<ChartDataObject> {
  const url = new URL(`${BACKEND_URL}/application/${appId}/instance/${instanceId}/chart`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetInstanceChartDataResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getApplicationConfigurations(id: string): Promise<ApplicationConfigurationObject[] | undefined> {
  const url = new URL(`${BACKEND_URL}/application/${id}/configuration`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME, tags: [cacheTags.configuration] } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationconfigurationsResponse(data)) return data;
  throw new Error("Invalid data type");
}





// POSTS and PUTS
//////////////////


export async function createApplicationInstance(id: string, dto: Initializers): Promise<AppInstanceObject> {
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
    throw new Error("Failed to upload");
  }
  const data: unknown = await response.json();
  if (isCreateInstanceResponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function createApplicationConfiguration(appId: string, dto: ApplicationConfigurationDto): Promise<ApplicationConfigurationObject> {
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
    throw new Error("Failed to upload");
  }
  const data: unknown = await response.json();
  if (isCreateConfigurationResponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function updateApplicationConfiguration(appId: string, configId: string, dto: Omit<ApplicationConfigurationDto, "applicationId">): Promise<ApplicationConfigurationObject> {
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
    throw new Error("Failed to update");
  }
  const data: unknown = await response.json();
  if (isCreateConfigurationResponse(data)) return data;
  throw new Error("Invalid data type");
}


