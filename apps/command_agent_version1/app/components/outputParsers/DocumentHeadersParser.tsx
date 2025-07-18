import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./DocumentHeadersParser.scss";
import { useState } from "react";






interface DocumentHeadersParserProps {
    isJSON?: boolean;
	result?: Record<string, string> & { line_items?: unknown };
}

export function DocumentHeadersParser({ isJSON, result = {} }: DocumentHeadersParserProps): React.ReactNode {
    const documentEntries = Object.entries(result)
		.filter(([key]) => key !== "line_items")
		.map(([key, value]) => [key, value as string] as [string, string]);
	const [isExpanded, setIsExpanded] = useState(true);


    // function handleInspect(): void {
    //     console.log("Zoom/inspect clicked");
    // }

    function handleExpandToggle(): void {
        setIsExpanded((prev) => !prev);
    }


    return (
		documentEntries.length === 0 ? undefined :
        <div className="document-headers-parser-container">
            <div className="document-header-title-row">
                <h3>Document Headers</h3>
                <div className="document-header-actions">
                    {/* <CommonButton onClick={handleInspect} noBackground>
                        <ElevaiteIcons.SVGMagnifyingGlass />
                    </CommonButton> */}
                    <CommonButton className={["chevron-toggle", isExpanded ? "expanded" : ""].join(" ")} onClick={handleExpandToggle} noBackground>
                        <ElevaiteIcons.SVGChevron />
                    </CommonButton>
                </div>
            </div>
			<div className={["document-header-content-wrapper", isExpanded ? "expanded" : "collapsed"].join(" ")}>
				{isJSON ? (
					<pre>{JSON.stringify(Object.fromEntries(documentEntries), null, 2)}</pre>
				) : (
					<table className="document-headers-table">
						<tbody>
							{documentEntries.map(([key, value]) => (
								<tr key={key}>
									<td className="header-key">{key}</td>
									<td className="header-value">{value}</td>
								</tr>
							))}
						</tbody>
					</table>
				)}
			</div>
        </div>
    );
}