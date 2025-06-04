import type { DeployResponse, PageChangeResponseObject, regenerateResponseObject, RunResponseObject, UploadFileResponseObject } from "./interfaces";





export function isUploadFileResponse(data: unknown): data is UploadFileResponseObject {
  return isUploadFileResponseObject(data);
}

export function isPageChangeResponse(data: unknown): data is PageChangeResponseObject {
  return isPageResponseObject(data);
}

export function isRunResponse(data: unknown): data is RunResponseObject {
  if (!Array.isArray(data)) return false;
  for (const item of data) {
    if (typeof item !== "string") return false;
  }
  return true;
}

export function isReRunResponse(data: unknown): data is regenerateResponseObject {
  return isReRunResponseObject(data);
}

export function isDeployResponse(data: unknown): data is DeployResponse {
  return typeof data === "string" && data === "Done";
}





// OBJECTS
///////////



function isObject(item: unknown): item is object {
    return Boolean(item) && item !== null && typeof item === "object";
}



function isUploadFileResponseObject(item: unknown): item is UploadFileResponseObject {
    return isObject(item) &&
    "image" in item &&
    "doc_type" in item &&
    "num_pages" in item &&
    "prompt" in item &&
	'table_header' in item &&
	'line_items' in item &&
	'result' in item;
}

function isPageResponseObject(item: unknown): item is PageChangeResponseObject {
    return isObject(item) &&
    "image" in item &&
    "prompt" in item;
}

function isReRunResponseObject(item: unknown): item is regenerateResponseObject {
    return isObject(item) &&
    "response" in item &&
    "prompt" in item;
}
