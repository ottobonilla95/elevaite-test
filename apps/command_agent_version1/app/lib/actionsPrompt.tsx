import { isUploadFileResponse } from "./discriminatorsPrompt";
import type { UploadFileResponse } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;


export async function uploadFile(
  sessionId: string,
  useYolo: boolean,
  file: File,
  isImage = false
): Promise<UploadFileResponse> {
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
  const data: unknown = await response.json();
  if (isUploadFileResponse(data)) return data;
  throw new Error("Invalid response shape");
}
