"use server";

import {
  isGenPPTResponse,
  isGenerateManifestResponse,
  isGetYamlContentResponse,
  isUploadResponse,
} from "./discriminators";
import type { GenPPTResponse, GenerateManifestResponse, GetYamlContentResponse, UploadResponse } from "./interfaces";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function uploadToServer(formData: FormData): Promise<UploadResponse> {
  const response = await fetch(`${BACKEND_URL}/upload/`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error("Failed to upload");
  const _data: unknown = await response.json();
  if (isUploadResponse(_data)) return _data;
  throw new Error("Data malformed", { cause: _data });
}

export async function generateManifest({
  fileName,
  filePath,
}: {
  fileName: string;
  filePath: string;
}): Promise<GenerateManifestResponse> {
  const url = new URL(`${BACKEND_URL}/generateManifest/`);
  url.searchParams.append("file_name", encodeURIComponent(fileName));
  url.searchParams.append("file_path", `data/Excel/${encodeURIComponent(filePath)}`);
  url.searchParams.append("save_dir", "data/Manifest");
  let _data: unknown;
  try {
    const response = await fetch(url.toString(), { method: "GET" });
    if (response.ok) {
      _data = await response.json();
    }
  } catch (error) {
    throw new Error("Something went wrong", { cause: error });
  }
  if (isGenerateManifestResponse(_data)) return _data;
  throw new Error("Data malformed", { cause: _data });
}

export async function getYamlContent({
  fileName,
  sheetName,
}: {
  fileName: string;
  sheetName: string;
}): Promise<GetYamlContentResponse> {
  const url = new URL(`${BACKEND_URL}/getYamlContent/`);
  url.searchParams.append("file_name", encodeURIComponent(fileName));
  url.searchParams.append("yaml_file", sheetName);

  let _data: unknown;
  try {
    const response = await fetch(url.toString(), { method: "GET" });
    _data = await response.json();
    if (!response.ok) {
      throw new Error("Something went wrong", { cause: _data });
    }
  } catch (error) {
    throw new Error("Something went wrong", { cause: error });
  }
  if (isGetYamlContentResponse(_data)) return _data;

  throw new Error("Data malformed", { cause: _data });
}

export async function generatePPT(fileName: string, activeSheet: string): Promise<GenPPTResponse> {
  const encodedExcelFile: string = encodeURIComponent(`${fileName}.xlsx`);
  const encodedSheetName = activeSheet.split(".")[0];
  const url = new URL(`${BACKEND_URL}/genPPT/`);
  url.searchParams.append("type", "financial");
  url.searchParams.append("excel_file", encodedExcelFile);
  url.searchParams.append("sheet_name", encodedSheetName);
  let _data: unknown;

  try {
    const response = await fetch(url.toString());
    _data = await response.json();

    if (!response.ok) {
      throw new Error("Something went wrong", { cause: _data });
    }
  } catch (error) {
    throw new Error("Error generating Presentation", { cause: error });
  }
  if (isGenPPTResponse(_data)) return _data;
  throw new Error("Data malformed", { cause: _data });
}

export async function ask(query: string, context: string): Promise<string> {
  const url = new URL(`${BACKEND_URL}/ask/`);
  const formData = new FormData();
  formData.append(query, query);
  formData.append(context, context);
  let _data: unknown;
  try {
    const response = await fetch(url.toString(), { body: JSON.stringify({ query, context }), method: "POST" });
    _data = await response.text();

    if (!response.ok) {
      throw new Error("Something went wrong", { cause: _data });
    }
  } catch (error) {
    throw new Error("Error generating Response", { cause: error });
  }
  if (typeof _data === "string") return _data;
  throw new Error("Data malformed", { cause: _data });
}

export async function downloadPPT(pptPath: string): Promise<Blob> {
  const validPptFile = pptPath ? pptPath : "";
  const url = new URL(`${BACKEND_URL}/downloadPPT/`);
  url.searchParams.append("ppt_path", validPptFile);
  let _data: Blob;
  try {
    const response = await fetch(url.toString(), { method: "GET" });
    if (response.ok) _data = await response.blob();
    else throw new Error("Something went wrong", { cause: response });
  } catch (error) {
    throw new Error("Something went wrong", { cause: error });
  }
  return _data;
}
