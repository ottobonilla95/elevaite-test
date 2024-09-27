import { CommonButton, CommonDialog, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractExtractionDictionary } from "../../../lib/interfaces";
import "./PdfExtraction.scss";
import { ExtractedBit } from "./extractionComponents/ExtractedBit";
import { ExtractedTableBit } from "./extractionComponents/ExtractedTableBit";
import { PdfExtractionEmphasis } from "./extractionComponents/PdfExtractionEmphasis";
import { PdfExtractionVerification } from "./extractionComponents/PdfExtractionVerification";



enum ExtractionTabs {
    EXTRACTION = "Extraction",
    VERIFICATION = "Verification",
};


interface PdfExtractionProps {
    handleExpansion: () => void;
    isExpanded: boolean;
}

export function PdfExtraction(props: PdfExtractionProps): JSX.Element {
    const contractsContext = useContracts();
    const [extractedBits, setExtractedBits] = useState<JSX.Element[]>([]);
    const [isApprovalConfirmationOpen, setIsApprovalConfirmationOpen] = useState(false);
    const [selectedTab, setSelectedTab] = useState<ExtractionTabs>(ExtractionTabs.EXTRACTION);


    useEffect(() => {
        if (contractsContext.selectedContract?.response) {
            setExtractedBits(getExtractedBits(contractsContext.selectedContract.response));
        } else setExtractedBits([]);
        if (!contractsContext.selectedContract?.verification) setSelectedTab(ExtractionTabs.EXTRACTION);
    }, [contractsContext.selectedContract, contractsContext.selectedContract?.response]);


    function handleBitChange(pageKey: string, itemKey: string, newValue: string): void {
        const pagePattern = /^page_\d+$/;
        if (!pagePattern.test(pageKey)) return;
        // contractsContext.changeSelectedContractBit(pageKey as `page_${number}`, itemKey, newValue);
    }

    function handleTableBitChange(pageKey: string, tableKey: string, newTableData: Record<string, string>[]): void {
        const pagePattern = /^page_\d+$/;
        if (!pagePattern.test(pageKey)) return;
        // contractsContext.changeSelectedContractTableBit(pageKey as `page_${number}`, tableKey, newTableData);
    }

    function handleManualApproval(): void {
        setIsApprovalConfirmationOpen(true);
    }

    function handleExpansion(): void {
        props.handleExpansion();
    }

    function confimedApproval(): void {        
        console.log("Handling manual approval of", contractsContext.selectedContract?.label ?? contractsContext.selectedContract?.filename);
        setIsApprovalConfirmationOpen(false);
    }



    function getExtractedBits(extractedData: ContractExtractionDictionary): JSX.Element[] {
        const bits: JSX.Element[] = [];
        const lineItems: Record<string, string>[] = [];
      
        Object.entries(extractedData).forEach(([pageKey, page]) => {
            
            Object.entries(page).forEach(([label, value]) => {
                if (typeof value === 'string') {
                    bits.push(<ExtractedBit
                                key={pageKey + label}
                                label={label}
                                value={value}
                                onChange={(changeLabel, changeText) => { handleBitChange(pageKey, changeLabel, changeText); }}
                            />);
                } else if (Array.isArray(value)) {
                    bits.push(<ExtractedBit
                        key={pageKey + label}
                        label={label}
                        value={`- ${value.join("\n- ")}`}
                        disabled
                    />);
                // TODO: Handle non-string values (recursion of record type, OR pester the model team to be consistent)
                } else if (label.startsWith("Line Item")) {
                    lineItems.push(value as Record<string, string>);
                } else if (typeof value === "string") { // Dictionary keys that don't start with "Line Item"
                    bits.push(<ExtractedTableBit
                                key={pageKey + label}
                                label={label}
                                data={[value]}
                                onTableChange={(changeLabel, changeText) => { handleTableBitChange(pageKey, changeLabel, changeText); }}
                                hideNumber
                            />);
                }
          });
        });

        if (lineItems.length > 0)
            bits.unshift(<ExtractedTableBit
                            key="line_items"
                            label="Line Items"
                            data={lineItems}
                        />);
      
        return bits;
      }


    return (
        <div className="pdf-extraction-container">

            <div className="pdf-extraction-header">
                <div className="pdf-extraction-controls">
                    <CommonButton
                        className={["expansion-arrow", props.isExpanded ? "expanded" : undefined].filter(Boolean).join(" ")}
                        onClick={handleExpansion}
                        noBackground
                        title={props.isExpanded ? "Restore views" : "Maximize Extraction / Verification view"}
                    >
                        <ElevaiteIcons.SVGSideArrow />
                    </CommonButton>
                    <div className="tabs-container">
                        <CommonButton
                            className={[
                                "tab-button",
                                selectedTab === ExtractionTabs.EXTRACTION ? "active" : undefined,
                            ].filter(Boolean).join(" ")}                        
                            onClick={() => { setSelectedTab(ExtractionTabs.EXTRACTION) }}
                        >
                            {ExtractionTabs.EXTRACTION}
                        </CommonButton>
                        {!contractsContext.selectedContract?.verification ? undefined : 
                            <CommonButton
                                className={[
                                    "tab-button",
                                    selectedTab === ExtractionTabs.VERIFICATION ? "active" : undefined,
                                ].filter(Boolean).join(" ")}                        
                                onClick={() => { setSelectedTab(ExtractionTabs.VERIFICATION) }}
                            >
                                {ExtractionTabs.VERIFICATION}
                            </CommonButton>
                        }
                    </div>
                </div>
                {contractsContext.selectedContract?.content_type !== CONTRACT_TYPES.INVOICE ? undefined :
                 contractsContext.selectedContract.verification?.verification_status === true ? 
                    <div className="approved-label">
                        <ElevaiteIcons.SVGCheckmark/>
                        <span>Approved</span>
                    </div>
                :
                    <CommonButton
                        onClick={handleManualApproval}
                        // disabled
                    >
                        Approve
                    </CommonButton>
                }
            </div>

            <div className="pdf-extraction-scroller">
                <div className="pdf-extraction-contents">
                    {selectedTab === ExtractionTabs.EXTRACTION ? 
                    <>
                        <PdfExtractionEmphasis />
                        {extractedBits.length === 0 ? 
                            <div className="empty-bits">
                                {contractsContext.selectedContract?.status === CONTRACT_STATUS.PROCESSING ? 
                                    <><ElevaiteIcons.SVGSpinner/><span>Extraction in progress...</span></>
                                    : <span>No extracted data</span>
                                }                            
                            </div>
                            :
                            extractedBits
                        }
                    </>
                    :
                        <PdfExtractionVerification />
                    }
                </div>
            </div>

            {!isApprovalConfirmationOpen || !contractsContext.selectedContract ? undefined :
                <CommonDialog
                    title={`Approve ${contractsContext.selectedContract.content_type}?`}

                    onConfirm={confimedApproval}
                    disableConfirm
                    onCancel={() => { setIsApprovalConfirmationOpen(false); }}
                >
                    <div className="invoice-approval-dialog-contents">
                        <div>
                            You will manually approve {contractsContext.selectedContract.content_type} {contractsContext.selectedContract.label ?? contractsContext.selectedContract.filename}
                        </div>
                        <div className="warning">This functionality has not been implemented yet.</div>
                    </div>
                </CommonDialog>
            }

        </div>
    );
}




