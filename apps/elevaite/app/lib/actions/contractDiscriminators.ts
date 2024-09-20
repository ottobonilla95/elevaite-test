import { type ContractProjectObject, type ContractExtractionDictionary, type ContractExtractionPage, type ContractExtractionPageItem } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////


export function isGetContractProjectsListReponse(data: unknown): data is ContractProjectObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isContractProjectObject(item)) return false;
    }
    return true;
}


export function isSubmitContractResponse(data: unknown): data is ContractExtractionDictionary {
    return isContractExtractionDictionaryObject(data);
}


export function isCreateProjectResponse(data: unknown): data is ContractProjectObject {
    return isContractProjectObject(data);
}




// OBJECTS
///////////



export function isContractProjectObject(item: unknown): item is ContractProjectObject {
    return isObject(item) &&
        "id" in item &&
        "creation_date" in item &&
        "name" in item &&
        "description" in item &&
        "reports" in item &&
        Array.isArray(item.reports);
}

export function isContractExtractionDictionaryObject(item: unknown): item is ContractExtractionDictionary {
    if (isObject(item)) {
        return Object.entries(item).every(([key, value]) => {
            return /^page_\d+$/.test(key) && isContractExtractionPage(value);
        });
    } return false;

    function isContractExtractionPage(page: unknown): page is ContractExtractionPage {
        if (isObject(page)) {
            return Object.values(page).every(isContractExtractionPageItem);
        } return false;
    }

    function isContractExtractionPageItem(pageItem: unknown): pageItem is ContractExtractionPageItem {
        if (typeof pageItem === "string") {
            return true;
        }    
        if (Array.isArray(pageItem)) {
            return pageItem.every(foundItem =>
                isObject(foundItem) &&
                Object.values(foundItem).every(val => typeof val === "string")
            );
        } return false;
    }
}

