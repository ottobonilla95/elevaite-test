"use client";
import { useState } from "react";
import "./PdfAndExtraction.scss";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";
import { ContractComparison } from "./ContractComparison";
import {
  type LoadingListObject,
  type ContractObject,
  type ContractProjectObject,
} from "@/interfaces";

enum ExpandedPages {
  PDF = "pdf",
  DATA = "data",
}

interface PdfAndExtractionProps {
  projectId: string;
  selectedProject: ContractProjectObject;
  selectedContract: ContractObject;
  secondarySelectedContract?: ContractObject;
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
        props.selectedContract ? "active" : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {props.selectedContract && props.secondarySelectedContract ? (
        <ContractComparison
          loading={props.loading}
          projectId={props.projectId}
          selectedProject={props.selectedProject}
          selectedContract={props.selectedContract}
          secondarySelectedContract={props.secondarySelectedContract}
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
            projectId={props.projectId}
            selectedContract={props.selectedContract}
            selectedProject={props.selectedProject}
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
