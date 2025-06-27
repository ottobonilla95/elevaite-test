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

export type PromptInputVariableEngineerType = "String" | "Text" | "Textarea";

export interface PromptInputVariableEngineerItem {
  id: string;
  name: string;
  displayName: string;
  type: PromptInputVariableEngineerType;
  required: boolean;
  json: boolean;
  definition: string;
  saved?: boolean,
}

export type NewPromptInputParameter = "Parameters" | "Elevaite" | "Enterprise" | "Cloud";

export type NewPromptInputStatus = "Status" | "Draft" | "In Review" | "Approved";

export type NewPromptInputVersion = "Version";

export type NewPromptInputExecution = "Hosted" | "Custom API";

export type NewPromptInputOutputFormat = "JSON" | "CSV" | "HTML";

export interface NewPromptInputSelectedModelOnHover {
	id: string;
	name: string;
	description: string;
	context: string;
	inputPricing: string;
	outputPricing: string;
}

export interface PromptTestingConsoleInputTab {
	id: number;
	value: string;
}
