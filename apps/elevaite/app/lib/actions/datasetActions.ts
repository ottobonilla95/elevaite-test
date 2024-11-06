"use server";
import { revalidateTag } from "next/cache";
import {
  type HuggingfaceDatasetObject,
  type ModelDatasetObject,
} from "../interfaces";
import { DATASET_REVALIDATION_TIME, cacheTags } from "./actionConstants";
import {
  isGetAvailableDatasetsResponse,
  isGetDatasetsResponse,
  isModelDatasetObject,
} from "./datasetDiscriminators";
import { isArrayOfStrings } from "./generalDiscriminators";

const MODELS_URL = process.env.NEXT_PUBLIC_MODELS_API_URL;
const MODELS_ELEVAITE_URL = `${MODELS_URL}/elevaite`;
const MODELS_USERNAME = process.env.MODELS_USERNAME;
const MODELS_PASSWORD = process.env.MODELS_PASSWORD;
const MODELS_AUTH_HEADER = new Headers({
  Authorization: `Basic ${btoa(`${MODELS_USERNAME}:${MODELS_PASSWORD}`)}`,
});

// TODO: This is temporary
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

// GETS
//////////////////

export async function getDatasets(): Promise<ModelDatasetObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_ELEVAITE_URL}/datasets`);
  const response = await fetch(url, {
    next: { revalidate: DATASET_REVALIDATION_TIME, tags: [cacheTags.datasets] },
    credentials: "include",
    headers: MODELS_AUTH_HEADER,
  });

  if (!response.ok) throw new Error("Failed to fetch datasets");
  const data: unknown = await response.json();
  if (isGetDatasetsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getDatasetTasks(): Promise<string[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_ELEVAITE_URL}/tasks`);
  const response = await fetch(url, {
    next: { revalidate: DATASET_REVALIDATION_TIME, tags: [cacheTags.datasets] },
    credentials: "include",
    headers: MODELS_AUTH_HEADER,
  });

  if (!response.ok) throw new Error("Failed to fetch model tasks");
  const data: unknown = await response.json();
  if (isArrayOfStrings(data)) return data;
  throw new Error("Invalid data type");
}

interface availableDatasetsByName {
  datasetName: string;
}
interface availableDatasetsByTask {
  task: string;
}
interface availableDatasetsByAuthor {
  author: string;
}
type availableDatasetInput =
  | availableDatasetsByName
  | availableDatasetsByTask
  | availableDatasetsByAuthor;

export async function getAvailableDatasets(
  input: availableDatasetInput
): Promise<HuggingfaceDatasetObject[]> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const url = new URL(`${MODELS_ELEVAITE_URL}/huggingface/datasets`);
  if ("datasetName" in input && input.datasetName)
    url.searchParams.set("dataset_name", input.datasetName);
  if ("task" in input && input.task) url.searchParams.set("task", input.task);
  if ("author" in input && input.author)
    url.searchParams.set("author", input.author);
  const response = await fetch(url, {
    next: { revalidate: DATASET_REVALIDATION_TIME, tags: [cacheTags.datasets] },
    credentials: "include",
    headers: MODELS_AUTH_HEADER,
  });

  if (!response.ok) throw new Error("Failed to fetch available datasets");
  const data: unknown = await response.json();
  if (isGetAvailableDatasetsResponse(data)) return data;
  throw new Error("Invalid data type");
}

// POSTS and PUTS
//////////////////

export async function registerDataset(
  datsetName: string,
  datasetRepo: string,
  tags?: string[]
): Promise<ModelDatasetObject> {
  if (!MODELS_URL) throw new Error("Missing base url");
  const dto = {
    huggingface_repo: datasetRepo,
    name: datsetName,
    tags,
  };

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append(
    "Authorization",
    `Basic ${btoa(`${MODELS_USERNAME}:${MODELS_PASSWORD}`)}`
  );
  const response = await fetch(`${MODELS_ELEVAITE_URL}/datasets`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers,
    credentials: "include",
  });
  revalidateTag(cacheTags.models);
  if (!response.ok) {
    if (response.status === 422) {
      const errorData: unknown = await response.json();
      // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      console.dir(errorData, { depth: null });
    }
    throw new Error("Failed to register dataset");
  }
  const data: unknown = await response.json();
  if (isModelDatasetObject(data)) return data;
  throw new Error("Invalid data type");
}
