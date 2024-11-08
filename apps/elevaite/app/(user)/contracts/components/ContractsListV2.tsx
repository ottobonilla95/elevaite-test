import { CommonButton, CommonDialog, CommonMenu, type CommonMenuItem, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import React, { useEffect, useState } from "react";
import { ListRow, type RowStructure } from "../../../lib/components/ListRow";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { formatBytes } from "../../../lib/helpers";
import { CONTRACT_TYPES, type ContractObject, ContractObjectVerificationItem, CONTRACTS_TABS, ContractStatus, type SortingObject, type UnverifiedItem, type VerificationQuickList, type VerificationQuickListItem } from "../../../lib/interfaces";
import { AddProject } from "./AddProject";
import "./ContractsListV2.scss";
import { ContractUpload } from "./ContractUpload";




enum ExtractionStatus {
    Uploading = "Upload In\xa0Progress",
    Extracting = "Extraction In\xa0Progress",
    Failed = "Extraction Failed, Re-Upload",
    Complete = "Extraction Complete",
}

enum MatchingStatus {
    Found = "Match Found, Auto-Approved",
    Failed = "Match Failed, Pending",
}

enum MenuActions {
    View = "View",
    Compare = "Compare",
    Delete = "Delete",
};

interface StatusFilterNumbers {
    uploading: number;
    extracting: number;
    failed: number;
    complete: number;
    matched: number;
    unmatched: number;
}

const cleanFilterNumbers: StatusFilterNumbers = {
    uploading: 0,
    extracting: 0,
    failed: 0,
    complete: 0,
    matched: 0,
    unmatched: 0,
}




export function ContractsListV2(): JSX.Element {
    const contractsContext = useContracts();
    const [contracts, setContracts] = useState<ContractObject[]>([]);
    const [displayContracts, setDisplayContracts] = useState<ContractObject[]>([]);
    const [selectedContractTypes, setSelectedContractTypes] = useState<CONTRACT_TYPES[]>([]);
    const [displayRowsStructure, setDisplayRowsStructure] = useState<RowStructure<ContractObject>[]>([]);
    const [statusFilterNumbers, setStatusFilterNumbers] = useState<StatusFilterNumbers>(cleanFilterNumbers);
    const [selectedStatus, setSelectedStatus] = useState<ExtractionStatus | MatchingStatus | undefined>();
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [sorting, setSorting] = useState<SortingObject<ContractObject>>({ field: undefined });
    const [isProjectEditOpen, setIsProjectEditOpen] = useState(false);
    const [contractForDeletion, setContractForDeletion] = useState<ContractObject | undefined>();
    const [isDeleteContractDialogOpen, setIsDeleteContractDialogOpen] = useState(false);


    const contractsListMenu: CommonMenuItem<ContractObject>[] = [
        { label: MenuActions.View, onClick: (item: ContractObject) => { handleMenuClick(item, MenuActions.View); } },
        { label: MenuActions.Compare, onClick: (item: ContractObject) => { handleMenuClick(item, MenuActions.Compare); } },
        { label: MenuActions.Delete, onClick: (item: ContractObject) => { handleMenuClick(item, MenuActions.Delete); } },
    ];

    // useEffect(() => {
    //     console.log("Display Contracts:", displayContracts);        
    // }, [displayContracts]);

    useEffect(() => {
        if (!contractsContext.selectedContract) clearUi();
    }, [contractsContext.selectedProject]);

    useEffect(() => {
        setContracts(contractsContext.selectedProject?.reports ?? []);
        setDisplayRowsStructure(getRowListStructure());
    }, [contractsContext.selectedProject?.reports]);

    useEffect(() => {
        updateStatusFilterNumbers(contracts);
    }, [contracts]);

    useEffect(() => {
        formatDisplayContracts(contracts);
    }, [contracts, selectedContractTypes, selectedStatus, sorting]);



    function handleUpload(): void {
        setIsUploadOpen(true);
    }

    function handleEditProject(): void {
        setIsProjectEditOpen(true);
    }

    function handleStatusClick(status: ExtractionStatus | MatchingStatus): void {
        setSelectedStatus(current => current === status ? undefined : status);
    }

    function handleFilterPillClick(type: CONTRACT_TYPES): void {
        setSelectedContractTypes((current) => {
            return current.includes(type)
                ? current.filter((pill) => pill !== type)
                : [...current, type];
        });
    }

    function handleMenuClick(contract: ContractObject, action: MenuActions): void {
        switch (action) {
            case MenuActions.View: handleContractClick(contract); break;
            case MenuActions.Compare: handleContractClick(contract, true); break;
            case MenuActions.Delete: handleContractDeleteClick(contract); break;
            default: break;
        }
    }

    function handleContractClick(contract: ContractObject, compare?: boolean): void {
        contractsContext.setSelectedContract(contract);
        if (compare) {
            contractsContext.setSecondarySelectedContract(contract.content_type);
        }
    }

    function handleContractDeleteClick(contract: ContractObject): void {
        setContractForDeletion(contract);
        setIsDeleteContractDialogOpen(true);
    }

    function handleConfirmedContractDeletion(): void {
        if (!contractsContext.selectedProject || !contractForDeletion) return;
        void contractsContext.deleteContract(contractsContext.selectedProject.id.toString(), contractForDeletion.id.toString());
        setContractForDeletion(undefined);
        setIsDeleteContractDialogOpen(false);
    }
    function handleCancelledContractDeletion(): void {
        setContractForDeletion(undefined);
        setIsDeleteContractDialogOpen(false);
    }

    function handleSort(field: keyof ContractObject): void {
        let sortingResult: SortingObject<ContractObject> = {};
        if (sorting.field !== field) sortingResult = { field };
        if (sorting.field === field) {
            if (sorting.isDesc) sortingResult = { field: undefined };
            else sortingResult = { field, isDesc: true };
        }
        setSorting(sortingResult);
    }


    function clearUi(): void {
        setSelectedContractTypes([]);
        setSelectedStatus(undefined);
    }


    function formatDisplayContracts(passedContracts: ContractObject[]): void {
        const clonedContracts = structuredClone(passedContracts);
        const verifiedContracts = getVerifiedContracts(clonedContracts);
        const filterPillContracts = getFilterPillContracts(verifiedContracts, selectedContractTypes);
        const filterStatusContracts = getFilterStatusContracts(filterPillContracts, selectedStatus);
        const sortContracts = getSortedContracts(filterStatusContracts);
        setDisplayContracts(sortContracts);
    }

    function getVerifiedContracts(allContracts: ContractObject[]): ContractObject[] {
        const verifiedContracts: ContractObject[] = allContracts.map(contract => {
            const quickList: VerificationQuickList = {
                vsow: getQuickList(contract, CONTRACT_TYPES.VSOW),
                csow: getQuickList(contract, CONTRACT_TYPES.CSOW),
                po: getQuickList(contract, CONTRACT_TYPES.PURCHASE_ORDER),
                invoice: getQuickList(contract, CONTRACT_TYPES.INVOICE),
            }
            return { ...contract, verificationQuickList: quickList }
        });
        return verifiedContracts;

        function getQuickList(contract: ContractObject, type: CONTRACT_TYPES): VerificationQuickListItem {
            return {
                irrelevant: contract.content_type === type,
                verified: contract.verification?.[type]?.every(item => item.verification_status),
                unverifiedItems: contract.verification?.[type]?.filter(item => !item.verification_status).map(item => {
                    const relevantContract = contractsContext.getContractById(item.file_id ?? "");
                    return {
                        id: item.file_id,
                        ref: item.file_ref,
                        label: relevantContract?.label ?? undefined,
                        fileName: relevantContract?.filename,
                    };
                }) ?? [],
            }
        }
    }

    function getFilterPillContracts(allContracts: ContractObject[], types: CONTRACT_TYPES[]): ContractObject[] {
        if (types.length === 0) return allContracts;
        return allContracts.filter(contract => types.includes(contract.content_type));
    }

    function getFilterStatusContracts(allContracts: ContractObject[], status?: ExtractionStatus | MatchingStatus): ContractObject[] {
        if (!status) return allContracts;
        switch (status) {
            case ExtractionStatus.Uploading: return allContracts.filter(item => item.status === ContractStatus.Uploading);
            case ExtractionStatus.Extracting: return allContracts.filter(item => item.status === ContractStatus.Extracting);
            case ExtractionStatus.Failed: return allContracts.filter(item => item.status === ContractStatus.ExtractionFailed);
            case ExtractionStatus.Complete: return allContracts.filter(item => item.status !== ContractStatus.Uploading && item.status !== ContractStatus.Extracting && item.status !== ContractStatus.ExtractionFailed);
            case MatchingStatus.Found: return allContracts.filter(item => item.verification?.verification_status === true);
            case MatchingStatus.Failed: return allContracts.filter(item => item.verification?.verification_status === false);
            default: return allContracts;
        }
    }

    function getSortedContracts(allContracts: ContractObject[]): ContractObject[] {
        if (!sorting.field) return allContracts;

        allContracts.sort((a, b) => {
            if (sorting.field === "label") {
                return (a.label ?? a.filename).localeCompare(b.label ?? b.filename);
            } else if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field])) {
                return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
            } else if (sorting.field && typeof a[sorting.field] === "number" && typeof b[sorting.field] === "number") {
                return (a[sorting.field] as number) - (b[sorting.field] as number);
            }
            return 0;
        });
        if (sorting.isDesc) { allContracts.reverse(); }

        return allContracts;
    }



    function updateStatusFilterNumbers(passedContracts: ContractObject[]): void {
        const numbers = cleanFilterNumbers;
        numbers.uploading = passedContracts.filter(item => item.status === ContractStatus.Uploading).length;
        numbers.extracting = passedContracts.filter(item => item.status === ContractStatus.Extracting).length;
        numbers.failed = passedContracts.filter(item => item.status === ContractStatus.ExtractionFailed).length;
        numbers.complete = passedContracts.filter(item => item.status !== ContractStatus.Uploading && item.status !== ContractStatus.Extracting && item.status !== ContractStatus.ExtractionFailed).length;
        numbers.matched = passedContracts.filter(item => item.verification?.verification_status === true).length;
        numbers.unmatched = passedContracts.filter(item => item.verification?.verification_status === false).length;
        setStatusFilterNumbers(numbers);
    }


    function getRowListStructure(): RowStructure<ContractObject>[] {
        const structure: RowStructure<ContractObject>[] = [];

        structure.push({ header: "", field: "status", align: "center", formattingFunction: structureStatus });
        structure.push({ header: "Size", field: "filesize", isSortable: true, align: "center", formattingFunction: structureFileSize, });
        // structure.push({ header: "Number", field: "contract_number", isSortable: true, formattingFunction: structureContractNumber, });
        structure.push({ header: "Title", field: "label", isSortable: true, formattingFunction: structureName, });
        structure.push({ header: "Type", field: "content_type", isSortable: true, formattingFunction: structureType });

        structure.push({ header: "VSOW", field: "1", align: "center", formattingFunction: structureVerificationVsow });
        structure.push({ header: "CSOW", field: "2", align: "center", formattingFunction: structureVerificationCsow });
        structure.push({ header: "PO", field: "3", align: "center", formattingFunction: structureVerificationPo });
        structure.push({ header: "Invoice", field: "4", align: "center", formattingFunction: structureVerificationInvoice });

        return structure;
    }


    // Table formatting functions

    function structureStatus(listItem: ContractObject): React.ReactNode {
        switch (listItem.status) {
            case ContractStatus.Uploading: return <span title="Uploading"><StatusIcon status={ExtractionStatus.Uploading} /></span>
            case ContractStatus.Extracting: return <span title="Extracting information"><StatusIcon status={ExtractionStatus.Extracting} /></span>
            case ContractStatus.ExtractionFailed: return <span title="Process failed, please reupload"><StatusIcon status={ExtractionStatus.Failed} /></span>
            default: return <span title="This file has been processed successfully"><StatusIcon status={ExtractionStatus.Complete} /></span>
        }
    }
    function structureFileSize(listItem: ContractObject): string {
        if (!listItem.filesize) return "";
        return formatBytes(listItem.filesize);
    }
    // function structureContractNumber(listItem: ContractObject): React.ReactNode {
    //     switch (listItem.content_type) {
    //         case CONTRACT_TYPES.INVOICE: return listItem.highlight?.invoice_number ?? "";
    //         case CONTRACT_TYPES.PURCHASE_ORDER: return listItem.po_number ?? "";
    //         default: return listItem.highlight?.contract_number ?? "";
    //     }
    // }
    function structureName(listItem: ContractObject): React.ReactNode {
        return (
            <CommonButton
                className="contract-name"
                title={listItem.filename}
                noBackground
                onClick={() => { handleContractClick(listItem); }}
            >
                <span>
                    {listItem.label && listItem.label.length > 0 ? listItem.label : listItem.filename}
                </span>
            </CommonButton>
        );
    }
    function structureType(listItem: ContractObject): React.ReactNode {
        return (
            <div
                className={[
                    "contract-type",
                    listItem.content_type
                ].filter(Boolean).join(" ")}
            >
                {listItem.content_type === CONTRACT_TYPES.INVOICE ? listItem.content_type : listItem.content_type.toUpperCase()}
            </div>
        );
    }
    function structureVerificationVsow(listItem: ContractObject, index: number): React.ReactNode { return structureVerification(listItem, index, CONTRACT_TYPES.VSOW); }
    function structureVerificationCsow(listItem: ContractObject, index: number): React.ReactNode { return structureVerification(listItem, index, CONTRACT_TYPES.CSOW); }
    function structureVerificationPo(listItem: ContractObject, index: number): React.ReactNode { return structureVerification(listItem, index, CONTRACT_TYPES.PURCHASE_ORDER); }
    function structureVerificationInvoice(listItem: ContractObject, index: number): React.ReactNode { return structureVerification(listItem, index, CONTRACT_TYPES.INVOICE); }
    function structureVerification(listItem: ContractObject, index: number, type: CONTRACT_TYPES): React.ReactNode {
        const item = listItem.verificationQuickList?.[type];
        if (!item) return "";
        return (
            <div className="contract-verification">
                {item.irrelevant ? <span className="irrelevant">—</span> :
                    listItem.status === ContractStatus.Extracting ? <span className="pending" title="This file is still being processed"><ElevaiteIcons.SVGInstanceProgress /></span> :
                        listItem.status === ContractStatus.ExtractionFailed ? <span className="failed" title="This file failed to extract"><ElevaiteIcons.SVGXmark /></span> :
                            item.verified ? 
                                <MatchButton contract={listItem} />
                            :
                                <MismatchButton contract={listItem} items={item.unverifiedItems} index={index} listLength={displayContracts.length} />
                }
            </div>
        );
    }

    ///////////////////////




    return (
        <div className={["contracts-list-v2-container", contractsContext.selectedProject ? undefined : "empty"].filter(Boolean).join(" ")}>


            <div className="contracts-list-v2-title-row">
                <span className="title">
                    {contractsContext.selectedProject?.name}
                </span>
                {!contractsContext.selectedProject ? undefined :
                    <div className="title-controls-container">
                        <CommonButton
                            className="edit-project-button"
                            onClick={handleEditProject}
                        >
                            Edit Project
                        </CommonButton>
                        <CommonButton
                            className="upload-button"
                            onClick={handleUpload}
                        >
                            Upload Files
                        </CommonButton>
                    </div>
                }
            </div>

            <div className="contracts-list-v2-status-row">
                <ContractListStatusBlock amount={statusFilterNumbers.uploading} title={ExtractionStatus.Uploading} selectedStatus={selectedStatus} onClick={handleStatusClick} />
                <ContractListStatusBlock amount={statusFilterNumbers.extracting} title={ExtractionStatus.Extracting} selectedStatus={selectedStatus} onClick={handleStatusClick} />
                <ContractListStatusBlock amount={statusFilterNumbers.failed} title={ExtractionStatus.Failed} selectedStatus={selectedStatus} onClick={handleStatusClick} />
                <ContractListStatusBlock amount={statusFilterNumbers.complete} title={ExtractionStatus.Complete} selectedStatus={selectedStatus} onClick={handleStatusClick} />
                <div className="status-separator" />
                <ContractListStatusBlock amount={statusFilterNumbers.matched} title={MatchingStatus.Found} selectedStatus={selectedStatus} onClick={handleStatusClick} />
                <ContractListStatusBlock amount={statusFilterNumbers.unmatched} title={MatchingStatus.Failed} selectedStatus={selectedStatus} onClick={handleStatusClick} />
            </div>

            <div className="contracts-list-v2-filter-pills-row">
                <ContractListFilterPill type={CONTRACT_TYPES.VSOW} selectedPills={selectedContractTypes} onClick={handleFilterPillClick} />
                <ContractListFilterPill type={CONTRACT_TYPES.CSOW} selectedPills={selectedContractTypes} onClick={handleFilterPillClick} />
                <ContractListFilterPill type={CONTRACT_TYPES.PURCHASE_ORDER} selectedPills={selectedContractTypes} onClick={handleFilterPillClick} />
                <ContractListFilterPill type={CONTRACT_TYPES.INVOICE} selectedPills={selectedContractTypes} onClick={handleFilterPillClick} />
                <div className="filter-pills-controls-container">
                    {/* <CommonButton className="edit-button">
                        Edit
                    </CommonButton> */}
                </div>
            </div>



            <div className="contracts-list-v2-table-container">

                {!contractsContext.selectedProject ?
                    <div className="no-project">
                        <span>No selected project</span>
                        <span>Select one from the list to the left</span>
                    </div>
                    :
                    <div className="contracts-list-v2-table-contents">
                        <ListRow<ContractObject>
                            isHeader
                            structure={displayRowsStructure}
                            menu={contractsListMenu}
                            onSort={handleSort}
                            sorting={sorting}
                        />
                        {contractsContext.loading.projectReports[contractsContext.selectedProject.id] ?
                            <div className="table-span empty">
                                <ElevaiteIcons.SVGSpinner />
                                <span>Loading...</span>
                            </div>
                            : displayContracts.length === 0 ?
                                <div className="table-span empty">
                                    There are no entries.
                                </div>

                                :

                                displayContracts.map((contract, index) =>
                                    <ListRow<ContractObject>
                                        key={contract.id}
                                        rowItem={contract}
                                        index={index}
                                        structure={displayRowsStructure}
                                        menu={contractsListMenu}
                                        menuToTop={displayContracts.length > 4 && index > (displayContracts.length - 4)}
                                    />
                                )}
                    </div>
                }

            </div>


            {!isUploadOpen ? undefined :
                <CommonModal
                    onClose={() => { setIsUploadOpen(false); }}
                >
                    <ContractUpload
                        selectedType={selectedContractTypes.length >= 1 ? selectedContractTypes[0] : undefined}
                        onClose={() => { setIsUploadOpen(false); }}
                    />
                </CommonModal>
            }

            {!isProjectEditOpen || !contractsContext.selectedProject ? undefined :
                <CommonModal
                    onClose={() => { setIsProjectEditOpen(false); }}
                >
                    <AddProject
                        onClose={() => { setIsProjectEditOpen(false); }}
                        editingProjectId={contractsContext.selectedProject.id.toString()}
                    />
                </CommonModal>
            }

            {!isDeleteContractDialogOpen || !contractForDeletion ? undefined :
                <CommonDialog
                    title="Delete Report?"
                    onConfirm={handleConfirmedContractDeletion}
                    confirmLabel="Delete"
                    onCancel={handleCancelledContractDeletion}
                    dangerSubmit
                >
                    <div className="delete-dialog-contents">
                        <span>{`Are you sure you want to delete the file "${contractForDeletion.label ?? contractForDeletion.filename}"?`}</span>
                        <span>This action can&apos;t be undone.</span>
                    </div>
                </CommonDialog>
            }


        </div>
    );
}




