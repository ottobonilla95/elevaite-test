export enum PromptInputTypes {
  DocumentHeader = "documentHeader",
  LineItemHeader = "lineItemHeader",
  UserFeedback = "userFeedback",
  LineItems = "lineItems",
  ExpectedOutput = "expectedOutput",
}

export interface UploadFileResponseObject {
  image: string;
  doc_type: string;
  num_pages: number;
  prompt: string;
  line_items: string;
  table_header: string;
  result: string;
}

export interface ProcessCurrentPageResponseObject {
  document_headers: string[];
  line_item_headers: string[];
  result: string;
  prompt: string;
}

export interface PageChangeResponseObject {
  image: string;
  prompt: string;
}

export interface regenerateResponseObject {
  id?: string;
  prompt: string;
  result: string;
}

export type RunResponseObject = string[];

export type DeployResponse = "Done";

export interface PromptInputItem {
  id: string;
  type: PromptInputTypes;
  label?: string;
  prompt: string;
  values: string[];
}
