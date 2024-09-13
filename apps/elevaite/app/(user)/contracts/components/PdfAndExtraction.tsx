"use client";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";




export function PdfAndExtraction(): JSX.Element {
    const contractsContext = useContracts();
    
    return (        
        <div className={["contracts-content", contractsContext.selectedContract ? "active" : undefined].filter(Boolean).join(" ")}>
            <div className="pdf-and-extraction-container">

                <PdfDisplay />

                <PdfExtraction/>

            </div>
        </div>
    );
}