import { isDeployResponse, isPageChangeResponse, isReRunResponse, isRunResponse, isUploadFileResponse } from "./discriminatorsPrompt";
import type { DeployResponse, PageChangeResponseObject, RunResponseObject, UploadFileResponseObject } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_PROMPT_BACKEND_URL;


export async function uploadFile(sessionId: string, useYolo: boolean, file: File, isImage = false): Promise<UploadFileResponseObject> {
  const url = new URL(`${BACKEND_URL ?? ""}upload_file/`);
  url.searchParams.set("session_id", sessionId);
  url.searchParams.set("use_yolo", String(useYolo));
  url.searchParams.set("is_image", String(isImage));

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(url.toString(), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Upload failed");
  const data = await response.json();
  if (isUploadFileResponse(data)) return data;
  throw new Error("Unexpected upload file response");
}

export async function nextPage(sessionId: string, useYolo: boolean): Promise<PageChangeResponseObject> {
  const url = new URL(`${BACKEND_URL ?? ""}next_page/`);
  url.searchParams.set("session_id", sessionId);
  url.searchParams.set("use_yolo", String(useYolo));

  const response = await fetch(url.toString(), {
    method: "POST",
  });

  if (!response.ok) throw new Error("Go to next page failed");
  const data = await response.json();
  if (isPageChangeResponse(data)) return data;
  throw new Error("Unexpected page change response");
}

export async function previousPage(sessionId: string, useYolo: boolean): Promise<PageChangeResponseObject> {
  const url = new URL(`${BACKEND_URL ?? ""}prev_page/`);
  url.searchParams.set("session_id", sessionId);
  url.searchParams.set("use_yolo", String(useYolo));

  const response = await fetch(url.toString(), {
    method: "POST",
  });

  if (!response.ok) throw new Error("Go to previous page failed");
  const data = await response.json();
  if (isPageChangeResponse(data)) return data;
  throw new Error("Unexpected page change response");
}


export async function run(sessionId: string): Promise<RunResponseObject> {
  const url = new URL(`${BACKEND_URL ?? ""}on_extract/`);
  url.searchParams.set("session_id", sessionId);

  const response = await fetch(url.toString(), {
    method: "POST",
  });

  if (!response.ok) throw new Error("Run action failed");
  const data = await response.json();
  if (isRunResponse(data)) return data;
  throw new Error("Unexpected extraction response");
}

export async function reRun(sessionId: string, options?: { userFeedback?: string; tableHeader?: string; lineItems?: string; expectedOutput?: string;}): Promise<any> {
  const url = new URL(`${BACKEND_URL ?? ""}regenerate/`);
  url.searchParams.set("session_id", sessionId);
  url.searchParams.set("user_feedback", options?.userFeedback ?? "");
  url.searchParams.set("table_header", options?.tableHeader ?? "");
  url.searchParams.set("line_items", options?.lineItems ?? "");
  url.searchParams.set("expected_output", options?.expectedOutput ?? "");

  const response = await fetch(url.toString(), {
    method: "POST",
  });

  if (!response.ok) throw new Error("Re-run action failed");
  const data = await response.json();
  if (isReRunResponse(data)) return data;
  throw new Error("Unexpected regeneration response");
}


export async function deploy(sessionId: string, originalText?: string, extractionPrompt?: string): Promise<DeployResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}on_publish/`);
  url.searchParams.set("session_id", sessionId);
  url.searchParams.set("original_text", originalText ?? "");
  url.searchParams.set("extraction_prompt", extractionPrompt ?? "");

  const response = await fetch(url.toString(), {
    method: "POST",
  });

  if (!response.ok) throw new Error("Deploy action failed");
  const data = await response.json();
  return data;
  if (isDeployResponse(data)) return data;
  throw new Error("Unexpected deployment response");
}