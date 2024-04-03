import type { AppInstanceObject, ApplicationConfigurationObject, ApplicationObject, ChartDataObject, Initializers, PipelineObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";




// RESPONSES
/////////////


export function isGetApplicationListReponse(data: unknown): data is ApplicationObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isApplicationObject(item)) return false;
    }
    return true;
}

export function isGetApplicationResponse(data: unknown): data is ApplicationObject {
    return isApplicationObject(data);
}

export function isGetApplicationconfigurationsResponse(data: unknown): data is ApplicationConfigurationObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isApplicationConfigurationObject(item)) return false;
    }
    return true;
}

export function isGetApplicationPipelinesResponse(data: unknown): data is PipelineObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isApplicationPipelineObject(item)) return false;
    }
    return true;
}

export function isGetInstanceChartDataResponse(data: unknown): data is ChartDataObject {
    return isInstanceChartObject(data);
}

export function isGetInstanceListResponse(data: unknown): data is AppInstanceObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isInstanceObject(item)) return false;
    }
    return true;
}

export function isGetInstanceResponse(data: unknown): data is AppInstanceObject {
    return isInstanceObject(data);
}

export function isCreateInstanceResponse(data: unknown): data is AppInstanceObject {
    return isInstanceObject(data);
}

export function isCreateConfigurationResponse(data: unknown): data is ApplicationConfigurationObject {
    return isApplicationConfigurationObject(data);
}

export function isInitializerDto(data: unknown): data is Initializers {
    return isInitializerObject(data);
}



// OBJECTS
///////////

export function isApplicationObject(item: unknown): item is ApplicationObject {
    return isObject(item) &&
        "id" in item &&
        "applicationType" in item &&
        "creator" in item &&
        "description" in item &&
        "icon" in item &&
        "title" in item &&
        "version" in item;
}

export function isInstanceChartObject(item: unknown): item is ChartDataObject {
    return isObject(item) &&
        "totalItems" in item &&
        "ingestedItems" in item &&
        "avgSize" in item &&
        "totalSize" in item &&
        "ingestedSize" in item;
}

export function isInstanceObject(item: unknown): item is AppInstanceObject {
    return isObject(item) &&
        "id" in item &&
        "datasetId" in item &&
        "creator" in item &&
        "startTime" in item &&
        "status" in item;
}

export function isApplicationPipelineObject(item: unknown): item is PipelineObject {
    return isObject(item) &&
        "id" in item &&
        "entry" in item &&
        "label" in item &&
        "steps" in item;
}

export function isInitializerObject(item: unknown): item is Initializers {
    return isObject(item) &&
        "projectId" in item &&
        "creator" in item;
}

export function isApplicationConfigurationObject(item: unknown): item is ApplicationConfigurationObject {
    return isObject(item) &&
        "id" in item &&
        "applicationId" in item &&
        "name" in item &&
        "isTemplate" in item &&
        "createDate" in item &&
        "updateDate" in item &&
        "raw" in item;
}

