import { type HuggingfaceDatasetObject, type ModelDatasetObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////





export function isGetDatasetsResponse(data: unknown): data is ModelDatasetObject[] {    
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isModelDatasetObject(item)) return false;
    }
    return true;
}



export function isGetAvailableDatasetsResponse(data: unknown): data is HuggingfaceDatasetObject[] {    
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isHuggingfaceDatasetObject(item)) return false;
    }
    return true;
}





// OBJECTS
///////////




export function isModelDatasetObject(item: unknown): item is ModelDatasetObject {
    return isObject(item) &&    
    "id" in item &&
    "name" in item &&
    "status" in item &&
    "huggingface_repo" in item &&
    "tags" in item;
}


export function isHuggingfaceDatasetObject(item: unknown): item is HuggingfaceDatasetObject {
    return isObject(item) &&    
    "id" in item &&
    // "author" in item &&
    "created_at" in item &&
    "last_modified" in item &&
    "gated" in item &&
    "sha" in item;
}
