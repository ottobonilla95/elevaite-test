"use client";
import { useState } from "react";
import { type ContractObject, type ContractProjectObject, } from "../../interfaces";
import { ContractComparison } from "./ContractComparison";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";


enum ExpandedPages {
  PDF = "pdf",
  DATA = "data",
}


interface PdfAndExtractionProps {
  projectId: string;
  project?: ContractProjectObject;
  contract?: ContractObject;
  comparedContract?: ContractObject | boolean;
  file?: Blob;
}

export function PdfAndExtraction(props: PdfAndExtractionProps): JSX.Element {
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
    <div
      className={["contracts-content", props.contract ? "active" : undefined].filter(Boolean).join(" ")}
    >
      {props.contract &&
        (props.comparedContract && props.project?.reports) ? (
        <ContractComparison
          projectId={props.projectId}
          project={props.project}
          contract={props.contract}
          comparedContract={typeof props.comparedContract === "boolean" ? undefined : props.comparedContract}
        />
      ) : (
        <div
          className={["pdf-and-extraction-container", expandedPage ? `expanded ${expandedPage}` : undefined].filter(Boolean).join(" ")}
        >
          <PdfDisplay
            projectId={props.projectId}
            contract={props.contract}
            project={props.project}
            handleExpansion={handlePdfExpansion}
            isExpanded={expandedPage === ExpandedPages.PDF}
            file={props.file}
          />
          <PdfExtraction
            projectId={props.projectId}
            handleExpansion={handleDataExpansion}
            isExpanded={expandedPage === ExpandedPages.DATA}
            contract={props.contract}
          />
        </div>
      )}
    </div>
  );
}
