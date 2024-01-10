import type { GenPPTResponse, GenerateManifestResponse, GetYamlContentResponse, UploadResponse } from "./interfaces";

function isObject(obj: unknown): obj is object {
  return Boolean(obj) && obj !== null && typeof obj === "object";
}

export function isUploadResponse(obj: unknown): obj is UploadResponse {
  return isObject(obj) && "response" in obj;
}

export function isGenerateManifestResponse(obj: unknown): obj is GenerateManifestResponse {
  return isObject(obj) && "message" in obj && "fileName" in obj;
}

export function isGetYamlContentResponse(obj: unknown): obj is GetYamlContentResponse {
  return (Boolean(obj) && obj !== null && typeof obj === "string") || (isObject(obj) && "error" in obj);
}

export function isGenPPTResponse(obj: unknown): obj is GenPPTResponse {
  return isObject(obj) && ("export_url" in obj || "error" in obj);
}
