import { SimpleInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import "./ExtractedTableBit.scss";


interface ExtractedTableBitProps {
    label: string;
    data: Record<string, string>[];
    onTableChange?: (label: string, newData: Record<string, string>[]) => void;
    hideLabel?: boolean;
}

export function ExtractedTableBit(props: ExtractedTableBitProps): JSX.Element {
    const TABLE_NUMBER_LABEL = "No.";
    const [tableData, setTableData] = useState(props.data);
    const [headers, setHeaders] = useState<string[]>([]);

    useEffect(() => {
        setTableData(props.data);
    }, [props.data]);

    useEffect(() => {
        setHeaders(tableData.length > 0 ? [TABLE_NUMBER_LABEL, ...Object.keys(tableData[0])] : []);
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
                </div>
            }

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
                                                    value={row[header] ?? ""}
                                                    onChange={(newValue) => { handleChange(rowIndex, header, newValue); }}
                                                    title={row[header] && row[header].length > 30 ? row[header] : ""}
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
