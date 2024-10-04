import { CommonButton, CommonModal, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractObjectVerificationLineItem, type ContractObjectVerificationLineItemVerification } from "../../../../lib/interfaces";
import "./VerificationLineItems.scss";




interface TableDataItem {
    value: (string | number | null | undefined)[];
    verification: ContractObjectVerificationLineItemVerification;
}



interface VerificationLineItemsProps {
    lineItems?: ContractObjectVerificationLineItem[];
    fullScreen?: boolean;
    onFullScreenClose?: () => void;
}

export function VerificationLineItems(props: VerificationLineItemsProps): JSX.Element {
    const headers = ["Ver.", "Amount", "Quantity", "Unit Price", "Product Code", "Part Number", "Need by", "Description"];
    const [displayHeaders, setDisplayHeaders] = useState<string[]>(headers);
    const [tableData, setTableData] = useState<TableDataItem[]>();


    useEffect(() => {
        console.log("Table Data:", tableData);        
    }, [tableData]);

    useEffect(() => {
        if (props.lineItems) {
            const data = getTableData(props.lineItems);
            setTableData(data.table);
            setDisplayHeaders(data.headers);
        }            
    }, [props.lineItems]);


    function handleClose(): void {
        if (props.onFullScreenClose) props.onFullScreenClose();
    }


    function getTableData(lineItems: ContractObjectVerificationLineItem[]): { table: TableDataItem[], headers: string[]} {
        const isColumnEmpty = Array(headers.length).fill(true);

        lineItems.forEach((item) => {
            const values = [
                true,
                item.amount,
                item.quantity,
                item.unit_price,
                item.product_code,
                item.part_number,
                item.need_by_date,
                item.description,
            ];    
            values.forEach((value, i) => {
                if (value !== null && value !== undefined && value !== "") {
                    isColumnEmpty[i] = false;
                }
            });
        });
        
        const filteredHeaders = headers.filter((_, index) => !isColumnEmpty[index]);

        const data = lineItems.map((item, index) => {
            const values = [
                index + 1,
                item.amount,
                item.quantity,
                item.unit_price,
                item.product_code,
                item.part_number,
                item.need_by_date,
                item.description,
            ];
            const filteredValues = values.filter((_, i) => !isColumnEmpty[i]);
    
            return {
                value: filteredValues,
                verification: item.verification,
            };
        });


        return { table: data, headers: filteredHeaders };
    };


    return (
        <div className="verification-line-items-container">
            <div className="table-scroller">
                {!tableData ? 
                    <div>No tabular data available</div>
                :
                    <VerificationTableStructure
                        headers={displayHeaders}
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
                            headers={displayHeaders}
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
                                        value={cell !== null && cell !== undefined ? cell.toString() : ""}
                                        title={cell !== null && cell !== undefined && cell.toString().length > 30 ? cell.toString() : ""}
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
