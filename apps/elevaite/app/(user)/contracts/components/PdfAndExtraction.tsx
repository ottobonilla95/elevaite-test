"use client";
import { useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";




export function PdfAndExtraction(): JSX.Element {
    const contractsContext = useContracts();
    const [isDisplayExpanded, setIsDisplayExpanded] = useState(false);

    function handleExpansion(): void {
        setIsDisplayExpanded(current => !current);
    }
    
    return (        
        <div className={["contracts-content", contractsContext.selectedContract ? "active" : undefined].filter(Boolean).join(" ")}>
            <div className={["pdf-and-extraction-container", isDisplayExpanded ? "expanded" : undefined].filter(Boolean). join(" ")}>

                <PdfDisplay handleExpansion={handleExpansion} isExpanded={isDisplayExpanded} />

                <PdfExtraction/>

            </div>
        </div>
    );
}