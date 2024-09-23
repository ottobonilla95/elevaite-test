import { CommonButton, CommonDialog, ElevaiteIcons, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { CONTRACT_STATUS, type ContractExtractionDictionary } from "../../../lib/interfaces";
import "./PdfExtraction.scss";
import { PdfExtractionEmphasis } from "./PdfExtractionEmphasis";






export function PdfExtraction(): JSX.Element {
    const contractsContext = useContracts();
    const [extractedBits, setExtractedBits] = useState<JSX.Element[]>([]);
    const [isApprovalConfirmationOpen, setIsApprovalConfirmationOpen] = useState(false);


    useEffect(() => {
        if (contractsContext.selectedContract?.response) {
            setExtractedBits(getExtractedBits(contractsContext.selectedContract.response));
        } else setExtractedBits([]);
    }, [contractsContext.selectedContract?.response]);


    function handleBitChange(pageKey: string, itemKey: string, newValue: string): void {
        const pagePattern = /^page_\d+$/;
        if (!pagePattern.test(pageKey)) return;
        contractsContext.changeSelectedContractBit(pageKey as `page_${number}`, itemKey, newValue);
    }

    function handleTableBitChange(pageKey: string, tableKey: string, newTableData: Record<string, string>[]): void {
        const pagePattern = /^page_\d+$/;
        if (!pagePattern.test(pageKey)) return;
        contractsContext.changeSelectedContractTableBit(pageKey as `page_${number}`, tableKey, newTableData);
    }

    function handleManualApproval(): void {
        setIsApprovalConfirmationOpen(true);
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
            } else {
                lineItems.push(value);
                // bits.push(<ExtractedTableBit
                //             key={pageKey + label}
                //             label={label}
                //             data={value}
                //             onTableChange={(changeLabel, changeText) => { handleTableBitChange(pageKey, changeLabel, changeText); }}
                //         />);
            }
          });
        });

        if (lineItems.length > 0)
            bits.unshift(<ExtractedTableBit
                            key="line_items"
                            label="Line Items"
                            data={lineItems}
                            onTableChange={(changeLabel, changeText) => { console.log("change", changeLabel, changeText)}}
                        />);
      
        return bits;
      }


    return (
        <div className="pdf-extraction-container">

            <div className="pdf-extraction-header">
                <span>Extraction</span>
                {contractsContext.selectedContract?.verification?.verification_status === true ? 
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
                </div>
            </div>

            {!isApprovalConfirmationOpen || !contractsContext.selectedContract ? undefined :
                <CommonDialog
                    title={`Approve ${contractsContext.selectedContract.content_type}?`}

                    onConfirm={confimedApproval}
                    onCancel={() => { setIsApprovalConfirmationOpen(false); }}
                >
                    <span>
                        You will manually approve {contractsContext.selectedContract.content_type} {contractsContext.selectedContract.label ?? contractsContext.selectedContract.filename}
                    </span>
                </CommonDialog>
            }

        </div>
    );
}



interface ExtractedBitProps {
    label: string;
    value: string; 
    onChange: (label: string, newValue: string) => void;
}

function ExtractedBit(props: ExtractedBitProps): JSX.Element {
    const [manualValue, setManualValue] = useState(props.value);

    function handleChange(text :string): void {
        setManualValue(text);
        props.onChange(props.label, text);
    }

    return (
        <div className="extracted-bit-container">
            <div className="top">
                <div className="label">{props.label}</div>
                {/* <div className="date"></div> */}
            </div>
            {manualValue.length > 70 ? 
                <SimpleTextarea
                    value={manualValue}
                    onChange={handleChange}
                    useCommonStyling
                    placeholder={!props.value ? "Value not found. Insert manually" : ""}
                    rows={Math.min(Math.ceil(manualValue.length / 70), 5)}
                    // title={manualValue.length > 30 ? manualValue: ""}
                />
            :
                <SimpleInput
                    value={manualValue}
                    onChange={handleChange}
                    useCommonStyling
                    placeholder={!props.value ? "Value not found. Insert manually" : ""}
                />
            }
        </div>
    );
}


interface ExtractedTableBitProps {
    label: string;
    data: Record<string, string>[];
    onTableChange: (label: string, newData: Record<string, string>[]) => void;
}

function ExtractedTableBit(props: ExtractedTableBitProps): JSX.Element {
    const TABLE_NUMBER_LABEL = "No.";
    const [tableData, setTableData] = useState(props.data);
    const headers = tableData.length > 0 ? [TABLE_NUMBER_LABEL, ...Object.keys(tableData[0])] : [];


    function handleChange(rowIndex: number, columnKey: string, newValue: string): void {
        const updatedTableData = tableData.map((row, index) => {
            if (index === rowIndex) {
              return {
                ...row,
                [columnKey]: newValue
              };
            }
            return row;
          });
      
        setTableData(updatedTableData);
        props.onTableChange(props.label, updatedTableData);
    }


    return (
        <div className="extracted-table-container">
            
            <div className="top">
                <div className="label">{props.label}</div>
            </div>

            <div className="table-scroller">
                {props.data.length === 0 ? 
                    <div>No tabular data available</div>
                :
                    <table className="extracted-table">
                        <thead>
                            <tr>
                                {headers.map(header => (
                                    <th key={header}>
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {props.data.map((row, rowIndex) => (
                                <tr key={row[0] + rowIndex.toString()}>
                                    {headers.map(header => (
                                        <td key={header}>
                                            {header === TABLE_NUMBER_LABEL ? 
                                                <SimpleInput
                                                    value={(rowIndex+1).toString()}
                                                    disabled
                                                />
                                            :
                                                <SimpleInput
                                                    value={row[header]}
                                                    onChange={(newValue) => { handleChange(rowIndex, header, newValue); }}
                                                    title={row[header].length > 30 ? row[header]: ""}
                                                />
                                            }
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                }
            </div>
        </div>
    );
}



