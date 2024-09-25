import { ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractObjectVerificationLineItem, type ContractObjectVerificationLineItemVerification } from "../../../../lib/interfaces";
import "./VerificationLineItems.scss";




interface TableDataItem {
    value: (string | number)[];
    verification: ContractObjectVerificationLineItemVerification;
}



interface VerificationLineItemsProps {
    lineItems?: ContractObjectVerificationLineItem[];
}

export function VerificationLineItems(props: VerificationLineItemsProps): JSX.Element {
    const headers = ["No.", "Amount", "Quantity", "Unit Price", "Part Number", "Need by", "Description"];
    const [tableData, setTableData] = useState<TableDataItem[]>();


    useEffect(() => {
        if (props.lineItems)
            setTableData(getTableData(props.lineItems));
    }, [props.lineItems]);


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
                <table className="line-items-table">
                    <thead>
                        <tr>
                            {headers.map((header, headerIndex) => 
                                <th key={header} className={headers[headerIndex]}>
                                    {header}
                                </th>
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        {tableData.map((row, rowIndex) => (
                            <tr key={`line_${rowIndex.toString()}`}>
                                {row.value.map((cell, cellIndex) => 
                                    <td
                                        key={`column_${cellIndex.toString()}`}
                                        className={headers[cellIndex]}
                                    >
                                        {cellIndex === 0 ? 
                                            <div
                                                className={["verification", row.verification.verification_status ? "verified" : undefined].filter(Boolean).join(" ")}
                                                title={
                                                    `VSOW: ${row.verification.vsow ? "Verified" : "Failed"}\nPO: ${row.verification.po ? "Verified" : "Failed"}\nInvoice: ${row.verification.invoice ? "Verified" : "Failed"}\n`
                                                }
                                            >
                                                <div>{cell ? cell.toString() : ""}</div>
                                                {row.verification.verification_status ? <ElevaiteIcons.SVGCheckmark/> : <ElevaiteIcons.SVGXmark/>}
                                            </div>
                                        :
                                            <SimpleInput
                                                value={cell ? cell.toString() : ""}
                                                title={cell && cell.toString().length > 30 ? cell.toString() : ""}
                                                disabled
                                            />
                                        }
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
                }
            </div>
        </div>
    );
}

