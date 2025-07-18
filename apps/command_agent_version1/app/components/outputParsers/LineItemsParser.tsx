import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useMemo, useState } from "react";
import "./LineItemsParser.scss";



interface LineItemsParserProps {
    isJSON?: boolean;
    lineItems?: Record<string, string>[];
}

export function LineItemsParser({ isJSON, lineItems = [] }: LineItemsParserProps): React.ReactNode {
    const [isExpanded, setIsExpanded] = useState(true);
    const headers = useMemo(() => {
        if (lineItems.length === 0) return [];
        return Object.keys(lineItems[0] || {});
    }, [lineItems]);
    // const [numericColumns, setNumericColumns] = useState<Set<string>>(new Set());


    const numericColumns = useMemo(() => {
        const detected = new Set<string>();
        for (const header of headers) {
            const values = lineItems.map((row) => row[header].toString());
            const numericMatches = values.filter((v) =>
                /^\s*(?:\$|€|£|USD|EUR|CAD)?\s*-?\d+(?:[.,]\d+)?\s*(?:USD|EUR|CAD|€|£)?\s*$/i.test(v)
            );
            if (numericMatches.length >= values.length * 0.9) {
                detected.add(header);
            }
        }
        return detected;
    }, [lineItems, headers]);

    
    // function handleInspect(): void {
    //     console.log("Inspect line items");
    // }

    function handleExpandToggle(): void {
        setIsExpanded((prev) => !prev);
    }


    return (
        lineItems.length === 0 ? undefined :
        <div className="line-items-parser-container">
            <div className="line-items-title-row">
                <h3>Line Items</h3>
                <div className="line-items-actions">
                    {/* <CommonButton onClick={handleInspect} noBackground>
                        <ElevaiteIcons.SVGMagnifyingGlass />
                    </CommonButton> */}
                    <CommonButton
                        onClick={handleExpandToggle}
                        noBackground
                        className={["chevron-toggle", isExpanded ? "expanded" : ""].join(" ")}
                    >
                        <ElevaiteIcons.SVGChevron />
                    </CommonButton>
                </div>
            </div>

            <div className={["line-items-content-wrapper", isExpanded ? "expanded" : "collapsed"].join(" ")}>
                {isJSON ? (
                    <pre>{JSON.stringify(lineItems, null, 2)}</pre>
                ) : (
                    <div className="line-items-table-wrapper">
                        <table className="line-items-table">
                            <thead>
                                <tr>
                                    {headers.map((header) => (
                                        <th key={header} className={numericColumns.has(header) ? "right-align" : undefined}>
                                            {header}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {lineItems.map((row, index) => (
                                    <tr key={`key_${index.toString()}`}>
                                        {Object.entries(row).map(([key, value]) => (
                                            <td key={key} className={numericColumns.has(key) ? "right-align" : undefined}>
                                                {value.trim()}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}