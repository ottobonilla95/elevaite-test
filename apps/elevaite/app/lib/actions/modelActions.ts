"use server";
import { revalidateTag } from "next/cache";
import type { AvailableModelObject, ModelDatasetObject, ModelObject, ModelParametersObject } from "../interfaces";
import { APP_REVALIDATION_TIME, DEFAULT_AVAILABLE_MODELS_LIMIT, MODEL_REVALIDATION_TIME, cacheTags } from "./actionConstants";
import { isArrayOfStrings, isObject } from "./generalDiscriminators";
import { isGetAvailableModelsResponse, isGetDatasetsResponse, isGetModelByIdResponse, isGetModelParametersResponse, isGetModelsResponse, isModelObject } from "./modelDiscriminators";

const MODELS_URL = process.env.NEXT_MODELS_API_URL;


// GETS
//////////////////


export async function getModelsTasks(): Promise<string[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/tasks`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch model tasks");
  const data: unknown = await response.json();
  if (isArrayOfStrings(data)) return data;
  throw new Error("Invalid data type");
}

export async function getAvailableModels(task: string, limit?: number): Promise<AvailableModelObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/huggingface/models`);
  url.searchParams.set("task", task);
  url.searchParams.set("limit", limit ? limit.toString() : DEFAULT_AVAILABLE_MODELS_LIMIT);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch available models");
  const data: unknown = await response.json();
  if (isGetAvailableModelsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getAvailableModelsByName(name: string, limit?: number): Promise<AvailableModelObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/huggingface/models`);
  url.searchParams.set("model_name", name);
  url.searchParams.set("limit", limit ? limit.toString() : DEFAULT_AVAILABLE_MODELS_LIMIT);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch available models");
  const data: unknown = await response.json();
  if (isGetAvailableModelsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getModels(): Promise<ModelObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/models`);
  const response = await fetch(url, { next: { revalidate: MODEL_REVALIDATION_TIME, tags: [cacheTags.models] } });

  if (!response.ok) throw new Error("Failed to fetch models");
  const data: unknown = await response.json();
  if (isGetModelsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getModelById(id: string | number): Promise<ModelObject> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/models/${id.toString()}`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch model");
  const data: unknown = await response.json();
  if (isGetModelByIdResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getModelParametersById(id: string | number): Promise<ModelParametersObject> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/models/${id.toString()}/config`);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) throw new Error("Failed to fetch model parameters");
  const data: unknown = await response.json();
  if (isGetModelParametersResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getModelDatasets(): Promise<ModelDatasetObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_URL}/datasets`);
  const response = await fetch(url, { next: { revalidate: MODEL_REVALIDATION_TIME, tags: [cacheTags.datasets] } });

  if (!response.ok) throw new Error("Failed to fetch datasets");
  const data: unknown = await response.json();
  if (isGetDatasetsResponse(data)) return data;
  throw new Error("Invalid data type");
}




// POSTS and PUTS
//////////////////

export async function registerModel(modelName: string, modelRepo: string, tags?: string[]): Promise<ModelObject> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const dto = {
    huggingface_repo: modelRepo,
    name: modelName,
    tags,
  };

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${MODELS_URL}/models`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
  });
  revalidateTag(cacheTags.models);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to upload model");
  }
  const data: unknown = await response.json();
  if (isModelObject(data)) return data;
  throw new Error("Invalid data type");
}




// DELETES
//////////////////

export async function deleteModel(modelId: string): Promise<boolean> {  
  if (!MODELS_URL) throw new Error("Missing base url");
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  const response = await fetch(`${MODELS_URL}/models/${modelId}`, {
    method: "DELETE",
    headers,
  });
  revalidateTag(cacheTags.models);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to delete model");
  }  
  const data: unknown = await response.json();
  if (isObject(data) && "message" in data) return true; // Expected result: { message: 'model `17` deleted' }
  return false;
}