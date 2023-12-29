"use server";

import { isGenerateManifestResponse, isGetYamlContentResponse, isUploadResponse } from "./discriminators";
import type { GenerateManifestResponse, GetYamlContentResponse, UploadResponse } from "./interfaces";

// export async function authenticate(
//   prevState: string | undefined,
//   formData: Record<"email" | "password", string>
// ): Promise<"Invalid credentials." | "Something went wrong." | undefined> {
//   try {
//     await signIn("credentials", formData);
//   } catch (error) {
//     if (error instanceof AuthError) {
//       switch (error.type) {
//         case "CredentialsSignin":
//           return "Invalid credentials.";
//         default:
//           return "Something went wrong.";
//       }
//     }
//     throw error;
//   }
// }

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
