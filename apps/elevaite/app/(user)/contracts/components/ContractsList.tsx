import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListRow, type RowStructure, specialHandlingListRowFields } from "../../../lib/components/ListRow";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { formatBytes } from "../../../lib/helpers";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractObject, CONTRACTS_TABS } from "../../../lib/interfaces";
import "./ContractsList.scss";
import { ContractUpload } from "./ContractUpload";



interface FilterTag {
    label: string;
    isActive?: boolean;
}


const ContractsTabsArray: {label: CONTRACTS_TABS, tooltip?: string, isDisabled?: boolean}[] = [
    { label: CONTRACTS_TABS.SUPPLIER_CONTRACTS },
    { label: CONTRACTS_TABS.CUSTOMER_CONTRACTS },
    { label: CONTRACTS_TABS.SUPPLIER_POS, tooltip: "Supplier Purchase Orders" },
    { label: CONTRACTS_TABS.SUPPLIER_INVOICES },
];

const contractsListStructure: RowStructure<ContractObject>[] = [
    { header: "Status", field: "status", isSortable: true, formattingFunction: structureStatus, align: "center" },
    { header: "Name", field: "label", isSortable: true, formattingFunction: structureName, },
    { header: "Contract No.", field: "id", isSortable: true, },
    { header: "File Size", field: "filesize", isSortable: true, style: "block", align: "center", formattingFunction: structureFileSize, },
    { header: "Tags", field: "tags", isSortable: false, specialHandling: specialHandlingListRowFields.TAGS },
    { header: "Approval", field: "approval", isSortable: true, formattingFunction: structureApproval, },
    // { header: "Created at", field: "creation_date", isSortable: true, specialHandling: specialHandlingListRowFields.SHORT_DATE, align: "right" },
];

// List structure formatting functions
function structureName(listItem: ContractObject): string {
    return listItem.label && listItem.label.length > 0 ? listItem.label : listItem.filename;
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
///////////////////////////////////////




export function ContractsList(): JSX.Element {
    const contractsContext = useContracts();
    const [selectedTab, setSelectedTab] = useState(CONTRACTS_TABS.SUPPLIER_CONTRACTS);
    const [contracts, setContracts] = useState<ContractObject[]>([]);
    const [displayContracts, setDisplayContracts] = useState<ContractObject[]>([]);
    const [filterTags, setFilterTags] = useState<FilterTag[]>([]);
    const [isUploadOpen, setIsUploadOpen] = useState(false);


    useEffect(() => {
        setContracts(contractsContext.selectedProject?.reports ?? []);
    }, [contractsContext.selectedProject?.reports]);

    useEffect(() => {        
        setFilterTags(getFilterTags(getTabContracts(contracts, selectedTab)));
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



    function formatDisplayContracts(passedContracts: ContractObject[]): void {
        const clonedContracts = structuredClone(passedContracts);

        const tabContracts = getTabContracts(clonedContracts, selectedTab);

        const taggedContracts = getTaggedContracts(tabContracts, filterTags);

        setDisplayContracts(taggedContracts);
    }

    function getTabContracts(allContracts: ContractObject[], tab: CONTRACTS_TABS): ContractObject[] {
        let contractType: CONTRACT_TYPES;
        switch (tab) {
            case CONTRACTS_TABS.CUSTOMER_CONTRACTS: contractType = CONTRACT_TYPES.VSOW; break;
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
                    <div className="cross-match-container">
                        <CrossMatchBit value={10} label="Total invoices pending approval" />
                        <CrossMatchBit value={8} label="PO matches failed" />
                        <CrossMatchBit value={2} label="VSOW matches failed" />
                    </div>
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
                    

                    
                    <div className="contracts-list-table-contents">
                        <ListRow<ContractObject>
                            isHeader
                            structure={contractsListStructure}
                            // onSort={handleSort}
                            // sorting={sorting}
                        />
                        {displayContracts.length === 0 && contractsContext.loading.contracts ?
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
                                structure={contractsListStructure}
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
    value: number;
    label: string;
}

function CrossMatchBit(props: CrossMatchBitProps): JSX.Element {
    return (
        <div className="cross-match-bit-container">
            <span className="cross-bit-value">{props.value}</span>
            <span className="cross-bit-label">{props.label}</span>
        </div>
    );
}


