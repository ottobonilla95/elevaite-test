"use client";
import { useState } from "react";
import "./PdfAndExtraction.scss";
import { ContractComparison } from "./ContractComparison";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";


enum ExpandedPages {
    PDF = "pdf",
    DATA = "data",
}


export function PdfAndExtraction(): JSX.Element {
    const contractsContext = useContracts();
    const [expandedPage, setExpandedPage] = useState<ExpandedPages | undefined>();

    function handlePdfExpansion(): void {
        setExpandedPage(current => current === ExpandedPages.PDF ? undefined : ExpandedPages.PDF);
    }
    function handleDataExpansion(): void {
        setExpandedPage(current => current === ExpandedPages.DATA ? undefined : ExpandedPages.DATA);
    }

    return (
        <div className={["contracts-content", contractsContext.selectedContract ? "active" : undefined].filter(Boolean).join(" ")}>

            {contractsContext.selectedContract && contractsContext.secondarySelectedContract ?
                <ContractComparison />
                :
                <div className={["pdf-and-extraction-container", expandedPage ? `expanded ${expandedPage}` : undefined].filter(Boolean).join(" ")}>
                    <PdfDisplay handleExpansion={handlePdfExpansion} isExpanded={expandedPage === ExpandedPages.PDF} />
                    <PdfExtraction handleExpansion={handleDataExpansion} isExpanded={expandedPage === ExpandedPages.DATA} />
                </div>
            }

        </div>
    );
}