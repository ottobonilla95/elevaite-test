"use client";
import { useState } from "react";
import { useContracts } from "../lib/contexts/ContractsContext";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";
import { ContractObject } from "@/lib/interfaces";

enum ExpandedPages {
  PDF = "pdf",
  DATA = "data",
}

export function PdfAndExtraction({
  projectId,
  fileId,
  contractsList,
  contract,
  file,
}: {
  projectId: string;
  fileId: string;
  contractsList: ContractObject[];
  contract: ContractObject;
  file: File | Blob;
}): JSX.Element {
  // const contractsContext = useContracts();
  const [expandedPage, setExpandedPage] = useState<ExpandedPages | undefined>();

  function handlePdfExpansion(): void {
    setExpandedPage((current) =>
      current === ExpandedPages.PDF ? undefined : ExpandedPages.PDF
    );
  }
  function handleDataExpansion(): void {
    setExpandedPage((current) =>
      current === ExpandedPages.DATA ? undefined : ExpandedPages.DATA
    );
  }

  return (
    <div className="contracts-content active">
      <div
        className={[
          "pdf-and-extraction-container",
          expandedPage ? `expanded ${expandedPage}` : undefined,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <PdfDisplay
          handleExpansion={handlePdfExpansion}
          isExpanded={expandedPage === ExpandedPages.PDF}
          file={file}
          contract={contract}
        />

        <PdfExtraction
          handleExpansion={handleDataExpansion}
          isExpanded={expandedPage === ExpandedPages.DATA}
        />
      </div>
    </div>
  );
}
