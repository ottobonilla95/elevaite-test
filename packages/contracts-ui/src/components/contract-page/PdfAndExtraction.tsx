"use client";
import { useState } from "react";
import "./PdfAndExtraction.scss";
import { ContractComparison } from "./ContractComparison";
import { PdfDisplay } from "./PdfDisplay";
import { PdfExtraction } from "./PdfExtraction";
import {
  CONTRACT_TYPES,
  LoadingListObject,
  type ContractObject,
} from "@/interfaces";

enum ExpandedPages {
  PDF = "pdf",
  DATA = "data",
}

interface PdfAndExtractionProps {
  projectId: string;
  fileId: string;
  contractsList: ContractObject[];
  contract: ContractObject;
  secondaryContract: ContractObject;
  file: File | Blob;
  loading: LoadingListObject;
  setSecondarySelectedContract: (
    contract?: ContractObject | CONTRACT_TYPES
  ) => void;
  setSecondarySelectedContractById: (id: string) => void;
  setSelectedContractById: (id?: string | number) => void;
  setSelectedContract: (contract?: ContractObject) => void;
  reprocessSelectedContract: () => void;
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
    <div className="contracts-content active">
      {props.contract && props.secondaryContract ? (
        <ContractComparison
          loading={props.loading}
          setSecondarySelectedContract={props.setSecondarySelectedContract}
          setSecondarySelectedContractById={
            props.setSecondarySelectedContractById
          }
          setSelectedContract={props.setSelectedContract}
          setSelectedContractById={props.setSelectedContractById}
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
            file={props.file}
            contract={props.contract}
            projectId={props.projectId}
          />
          <PdfExtraction
            loading={props.loading}
            reprocessSelectedContract={props.reprocessSelectedContract}
            handleExpansion={handleDataExpansion}
            isExpanded={expandedPage === ExpandedPages.DATA}
          />
        </div>
      )}
    </div>
  );
}
