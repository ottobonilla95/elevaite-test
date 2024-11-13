"use client";
import { useState } from "react";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";
import { ContractComparison } from "./ContractComparison";
import { type LoadingListObject, type ContractObject } from "@/interfaces";

enum ExpandedPages {
  PDF = "pdf",
  DATA = "data",
}

interface PdfAndExtractionProps {
  projectId: string;
  primarycontract: ContractObject;
  contractsList: ContractObject[];
  loading: LoadingListObject;
  file: Blob;
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
      className={[
        "contracts-content",
        props.primarycontract ? "active" : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {props.primarycontract && secondaryContract ? (
        <ContractComparison
          loading={props.loading}
          projectId={props.projectId}
          primaryContract={props.primarycontract}
          contractsList={props.contractsList}
        />
      ) : (
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
          />
          <PdfExtraction
            loading={props.loading}
            projectId={props.projectId}
            handleExpansion={handleDataExpansion}
            isExpanded={expandedPage === ExpandedPages.DATA}
          />
        </div>
      )}
    </div>
  );
}
