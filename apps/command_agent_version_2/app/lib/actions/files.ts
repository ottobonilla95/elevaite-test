"use server";

export interface FileUploadResponse {
  message: string;
  filename: string;
  file_path: string;
  file_size: number;
  upload_timestamp: string;
  auto_processing?: {
    execution_id: string;
    workflow_id: string;
    status: string;
  };
}

function isFileUploadResponse(data: unknown): data is FileUploadResponse {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as FileUploadResponse).message === "string" &&
    typeof (data as FileUploadResponse).filename === "string" &&
    typeof (data as FileUploadResponse).file_path === "string"
  );
}

export async function uploadFile(file: File, options?: { workflow_id?: string; auto_process?: boolean }) {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.workflow_id) formData.append("workflow_id", options.workflow_id);
  if (options?.auto_process) formData.append("auto_process", "true");

  // Use fetch directly for FormData since the client.post expects JSON
  const response = await fetch("/api/files/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  const data: unknown = await response.json();
  if (!isFileUploadResponse(data)) throw new Error("Invalid file upload response");
  return data;
}
