import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListRow, type RowStructure, specialHandlingListRowFields } from "../../../lib/components/ListRow";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { CONTRACT_TYPES, type ContractObject, CONTRACTS_TABS } from "../../../lib/interfaces";
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
    { header: "Status", field: "status", isSortable: true, specialHandling: specialHandlingListRowFields.CONTRACTS_STATUS, align: "center" },
    { header: "Name", field: "name", isSortable: true },
    { header: "File Size", field: "fileSize", isSortable: true, style: "block", align: "center" },
    { header: "Tags", field: "tags", isSortable: false, specialHandling: specialHandlingListRowFields.TAGS },
    { header: "Created at", field: "createdAt", isSortable: true, specialHandling: specialHandlingListRowFields.SHORT_DATE, align: "right" },
];





export function ContractsList(): JSX.Element {
    const contractsContext = useContracts();
    const [selectedTab, setSelectedTab] = useState(CONTRACTS_TABS.SUPPLIER_CONTRACTS);
    const [contracts, setContracts] = useState<ContractObject[]>([]);
    const [displayContracts, setDisplayContracts] = useState<ContractObject[]>([]);
    const [filterTags, setFilterTags] = useState<FilterTag[]>([]);
    const [isUploadOpen, setIsUploadOpen] = useState(false);


    useEffect(() => {
        setContracts(contractsContext.contracts);
        setFilterTags(getFilterTags());
    }, [contractsContext.contracts]);

    useEffect(() => {
        formatDisplayContracts(contracts);
    }, [contracts, selectedTab, filterTags]);

    

    function getFilterTags(): FilterTag[] {
        const uniqueTags = Array.from(new Set(contractsContext.contracts.flatMap(contract => contract.tags)));
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
            case CONTRACTS_TABS.CUSTOMER_CONTRACTS: contractType = CONTRACT_TYPES.CONTRACT; break;
            case CONTRACTS_TABS.SUPPLIER_CONTRACTS: contractType = CONTRACT_TYPES.CONTRACT; break;
            case CONTRACTS_TABS.SUPPLIER_INVOICES: contractType = CONTRACT_TYPES.INVOICE; break;
            case CONTRACTS_TABS.SUPPLIER_POS: contractType = CONTRACT_TYPES.PURCHASE_ORDER; break;
        }
        return allContracts.filter(contract => contract.type === contractType);
    }

    function getTaggedContracts(tabbedContracts: ContractObject[], filters: FilterTag[]): ContractObject[] {
        if (getActiveTagsAmount() <= 0) return tabbedContracts;
        const activeTags = filters.filter(item => item.isActive).map(tag => tag.label);
        return tabbedContracts.filter(contract => activeTags.some(tag => contract.tags.includes(tag)));
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
                            There are no contracts to display.
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