// SUB-COMPONENTS
///////////////////



interface StatusIconProps {
    status: ExtractionStatus | MatchingStatus;
}

function StatusIcon(props: StatusIconProps): JSX.Element {
    switch (props.status) {
        case ExtractionStatus.Uploading: return <div className="status-icon-container"><ElevaiteIcons.SVGUpload /></div>
        case ExtractionStatus.Extracting: return <div className="status-icon-container highlight"><ElevaiteIcons.SVGInstanceProgress /></div>
        case ExtractionStatus.Failed: return <div className="status-icon-container danger"><ElevaiteIcons.SVGXmark /></div>
        case ExtractionStatus.Complete: return <div className="status-icon-container blue"><ElevaiteIcons.SVGCheckmark /></div>
        case MatchingStatus.Found: return <div className="status-icon-container success"><ElevaiteIcons.SVGCheckmark /></div>
        case MatchingStatus.Failed: return <div className="status-icon-container"><ElevaiteIcons.SVGQuestionMark /></div>
    }
}


interface ContractListStatusBlockProps {
    amount: number;
    title: ExtractionStatus | MatchingStatus;
    selectedStatus: ExtractionStatus | MatchingStatus | undefined;
    onClick: (status: ExtractionStatus | MatchingStatus) => void;
}

function ContractListStatusBlock(props: ContractListStatusBlockProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.title);
    }

    return (
        <CommonButton
            className={[
                "contract-list-status-block-container",
                props.title === props.selectedStatus ? "active" : undefined,
            ].filter(Boolean).join(" ")}
            onClick={handleClick}
            disabled={props.amount === 0}
        >
            <div className="amount">{props.amount.toString().padStart(2, "0")}</div>
            <StatusIcon status={props.title} />
            <div className="title">{props.title}</div>
        </CommonButton>
    );
}


