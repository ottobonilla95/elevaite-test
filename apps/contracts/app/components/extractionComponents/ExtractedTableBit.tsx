import { CommonButton, CommonModal, ElevaiteIcons, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { useEffect, useState } from "react";
import "./ExtractedTableBit.scss";


const TABLE_NUMBER_LABEL = "No.";

interface ExtractedTableBitProps {
    label: string;
    data: Record<string, string>[];
    onTableChange?: (label: string, newData: Record<string, string>[]) => void;
    hideLabel?: boolean;
    hideNumber?: boolean;
}

export function ExtractedTableBit(props: ExtractedTableBitProps): JSX.Element {
    const [tableData, setTableData] = useState(props.data);
    const [headers, setHeaders] = useState<string[]>([]);
    const [isFullScreenOpen, setIsFullScreenOpen] = useState(false);

    useEffect(() => {
        setTableData(props.data);
    }, [props.data]);

    useEffect(() => {
        if (tableData.length === 0) {
            setHeaders([]);
            return;
        }
        setHeaders(props.hideNumber ? Object.keys(tableData[0]) : [TABLE_NUMBER_LABEL, ...Object.keys(tableData[0])]);
    }, [tableData]);


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
        if (props.onTableChange) props.onTableChange(props.label, updatedTableData);
    }


    return (
        <div className="extracted-table-container">
            
            {props.hideLabel ? undefined :
                <div className="top">
                    <div className="label">{props.label}</div>
                    {props.data.length === 0 ? undefined :
                        <CommonButton
                            onClick={() => { setIsFullScreenOpen(true); }}
                            noBackground
                        >
                            <ElevaiteIcons.SVGZoom/>
                        </CommonButton>
                    }
                </div>
            }

            <div className="table-scroller">
                {props.data.length === 0 ? 
                    <div>No tabular data available</div>
                :
                    <TableStructure
                        headers={headers}
                        data={props.data}
                        onChange={handleChange}
                    />                    
                }
            </div>


            {!isFullScreenOpen ? undefined :
                <CommonModal
                    className="full-screen-extracted-table-modal"
                    onClose={() => { setIsFullScreenOpen(false); }}
                >                 
                    <div className="close-button-area">
                        <CommonButton
                            onClick={() => { setIsFullScreenOpen(false); }}
                            noBackground
                        >
                            <ElevaiteIcons.SVGXmark />
                        </CommonButton>
                    </div>   
                    <div className="table-scroller">
                        <TableStructure
                            headers={headers}
                            data={props.data}
                            onChange={handleChange}
                        />
                    </div>
                </CommonModal>
            }


        </div>
    );
}



interface TableStructureProps {
    headers: string[];    
    data: Record<string, string>[];
    onChange?: (rowIndex: number, columnKey: string, newValue: string) => void;
}


function TableStructure(props: TableStructureProps): JSX.Element {
    const [tableData, setTableData] = useState(props.data);

    useEffect(() => {
        setTableData(filterTableData(props.data, props.headers));
    }, [props.data, props.headers]);

    function handleChange(rowIndex: number, columnKey: string, newValue: string): void {
        if (props.onChange)
            props.onChange(rowIndex, columnKey, newValue);
    }

    // Removes rows with irrelevant data to our line items.
    function filterTableData(tableData: Record<string, string>[], headers: string[]): Record<string, string>[] {
        return tableData.filter(row => 
            headers.some(header => row.hasOwnProperty(header) && row[header] !== "")
        );
    }

    return (
        <table className="extracted-table">
            <thead>
                <tr>
                    {props.headers.map(header => (
                        <th key={header}>
                            {header}
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {tableData.map((row, rowIndex) => (
                    <tr key={row[0] + rowIndex.toString()}>
                        {props.headers.map(header => (
                            <td key={header}>
                                {header === TABLE_NUMBER_LABEL ? 
                                    <SimpleInput
                                        value={(rowIndex+1).toString()}
                                        autoSize
                                        disabled
                                    />
                                :                                    
                                    <SimpleInput
                                        value={row[header] ?? ""}
                                        onChange={(newValue) => { handleChange(rowIndex, header, newValue); }}
                                        title={row[header] && row[header].length > 30 ? row[header] : ""}
                                        autoSize
                                    />
                                }
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
