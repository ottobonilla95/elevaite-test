export type UploadResponse = UploadResponseSuccess | UploadErrorResponse;
export interface GenerateManifestResponse {
  message: "Manifest generated successfully" | "Manifest generated successfully!!";
  fileName: string;
  sheet_names: string[];
  status: 200;
}
export type GetYamlContentResponse = GetYamlContentSuccess | BaseErrorResponse;
export type GenPPTResponse = GenPPTSuccess | BaseErrorResponse;

export interface ChatMessageInterface {
  content: string | EmbeddedMessage;
  sender: "user" | "system";
  timestamp: string;
  btn?: {
    link: string;
    label: string;
  };
  isLoading?: boolean;
  uuid: string;
}

export interface EmbeddedMessage {
  before?: string | EmbeddedMessage;
  embed?: string;
  after?: string | EmbeddedMessage;
}

export interface Manifest {
  name: string;
  content: string;
}

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

interface GenPPTSuccess {
  export_url: string;
  summary: string;
}

export interface UploadedFile {
  name: string;
  sheetCount: number;
  sheets: string[];
  fileSize: string;
  key: string;
  filePath: string;
  fileType: string;
}