interface ContractListFilterPillProps {
    type: CONTRACT_TYPES;
    selectedPills: CONTRACT_TYPES[];
    onClick: (selectedTab: CONTRACT_TYPES) => void;
}

function ContractListFilterPill(props: ContractListFilterPillProps): JSX.Element {
    const [label, setLabel] = useState("");
    const [isSelected, setIsSelected] = useState(false);

    useEffect(() => {
        switch (props.type) {
            case CONTRACT_TYPES.VSOW: setLabel(CONTRACTS_TABS.SUPPLIER_CONTRACTS.toUpperCase()); break;
            case CONTRACT_TYPES.CSOW: setLabel(CONTRACTS_TABS.CUSTOMER_CONTRACTS.toUpperCase()); break;
            case CONTRACT_TYPES.PURCHASE_ORDER: setLabel(CONTRACTS_TABS.SUPPLIER_POS.toUpperCase()); break;
            case CONTRACT_TYPES.INVOICE: setLabel(CONTRACTS_TABS.SUPPLIER_INVOICES.toUpperCase()); break;
        }
    }, [props.type]);

    useEffect(() => {
        setIsSelected(props.selectedPills.includes(props.type));
    }, [props.type, props.selectedPills]);

    function handleClick(): void {
        props.onClick(props.type);
    }

    return (
        <CommonButton
            className={["filter-pill-container", isSelected ? "active" : undefined].filter(Boolean).join(" ")}
            onClick={handleClick}
            noBackground={!isSelected}
        >
            {label}
        </CommonButton>
    );
}




