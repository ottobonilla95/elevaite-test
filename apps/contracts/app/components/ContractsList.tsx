import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListRow, type RowStructure, specialHandlingListRowFields } from "../lib/components/ListRow";
import { useContracts } from "../lib/contexts/ContractsContext";
import { formatBytes } from "../lib/helpers";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractObject, CONTRACTS_TABS } from "../lib/interfaces";
import "./ContractsList.scss";
import { ContractUpload } from "./ContractUpload";



interface FilterTag {
    label: string;
    isActive?: boolean;
}

interface CrossMatchFields {
    [CONTRACT_TYPES.INVOICE]: number,
    [CONTRACT_TYPES.PURCHASE_ORDER]: number,
    [CONTRACT_TYPES.VSOW]: number
    [CONTRACT_TYPES.CSOW]: number
}


const ContractsTabsArray: {label: CONTRACTS_TABS, tooltip?: string, isDisabled?: boolean}[] = [
    { label: CONTRACTS_TABS.SUPPLIER_CONTRACTS },
    { label: CONTRACTS_TABS.CUSTOMER_CONTRACTS },
    { label: CONTRACTS_TABS.SUPPLIER_POS, tooltip: "Supplier Purchase Orders" },
    { label: CONTRACTS_TABS.SUPPLIER_INVOICES },
];

// List structure formatting functions
function structureName(listItem: ContractObject): React.ReactNode {
    return (
        <span className="contract-name" title={listItem.label ? listItem.filename : ""}>
            {listItem.label && listItem.label.length > 0 ? listItem.label : listItem.filename}
        </span>
    );
}
function structureFileSize(listItem: ContractObject): string {
    if (!listItem.filesize) return "";
    return formatBytes(listItem.filesize);
}
function structureStatus(listItem: ContractObject): React.ReactNode {
    function statusSwitch(status: CONTRACT_STATUS): JSX.Element {
        switch (status) {
            case CONTRACT_STATUS.COMPLETED: return <ElevaiteIcons.SVGCheckmark/>;
            case CONTRACT_STATUS.APPROVED: return <ElevaiteIcons.SVGCheckmark/>;
            case CONTRACT_STATUS.PROCESSING: return <ElevaiteIcons.SVGInstanceProgress/>;
            case CONTRACT_STATUS.FAILED: return <ElevaiteIcons.SVGXmark/>;
            case CONTRACT_STATUS.REJECTED: return <ElevaiteIcons.SVGXmark/>;
        }
    }
    return (
        <div className={["contract-status", listItem.status].join(" ")} title={listItem.status}>
            {statusSwitch(listItem.status)}
        </div>
    );
}
function structureApproval(listItem: ContractObject): React.ReactNode {
    const isApproved = listItem.status === CONTRACT_STATUS.APPROVED || listItem.verification?.verification_status === true;
    return (
        <span className={["contract-approval", !isApproved ? "pending" : undefined].filter(Boolean).join(" ")}>
            {isApproved ? "Approved" : "Pending"}
        </span>
    );
}
function structureContractNumber(listItem: ContractObject): React.ReactNode {
    switch (listItem.content_type) {
        case CONTRACT_TYPES.INVOICE: return listItem.highlight?.invoice_number ?? "";
        case CONTRACT_TYPES.PURCHASE_ORDER: return listItem.highlight?.po_number ?? "";
        default: return listItem.highlight?.contract_number ?? "";
    }
}
function structureVerification(listItem: ContractObject, checkingType: CONTRACT_TYPES): React.ReactNode {
    let isVerified = false;

    switch (checkingType) {
        case CONTRACT_TYPES.INVOICE: isVerified = listItem.verification?.invoice?.length
                                                ? listItem.verification.invoice.some(item => item.verification_status) : false; break;
        case CONTRACT_TYPES.PURCHASE_ORDER: isVerified = listItem.verification?.po?.length
                                                ?  listItem.verification.po.some(item => item.verification_status) : false; break;
        case CONTRACT_TYPES.VSOW: isVerified = listItem.verification?.vsow?.length
                                                ? listItem.verification.vsow.some(item => item.verification_status) : false; break;
        case CONTRACT_TYPES.CSOW: isVerified = listItem.verification?.csow?.length
                                                ? listItem.verification.csow.some(item => item.verification_status) : false; break;
    }

    return (
        isVerified ? 
            <span className="verified"><ElevaiteIcons.SVGCheckmark/></span>
        :
            <span className="not-verified"><ElevaiteIcons.SVGXmark/></span>
    );
}
///////////////////////////////////////




