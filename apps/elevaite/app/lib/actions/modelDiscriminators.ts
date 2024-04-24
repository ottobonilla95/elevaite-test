import type { AvailableModelObject, EvaluationObject, InferEmbeddingDto, InferSummarizationDto, InferTextGenerationDto, ModelDatasetObject, ModelEndpointCreationObject, ModelEndpointObject, ModelEvaluationLogObject, ModelObject, ModelParametersObject, ModelRegistrationLogObject } from "../interfaces";
import { isArrayOfNumbers, isArrayOfStrings, isObject } from "./generalDiscriminators";





// RESPONSES
/////////////


export function isGetAvailableModelsResponse(data: unknown): data is AvailableModelObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isAvailableModelObject(item)) return false;
    }
    return true;
}

export function isGetModelByIdResponse(data: unknown): data is ModelObject {
    return isModelObject(data);
}

export function isGetModelLogsResponse(data: unknown): data is ModelRegistrationLogObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelLogObject(item)) return false;
    }
    return true;
}

export function isGetEvaluationLogsResponse(data: unknown): data is ModelEvaluationLogObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isEvaluationLogObject(item)) return false;
    }
    return true;
}

export function isGetModelParametersResponse(data: unknown): data is ModelParametersObject {
    return isModelParametersObject(data);
}

export function isGetModelEndpointsResponse(data: unknown): data is ModelEndpointObject[] {    
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelEndpointObject(item)) return false;
    }
    return true;
}

export function isDeployModelResponse(data: unknown): data is ModelEndpointCreationObject {
    return isModelEndpointCreationObject(data);
}

export function isInferEndpointTextGenerationResponse(data: unknown): data is InferTextGenerationDto {
    return isInferTextGenerationDto(data);
}

export function isInferEndpointSummarizationResponse(data: unknown): data is InferSummarizationDto {
    return isInferSummarizationDto(data);
}

export function isInferEndpointEmbeddingResponse(data: unknown): data is InferEmbeddingDto {
    return isInferEmbeddingDto(data);
}

export function isGetDatasetsResponse(data: unknown): data is ModelDatasetObject[] {    
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelDatasetObject(item)) return false;
    }
    return true;
}

export function isGetModelsResponse(data: unknown): data is ModelObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelObject(item)) return false;
    }
    return true;
}

export function isGetModelEvaluationsResponse(data: unknown): data is EvaluationObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isEvaluationObject(item)) return false;
    }
    return true;
}




// OBJECTS
///////////

export function isAvailableModelObject(item: unknown): item is AvailableModelObject {
    return isObject(item) &&
        "id" in item &&
        "created_at" in item &&
        "gated" in item &&
        "library_name" in item;
}

export function isModelObject(item: unknown): item is ModelObject {
    return isObject(item) &&
        "id" in item &&
        "name" in item &&
        "status" in item &&
        "task" in item &&
        "tags" in item &&
        "huggingface_repo" in item;
}

export function isModelLogObject(item: unknown): item is ModelRegistrationLogObject {
    return isObject(item) &&
        "id" in item &&
        "model_id" in item &&
        "message" in item &&
        "stream" in item &&
        "time" in item ;
}

export function isEvaluationLogObject(item: unknown): item is ModelEvaluationLogObject {
    return isObject(item) &&
        "id" in item &&
        "evaluation_id" in item &&
        "message" in item &&
        "stream" in item &&
        "time" in item ;
}

export function isModelEndpointObject(item: unknown): item is ModelEndpointObject {
    return isObject(item) &&
    "endpoint_id" in item &&
    "model_id" in item &&
    "url" in item;
}

export function isModelEndpointCreationObject(item: unknown): item is ModelEndpointCreationObject {
    return isObject(item) &&
    "endpoint_id" in item;
}

export function isInferTextGenerationDto(item: unknown): item is InferTextGenerationDto {
    return isObject(item) &&
    "results" in item &&
    Array.isArray(item.results) && 
    item.results.length >= 1 &&
    doesEachItemInArrayHaveField(item.results, "generated_text");
}

export function isInferSummarizationDto(item: unknown): item is InferSummarizationDto {
    return isObject(item) &&
    "results" in item &&
    Array.isArray(item.results) && 
    item.results.length >= 1 &&
    doesEachItemInArrayHaveField(item.results, "summary_text");
}

export function isInferEmbeddingDto(item: unknown): item is InferEmbeddingDto {
    return isObject(item) &&
    "results" in item &&
    isArrayOfNumbers(item.results);
}

export function isModelDatasetObject(item: unknown): item is ModelDatasetObject {
    return isObject(item) &&
    "id" in item &&
    "name" in item &&
    "status" in item &&
    "huggingface_repo" in item &&
    "tags" in item;
}

export function isModelParametersObject(item: unknown): item is ModelParametersObject {
    return isObject(item) &&
        "architectures" in item &&
        "model_type" in item;
}

export function isEvaluationObject(item: unknown): item is EvaluationObject {
    return isObject(item) &&    
    "id" in item &&
    "model_id" in item &&
    "dataset_id" in item &&
    "status" in item &&
    "results" in item;
}




// OBJECT FUNCTIONS
////////////////////

function doesEachItemInArrayHaveField(array: unknown[], field: string): boolean {
    for (const item of array) {
        if (!isObject(item) || !(field in item)) return false;
    }
    return true;
}