interface MatchButtonProps {
    contract: ContractObject;
}

function MatchButton(props: MatchButtonProps): JSX.Element {
    const contractsContext = useContracts();
    
    function handleMatchClick(): void {
        if (!props.contract.verification) return;
        const relevantContracts = Object.values(props.contract.verification)
            .filter((value): value is ContractObjectVerificationItem[] => Array.isArray(value)).flat();

        if (relevantContracts[0]) {            
            contractsContext.setSecondarySelectedContractById(relevantContracts[0].file_id);
            contractsContext.setSelectedContract(props.contract);
        }
    }


    return (
        <CommonButton
            className="verified"
            title="This cross-section has no issues"
            onClick={handleMatchClick}
        >
            <ElevaiteIcons.SVGCheckmark />
        </CommonButton>
    );
}




interface MismatchButtonProps {
    contract: ContractObject;
    items: UnverifiedItem[];
    index?: number;
    listLength?: number;
}

function MismatchButton(props: MismatchButtonProps): JSX.Element {
    const contractsContext = useContracts();
    if (props.items.length === 0) return <span className="failed"><ElevaiteIcons.SVGXmark /></span>


    function handleMismatchMenuClick(clickedItem: UnverifiedItem): void {
        if (!clickedItem.id) return;
        contractsContext.setSecondarySelectedContractById(clickedItem.id);
        contractsContext.setSelectedContract(props.contract);
    }

    if (props.items.length === 1)
        return (
            <CommonButton
                // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition, no-constant-binary-expression -- TODO: Take a look at this
                title={`This cross-section has one issue, with file:\n${props.items[0].label ?? props.items[0].fileName ?? "Unknown File" ?? "Unknown"}`}
                onClick={() => { handleMismatchMenuClick(props.items[0]); }}
            >
                <ElevaiteIcons.SVGQuestionMark />
            </CommonButton>
        );

    //--------------------

    const mismatchMenu: CommonMenuItem<UnverifiedItem[]>[] =
        props.items.map(item => {
            return {
                label: item.label ?? item.fileName ?? "Unknown File",
                onClick: () => { handleMismatchMenuClick(item); },
                tooltip: item.fileName,
            }}
        );

    return (
        <CommonMenu
            menu={mismatchMenu}
            menuIcon={<ElevaiteIcons.SVGQuestionMark />}
            tooltip={`This cross-section has ${props.items.length.toString()} issues`}
            labelWidth="long"
            left
            top={Boolean(props.listLength && props.index && props.listLength > 4 && props.index > (props.listLength - 4))}
        />
    );
}
