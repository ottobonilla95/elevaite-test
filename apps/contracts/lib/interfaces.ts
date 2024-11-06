
// Remember to change the discriminators if you change an interface!

import type { CommonInputProps, CommonCheckboxProps } from "@repo/ui/components";



// ENUMS
////////////////

export enum CONTRACTS_TABS {
    SUPPLIER_CONTRACTS = "VSOW",
    CUSTOMER_CONTRACTS = "CSOW",
    SUPPLIER_POS = "Supplier POs",
    SUPPLIER_INVOICES = "Supplier Invoices",
}

export enum CONTRACT_STATUS {
    COMPLETED = "completed",
    PROCESSING = "processing",
    FAILED = "failed",
    APPROVED = "approved",
    REJECTED = "rejected"
}

export enum CONTRACT_TYPES {
    VSOW = "vsow",
    CSOW = "csow",
    PURCHASE_ORDER = "po",
    INVOICE = "invoice",
}

export enum ContractVariations {
    Default = 0,
    Iopex = 1,
};




// SYSTEM INTERFACES
////////////////


export interface FiltersStructure {
    label?: string;
    filters: (FilterUnitStructure|FilterGroupStructure)[];
}

export interface FilterUnitStructure {
    label: string;
    isSelected?: boolean;
    isActive?: boolean;
}

export interface FilterGroupStructure {
    label: string;
    field?: string;
    isClosed?: boolean;
    filters: FilterUnitStructure[];
}

export interface SortingObject<ObjectToBeSorted, SpecialHandlingFieldsEnum = undefined> {
    field?: keyof ObjectToBeSorted;
    isDesc?: boolean;
    specialHandling?: SpecialHandlingFieldsEnum;
}






// COMMON INTERFACES
////////////////


// CONTRACTS
////////////////

export interface ContractProjectObject {
    id: string | number;
    name: string;
    description: string;
    create_date: string;
    update_date: string;
    reports?: ContractObject[];
    settings?: ContractSettings;
}

export interface ContractSettings {
    strings: ContractSettingsStrings;
    labels: ContractSettingsLabels;
}

export interface ContractSettingsStrings {
    li_keys_to_exclude: string[];
    li_amount: string[];
    li_qty: string[];
    li_desc: string[];
    li_ibx: string[];
    li_product_identifier: string[];
    li_nbd: string[];
    li_unit_price: string[];
    li_action: string[];
    po_number: string[];
    customer_po_number: string[];
    total_amount: string[];
    non_rec_charges: string[];
    rec_charges: string[];
    date_issued: string[];
    contr_number: string[];
    inv_number: string[];
    customer_name: string[];
    service_start_date: string[];
    service_end_date: string[];
    service_combined_date: string[];
}

export interface ContractSettingsLabels {
    // [K in keyof Omit<ContractObjectVerificationLineItem, "id" | "verification">]: string;
    description: string;
    product_identifier: string;
    quantity: string;
    total_cost: string;
    unit_cost: string;
    need_by_date: string;
    ibx: string;
    site_name: string;
    site_address: string;
}

export interface ContractObject {
    id: string | number;
    project_id: string | number;
    status: CONTRACT_STATUS;
    content_type: CONTRACT_TYPES;
    label?: string | null;
    filename: string;
    filesize: number; // Bytes
    file_ref: File | string | null; // Url
    response: ContractExtractionDictionary | null;
    response_comments?: string[];
    po_number?: string | null;
    supplier?: string | null;
    matched_supplier?: string | null;
    normalized_supplier?: string | null;
    total_amount?: string | null;
    verification?: ContractObjectVerification | null;
    line_items?: ContractObjectVerificationLineItem[] | null;
    highlight?: ContractObjectEmphasis | null;
    tags?: string[];
    creation_date: string;
    checksum: string; // MD5
    index_key?: string;
}

export interface ContractObjectEmphasis {
    invoice_number: string | null;
    po_number: string | null;
    customer_po_number: string | null;
    customer_name: string | null;
    contract_number: string | null;
    supplier: string | null;
    rec_charges: string | null;
    non_rec_charges: string | null;
    total_amount: string | null;
}

export interface ContractObjectVerificationLineItem {
    id: number;
    description?: string | null;
    product_identifier?: string | null;
    quantity?: string | null;
    need_by_date?: string | null;
    unit_price?: number | null;
    amount?: number | null;
    action?: string | null;
    ibx?: string | null;
    site_name?: string | null;
    site_address?: string | null;
    verification: ContractObjectVerificationLineItemVerification;
}

export interface ContractObjectVerificationLineItemVerification {
    verification_status: boolean;
    vsow: boolean;
    po: boolean;
    invoice: boolean;
    csow: boolean;
    line_item_match_id?: number;
    line_item_match_report_id?: number;
}

export interface ContractObjectVerification {
    verification_status: boolean;
    line_items: boolean;
    vsow?: ContractObjectVerificationItem[];
    csow?: ContractObjectVerificationItem[];
    invoice?: ContractObjectVerificationItem[];
    po?: ContractObjectVerificationItem[];
}

export interface ContractObjectVerificationItem {
    verification_status: boolean;
    file_ref?: string;
    file_id?: string | number;
    po_number?: VerificationItem;
    supplier?: VerificationItem;
    total_amount?: VerificationItem;
}
export interface VerificationItem {
    verification_status: boolean;
    value?: string;
}

export type ContractExtractionPageItem = string | string[] | Record<string, unknown>;
export type ContractExtractionPage = Record<string, ContractExtractionPageItem> & Record<`Line Item ${number}`, Record<string, string>>;
export type ContractExtractionDictionary = Record<`page_${number}`, ContractExtractionPage>;
