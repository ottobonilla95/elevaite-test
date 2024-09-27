import { CommonButton, CommonModal, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractObjectVerificationLineItem, type ContractObjectVerificationLineItemVerification } from "../../../../lib/interfaces";
import "./VerificationLineItems.scss";




interface TableDataItem {
    value: (string | number | null)[];
    verification: ContractObjectVerificationLineItemVerification;
}



interface VerificationLineItemsProps {
    lineItems?: ContractObjectVerificationLineItem[];
    fullScreen?: boolean;
    onFullScreenClose?: () => void;
}

export function VerificationLineItems(props: VerificationLineItemsProps): JSX.Element {
    const headers = ["Ver.", "Amount", "Quantity", "Unit Price", "Part Number", "Need by", "Description"];
    const [tableData, setTableData] = useState<TableDataItem[]>();


    useEffect(() => {
        if (props.lineItems)
            setTableData(getTableData(props.lineItems));
    }, [props.lineItems]);


    function handleClose(): void {
        if (props.onFullScreenClose) props.onFullScreenClose();
    }


    function getTableData(lineItems: ContractObjectVerificationLineItem[]): TableDataItem[] {
        return lineItems.map((item, index) => ({
            value: [
                index + 1, // "No." (Using id here for uniqueness)
                item.amount, // "Amount"
                item.quantity, // "Quantity"
                item.unit_price, // "Unit Price"
                item.part_number, // "Part Number"
                item.need_by_date, // "Need by"
                item.description, // "Description"
            ],
            verification: item.verification
        }));
    };


    return (
        <div className="verification-line-items-container">
            <div className="table-scroller">
                {!tableData ? 
                    <div>No tabular data available</div>
                :
                    <VerificationTableStructure
                        headers={headers}
                        data={tableData}
                    />                
                }
            </div>

            {!props.fullScreen || !tableData ? undefined :
                <CommonModal
                    className="full-screen-extracted-line-items-modal"
                    onClose={handleClose}
                >                 
                    <div className="close-button-area">
                        <CommonButton
                            onClick={handleClose}
                            noBackground
                        >
                            <ElevaiteIcons.SVGXmark />
                        </CommonButton>
                    </div>   
                    <div className="table-scroller">
                        <VerificationTableStructure
                            headers={headers}
                            data={tableData}
                        />
                    </div>
                </CommonModal>
            }
        </div>
    );
}




interface VerificationTableStructureProps {
    headers: string[];    
    data: TableDataItem[];
}


function VerificationTableStructure(props: VerificationTableStructureProps): JSX.Element {
    return (
        <table className="line-items-table">
            <thead>
                <tr>
                    {props.headers.map((header, headerIndex) => 
                        <th key={header} className={props.headers[headerIndex]}>
                            {header}
                        </th>
                    )}
                </tr>
            </thead>
            <tbody>
                {props.data.map((row, rowIndex) => (
                    <tr key={`line_${rowIndex.toString()}`}>
                        {row.value.map((cell, cellIndex) => 
                            <td
                                key={`column_${cellIndex.toString()}`}
                                className={props.headers[cellIndex]}
                            >
                                {cellIndex === 0 ? 
                                    <div
                                        className={["verification", row.verification.verification_status ? "verified" : undefined].filter(Boolean).join(" ")}
                                        title={
                                            `VSOW: ${row.verification.vsow ? "Verified" : "Failed"}\nPO: ${row.verification.po ? "Verified" : "Failed"}\nInvoice: ${row.verification.invoice ? "Verified" : "Failed"}\n`
                                        }
                                    >
                                        {/* <div>{cell !== null ? cell.toString() : ""}</div> */}
                                        {row.verification.verification_status ? <ElevaiteIcons.SVGCheckmark/> : <ElevaiteIcons.SVGXmark/>}
                                    </div>
                                :
                                    <SimpleInput
                                        value={cell !== null ? cell.toString() : ""}
                                        title={cell !== null && cell.toString().length > 30 ? cell.toString() : ""}
                                        autoSize
                                        disabled
                                    />
                                }
                            </td>
                        )}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
