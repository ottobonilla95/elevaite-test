export type UploadResponse = UploadResponseSuccess | UploadErrorResponse;
export interface GenerateManifestResponse {
  message: "Manifest generated successfully" | "Manifest generated successfully!!";
  fileName: string;
  sheet_names: string[];
  status: 200;
}
export type GetYamlContentResponse = GetYamlContentSuccess | BaseErrorResponse;

interface UploadErrorResponse {
  response: "Error";
  error_message: string;
}

interface UploadResponseSuccess {
  response: "Success";
  file_size: string;
  file_path: string;
  file_name: string;
  file_type: string;
  sheet: string[];
  sheets_count: number;
}

interface BaseErrorResponse {
  error: string;
}

type GetYamlContentSuccess = string;

export enum Stages {
  Upload,
  Manifest,
  Template,
  Review,
}
