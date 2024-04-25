

export const DEFAULT_AVAILABLE_MODELS_LIMIT = "10";
export const APP_REVALIDATION_TIME = 3600; // one hour
export const INSTANCE_REVALIDATION_TIME = 5 * 60; // X minutes
export const MODEL_REVALIDATION_TIME = 30; // seconds
export const DATASET_REVALIDATION_TIME = 30; // seconds
export const RBAC_REVALIDATION_TIME = 3600; // one hour
export enum cacheTags {
  instance = "INSTANCE",
  pipeline = "PIPELINE",
  configuration = "CONFIGURATION",
  models = "MODELS",
  endpoints = "ENDPOINTS",
  datasets = "DATASETS",
  evaluations = "EVALUATIONS",
  rbac = "RBAC",
};
