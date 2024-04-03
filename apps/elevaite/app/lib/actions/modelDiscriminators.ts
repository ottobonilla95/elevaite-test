import type { AvailableModelObject, ModelObject, ModelParametersObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";





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

export function isGetModelParametersResponse(data: unknown): data is ModelParametersObject {
    return isModelParametersObject(data);
}

export function isGetModelsResponse(data: unknown): data is ModelObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelObject(item)) return false;
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
export function isModelParametersObject(item: unknown): item is ModelParametersObject {
    return isObject(item) &&
        "architectures" in item &&
        "model_type" in item;
        // "hidden_size" in item &&
        // "intermediate_size" in item;
}