import { ContractObjectEmphasis, ContractObjectVerification, ContractObjectVerificationItem, ContractObjectVerificationLineItem, ContractObjectVerificationLineItemVerification, ContractSettings, ContractSettingsLabels, ContractSettingsStrings, type ContractExtractionDictionary, type ContractExtractionPage, type ContractExtractionPageItem, type ContractObject, type ContractProjectObject } from "../interfaces";
import { isObject } from "./generalDiscriminators";





// RESPONSES
/////////////


export function isGetContractObjectResponse(data: unknown): data is ContractObject {
    return isContractObject(data);
}

export function isGetContractProjectsListReponse(data: unknown): data is ContractProjectObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isContractProjectObject(item)) return false;
    }
    return true;
}

export function isGetContractProjectByIdResponse(data: unknown): data is ContractProjectObject {
    return isContractProjectObject(data);
}


export function isSubmitContractResponse(data: unknown): data is ContractObject {
    return isContractObject(data);
}

export function isDeleteContractResponse(data: unknown): data is ContractObject {
    return isContractObject(data);
}

export function isGetContractProjectSettingsByIdResponse(data: unknown): data is ContractSettings {
    return isContractProjectSettingsObject(data);
}

export function isGetContractProjectContractsResponse(data: unknown): data is ContractObject[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isContractObject(item)) return false;
    }
    return true;
}

export function isGetContractObjectEmphasisResponse(data: unknown): data is ContractObjectEmphasis {
    return isContractObjectEmphasis(data);
}

export function isGetContractObjectVerificationResponse(data: unknown): data is ContractObjectVerification {
    return isContractVerification(data);
}

export function isGetContractObjectVerificationLineItemsResponse(data: unknown): data is ContractObjectVerificationLineItem[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (!isContractObjectVerficationLineItem(item)) return false;
    }
    return true;
}

export function isReprocessContractResponse(data: unknown): data is ContractObject {
    return isContractObject(data);
}


export function isCreateProjectResponse(data: unknown): data is ContractProjectObject {
    return isContractProjectObject(data);
}
export function isEditProjectResponse(data: unknown): data is ContractProjectObject {
    return isContractProjectObject(data);
}
export function isDeleteProjectResponse(data: unknown): data is ContractProjectObject {
    return isContractProjectObject(data);
}




// OBJECTS
///////////



export function isContractProjectObject(item: unknown): item is ContractProjectObject {
    return isObject(item) &&
        "id" in item &&
        "create_date" in item &&
        "update_date" in item &&
        "name" in item &&
        "description" in item &&
        "settings" in item &&
        "reports" in item &&
        (item.settings === null || isObject(item.settings)) &&
        (item.reports === null || Array.isArray(item.reports))
}

export function isContractObject(item: unknown): item is ContractObject {
    return isObject(item) &&
        "id" in item &&
        "project_id" in item &&
        "status" in item &&
        "content_type" in item &&
        "filename" in item &&
        "filesize" in item &&
        "file_ref" in item &&
        "response" in item &&
        "creation_date" in item
}

export function isContractProjectSettingsObject(item: unknown): item is ContractSettings {
    return isObject(item) &&
        "strings" in item && isContractProjectSettingsStringObject(item.strings) &&
        "labels" in item && isContractProjectSettingsLabelsObject(item.labels)
}

export function isContractProjectSettingsStringObject(item: unknown): item is ContractSettingsStrings {
    return isObject(item) &&
        "li_keys_to_exclude" in item && Array.isArray(item.li_keys_to_exclude) &&
        "li_amount" in item && Array.isArray(item.li_amount) &&
        "li_qty" in item && Array.isArray(item.li_qty) &&
        "li_desc" in item && Array.isArray(item.li_desc) &&
        "li_ibx" in item && Array.isArray(item.li_ibx) &&
        "li_product_identifier" in item && Array.isArray(item.li_product_identifier) &&
        "li_nbd" in item && Array.isArray(item.li_nbd) &&
        "li_unit_price" in item && Array.isArray(item.li_unit_price) &&
        "li_action" in item && Array.isArray(item.li_action) &&
        "po_number" in item && Array.isArray(item.po_number) &&
        "customer_po_number" in item && Array.isArray(item.customer_po_number) &&
        "total_amount" in item && Array.isArray(item.total_amount) &&
        "non_rec_charges" in item && Array.isArray(item.non_rec_charges) &&
        "rec_charges" in item && Array.isArray(item.rec_charges) &&
        "date_issued" in item && Array.isArray(item.date_issued) &&
        "contr_number" in item && Array.isArray(item.contr_number) &&
        "inv_number" in item && Array.isArray(item.inv_number) &&
        "customer_name" in item && Array.isArray(item.customer_name)
}

export function isContractProjectSettingsLabelsObject(item: unknown): item is ContractSettingsLabels {
    return isObject(item) &&
        "description" in item &&
        "product_identifier" in item &&
        "quantity" in item &&
        "total_cost" in item &&
        "unit_cost" in item &&
        "need_by_date" in item &&
        "ibx" in item &&
        "site_name" in item &&
        "site_address" in item
}

export function isContractVerification(item: unknown): item is ContractObjectVerification {
    return isObject(item) &&
        "verification_status" in item &&
        "line_items" in item &&
        "vsow" in item && isContractObjectVerificationItemArray(item.vsow) &&
        "csow" in item && isContractObjectVerificationItemArray(item.csow) &&
        "invoice" in item && isContractObjectVerificationItemArray(item.invoice) &&
        "po" in item && isContractObjectVerificationItemArray(item.po)
}


export function isContractObjectVerificationItemArray(array: unknown): array is ContractObjectVerificationItem[] {
    if (!Array.isArray(array)) return false;
    for (const item of array) {
        if (!isContractObjectVerificationItem(item)) return false;
    }
    return true;
}

export function isContractObjectVerificationItem(item: unknown): item is ContractObjectVerificationItem {
    return isObject(item) &&
        "verification_status" in item &&
        "file_ref" in item &&
        "file_id" in item &&
        "po_number" in item &&
        "supplier" in item &&
        "total_amount" in item
}

export function isContractObjectEmphasis(item: unknown): item is ContractObjectEmphasis {
    return isObject(item) &&
        "invoice_number" in item &&
        "po_number" in item &&
        "customer_po_number" in item &&
        "customer_name" in item &&
        "contract_number" in item &&
        "supplier" in item &&
        "rec_charges" in item &&
        "non_rec_charges" in item &&
        "total_amount" in item
}

export function isContractObjectVerficationLineItem(item: unknown): item is ContractObjectVerificationLineItem {
    return isObject(item) &&
        "id" in item &&
        "description" in item &&
        "product_identifier" in item &&
        "quantity" in item &&
        "need_by_date" in item &&
        "unit_price" in item &&
        "amount" in item &&
        "action" in item &&
        "ibx" in item &&
        "site_name" in item &&
        "site_address" in item &&
        "verification" in item &&
        isContractObjectVerificationLineItemVerification(item.verification)
}

export function isContractObjectVerificationLineItemVerification(item: unknown): item is ContractObjectVerificationLineItemVerification {
    return isObject(item) &&
        "verification_status" in item &&
        "vsow" in item &&
        "po" in item &&
        "invoice" in item
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

