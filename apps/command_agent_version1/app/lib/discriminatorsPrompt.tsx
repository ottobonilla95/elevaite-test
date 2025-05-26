import type { UploadFileResponse } from "./interfaces";





export function isUploadFileResponse(data: unknown): data is UploadFileResponse {
  return isUploadFileResponseObject(data);
}



// OBJECTS
///////////



function isObject(item: unknown): item is object {
    return Boolean(item) && item !== null && typeof item === "object";
}



function isUploadFileResponseObject(item: unknown): item is UploadFileResponse {
    return isObject(item) &&
    item !== null &&
    "success" in item &&
    typeof (item as any).success === "boolean";
}