export function ContractsList(): JSX.Element {
    const contractsContext = useContracts();
    const [selectedTab, setSelectedTab] = useState(CONTRACTS_TABS.SUPPLIER_CONTRACTS);
    const [displayRowsStructure, setDisplayRowsStructure] = useState<RowStructure<ContractObject>[]>([]);
    const [contracts, setContracts] = useState<ContractObject[]>([]);
    const [displayContracts, setDisplayContracts] = useState<ContractObject[]>([]);
    const [crossMatches, setCrossMatches] = useState<CrossMatchFields>();
    const [filterTags, setFilterTags] = useState<FilterTag[]>([]);
    const [isUploadOpen, setIsUploadOpen] = useState(false);


    useEffect(() => {
        setContracts(contractsContext.selectedProject?.reports ?? []);
    }, [contractsContext.selectedProject?.reports]);

    useEffect(() => {    
        setCrossMatches(getCrossMatches(contracts));
    }, [contracts]);

    useEffect(() => {        
        setFilterTags(getFilterTags(getTabContracts(contracts, selectedTab)));
        setDisplayRowsStructure(getRowListStructure(selectedTab));
    }, [contracts, selectedTab]);

    useEffect(() => {
        formatDisplayContracts(contracts);
    }, [contracts, selectedTab, filterTags]);

    

    function getFilterTags(contractsWithTags: ContractObject[]): FilterTag[] {
        const uniqueTags = Array.from(new Set(contractsWithTags.flatMap(contract => contract.tags ?? [])));
        return uniqueTags.map(tag => ({ label: tag, isActive: false }));
    }

    function getActiveTagsAmount(): number {
        return filterTags.filter(tag => tag.isActive).length;
    }

    function getRowListStructure(tab: CONTRACTS_TABS): RowStructure<ContractObject>[] {
        const structure: RowStructure<ContractObject>[] = [];

        structure.push({ header: "Status", field: "status", isSortable: true, formattingFunction: structureStatus, align: "center" });
        structure.push({ header: "Name", field: "label", isSortable: true, formattingFunction: structureName, });

        switch (tab) {
            case CONTRACTS_TABS.SUPPLIER_INVOICES: structure.push({ header: "Invoice Number", field: "invoice_number", isSortable: true, formattingFunction: structureContractNumber, }); break;
            case CONTRACTS_TABS.SUPPLIER_POS: structure.push({ header: "PO Number", field: "po_number", isSortable: true, formattingFunction: structureContractNumber, }); break;
            default: structure.push({ header: "Contract Number", field: "contract_number", isSortable: true, formattingFunction: structureContractNumber, });
        };

        structure.push({ header: "File Size", field: "filesize", isSortable: true, style: "block", align: "center", formattingFunction: structureFileSize, });
        structure.push({ header: "Tags", field: "tags", isSortable: false, specialHandling: specialHandlingListRowFields.TAGS });
        
        if (selectedTab === CONTRACTS_TABS.SUPPLIER_INVOICES)
            structure.push({ header: "Approval", field: "approval", isSortable: true, formattingFunction: structureApproval, });

        // structure.push({ header: "Created at", field: "creation_date", isSortable: true, specialHandling: specialHandlingListRowFields.SHORT_DATE, align: "right" });
        
        switch (tab) {
            case CONTRACTS_TABS.SUPPLIER_INVOICES: 
                structure.push({ header: "VSOW", field: "inv_vsow_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.VSOW), });
                structure.push({ header: "PO", field: "inv_po_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.PURCHASE_ORDER), });
                break;
            case CONTRACTS_TABS.SUPPLIER_POS:
                structure.push({ header: "VSOW", field: "po_vsow_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.VSOW), });
                structure.push({ header: "Inv.", field: "po_inv_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.INVOICE), });
                break;
            case CONTRACTS_TABS.CUSTOMER_CONTRACTS:
                structure.push({ header: "VSOW", field: "csow_vsow_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.VSOW), });
                structure.push({ header: "PO", field: "csow_po_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.PURCHASE_ORDER), });
                break;
            case CONTRACTS_TABS.SUPPLIER_CONTRACTS:
                structure.push({ header: "CSOW", field: "vsow_csow_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.CSOW), });
                structure.push({ header: "Inv.", field: "vsow_inv_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.INVOICE), });
                structure.push({ header: "PO", field: "vsow_po_verification", align: "center", isSortable: false, formattingFunction: (item) => structureVerification(item, CONTRACT_TYPES.PURCHASE_ORDER), });
                break;
        }
        return structure;
    }



    function formatDisplayContracts(passedContracts: ContractObject[]): void {
        const clonedContracts = structuredClone(passedContracts);

        const tabContracts = getTabContracts(clonedContracts, selectedTab);

        const taggedContracts = getTaggedContracts(tabContracts, filterTags);

        setDisplayContracts(taggedContracts);
    }

    function getTabContracts(allContracts: ContractObject[], tab: CONTRACTS_TABS): ContractObject[] {
        let contractType: CONTRACT_TYPES;
        switch (tab) {
            case CONTRACTS_TABS.CUSTOMER_CONTRACTS: contractType = CONTRACT_TYPES.CSOW; break;
            case CONTRACTS_TABS.SUPPLIER_CONTRACTS: contractType = CONTRACT_TYPES.VSOW; break;
            case CONTRACTS_TABS.SUPPLIER_INVOICES: contractType = CONTRACT_TYPES.INVOICE; break;
            case CONTRACTS_TABS.SUPPLIER_POS: contractType = CONTRACT_TYPES.PURCHASE_ORDER; break;
        }
        return allContracts.filter(contract => contract.content_type === contractType);
    }

    function getTaggedContracts(tabbedContracts: ContractObject[], filters: FilterTag[]): ContractObject[] {
        if (getActiveTagsAmount() <= 0) return tabbedContracts;
        const activeTags = filters.filter(item => item.isActive).map(tag => tag.label);
        return tabbedContracts.filter(contract => activeTags.some(tag => contract.tags?.includes(tag)));
    }

    function getCrossMatches(contractsToCheck: ContractObject[]): CrossMatchFields {
        const invoiceFailures = contractsToCheck.filter(item => item.content_type === CONTRACT_TYPES.INVOICE && item.verification?.verification_status === false).length;
        const poFailures = contractsToCheck.filter(item => item.content_type === CONTRACT_TYPES.PURCHASE_ORDER && item.verification?.verification_status === false).length;
        const vsowFailures = contractsToCheck.filter(item => item.content_type === CONTRACT_TYPES.VSOW && item.verification?.verification_status === false).length;
        const csowFailures = contractsToCheck.filter(item => item.content_type === CONTRACT_TYPES.CSOW && item.verification?.verification_status === false).length;

        return {
            [CONTRACT_TYPES.INVOICE]: invoiceFailures,
            [CONTRACT_TYPES.PURCHASE_ORDER]: poFailures,
            [CONTRACT_TYPES.VSOW]: vsowFailures,
            [CONTRACT_TYPES.CSOW]: csowFailures,
        }
    }



    function handleTabSelection(passedTab: CONTRACTS_TABS): void {
        setSelectedTab(passedTab);
    }

    function handleFilterTagClick(tag: FilterTag): void {        
        setFilterTags(current => 
            current.map(currentTag => currentTag.label === tag.label ? {...currentTag, isActive: !tag.isActive} : currentTag)
        )
    }

    function handleUpload(): void {
        setIsUploadOpen(true);
    }

    function handleRowClick(contract: ContractObject): void {
        // console.log("Contract clicked:", contract);
        contractsContext.setSelectedContract(contract);
    }




    return (
        <div className="contracts-list-container">

            <div className={["cross-match-container", !contractsContext.selectedProject ? "concealed" : undefined ].filter(Boolean).join(" ")}>
                <CrossMatchBit value={crossMatches?.[CONTRACT_TYPES.VSOW]} label="VSOW matches failed" />
                <CrossMatchBit value={crossMatches?.[CONTRACT_TYPES.CSOW]} label="CSOW matches failed" />
                <CrossMatchBit value={crossMatches?.[CONTRACT_TYPES.PURCHASE_ORDER]} label="PO matches failed" />
                <CrossMatchBit value={crossMatches?.[CONTRACT_TYPES.INVOICE]} label="Total invoices pending approval" />
            </div>

            <div className="tabs-container">
                {ContractsTabsArray.map((item: {label: CONTRACTS_TABS, tooltip?: string, isDisabled?: boolean}) => 
                    <CommonButton
                        key={item.label}
                        className={[
                            "tab-button",
                            selectedTab === item.label ? "active" : undefined,
                        ].filter(Boolean).join(" ")}                        
                        onClick={() => { handleTabSelection(item.label)}}
                        disabled={item.isDisabled}
                    >
                        {item.label}
                    </CommonButton>
                )}
            </div>


            <div className="contracts-list-table-container">

                {!contractsContext.selectedProject ? 
                    <div className="no-project">
                        <span>No selected project</span>
                        <span>Select one from the list to the left</span>
                    </div>
                :
                <>                    
                    <div className="table-controls-container">
                        <div className="tags-container">
                            {filterTags.map(tag => 
                                <CommonButton 
                                    key={tag.label}
                                    className={["filter-tag", tag.isActive ? "active" : undefined].filter(Boolean).join(" ")}
                                    onClick={() => { handleFilterTagClick(tag)}}
                                >
                                    {tag.label}
                                </CommonButton>
                            )}
                        </div>
                        <div className="controls-container">
                            {/* <CommonButton>
                                <ElevaiteIcons.SVGFilter/>
                            </CommonButton>
                            <CommonButton>
                                <ElevaiteIcons.SVGMagnifyingGlass/>
                            </CommonButton> */}
                            <CommonButton
                                className="upload-button"
                                onClick={handleUpload}
                            >
                                Upload
                            </CommonButton>
                        </div>
                    </div>
                    

                    
                    <div className={["contracts-list-table-contents",
                        selectedTab === CONTRACTS_TABS.SUPPLIER_INVOICES ? "invoice" :
                        selectedTab === CONTRACTS_TABS.SUPPLIER_CONTRACTS ? "vsow" : undefined].filter(Boolean).join(" ")}>
                        <ListRow<ContractObject>
                            isHeader
                            structure={displayRowsStructure}
                            // onSort={handleSort}
                            // sorting={sorting}
                        />
                        {contractsContext.loading.projectReports[contractsContext.selectedProject?.id ?? ""] ?
                            <div className="table-span empty">
                                <ElevaiteIcons.SVGSpinner/>
                                <span>Loading...</span>
                            </div>
                            : displayContracts.length === 0 ? 
                            <div className="table-span empty">
                                There are no entries.
                            </div>

                        :

                        displayContracts.map((account, index) => 
                            <ListRow<ContractObject>
                                key={account.id}
                                rowItem={account}
                                structure={displayRowsStructure}
                                onClick={handleRowClick}
                                menuToTop={displayContracts.length > 4 && index > (displayContracts.length - 4) }
                            />
                        )}
                    </div>
                </>
                }

            </div>


            {!isUploadOpen ? undefined :
                <CommonModal
                    onClose={() => { setIsUploadOpen(false); }}
                >
                    <ContractUpload
                        selectedTab={selectedTab}
                        onClose={() => { setIsUploadOpen(false); }}
                    />
                </CommonModal>
            }


        </div>
    );
}




interface CrossMatchBitProps {
    value?: number;
    label: string;
}

function CrossMatchBit(props: CrossMatchBitProps): JSX.Element {
    return (
        <div className={["cross-match-bit-container", props.value !== undefined && props.value === 0 ? "success" : undefined].filter(Boolean).join(" ")}>
            {props.value === undefined ? <ElevaiteIcons.SVGSpinner/> :
                <span className="cross-bit-value">{props.value}</span>
            }
            <span className="cross-bit-label">{props.label}</span>
        </div>
    );
}


