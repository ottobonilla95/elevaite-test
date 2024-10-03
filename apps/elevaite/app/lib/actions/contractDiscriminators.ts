import { type ContractExtractionDictionary, type ContractExtractionPage, type ContractExtractionPageItem } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////




export function isSubmitContractResponse(data: unknown): data is ContractExtractionDictionary {
    return isContractExtractionDictionaryObject(data);
}




// OBJECTS
///////////



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

