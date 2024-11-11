import { CommonButton, CommonDialog, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import "./PdfExtraction.scss";
import { ExtractedBit } from "./extractionComponents/ExtractedBit";
import { ExtractedTableBit } from "./extractionComponents/ExtractedTableBit";
import { PdfExtractionEmphasis } from "./extractionComponents/PdfExtractionEmphasis";
import { PdfExtractionVerification } from "./extractionComponents/PdfExtractionVerification";
import {
  ContractStatus,
  CONTRACT_TYPES,
  type ContractExtractionDictionary,
  type ContractObject,
  type LoadingListObject,
} from "@/interfaces";

enum ExtractionTabs {
  EXTRACTION = "Extraction",
  VERIFICATION = "Verification",
}

interface PdfExtractionProps {
  handleExpansion: () => void;
  isExpanded: boolean;
  selectedContract?: ContractObject;
  reprocessSelectedContract: () => void;
  loading: LoadingListObject;
}

export function PdfExtraction(props: PdfExtractionProps): JSX.Element {
  const [extractedBits, setExtractedBits] = useState<JSX.Element[]>([]);
  const [isApprovalConfirmationOpen, setIsApprovalConfirmationOpen] =
    useState(false);
  const [selectedTab, setSelectedTab] = useState<ExtractionTabs>(
    ExtractionTabs.EXTRACTION
  );

  useEffect(() => {
    function getExtractedBits(
      extractedData: ContractExtractionDictionary
    ): JSX.Element[] {
      const bits: JSX.Element[] = [];
      const lineItems: Record<string, string>[] = [];

      Object.entries(extractedData).forEach(([pageKey, page]) => {
        Object.entries(page).forEach(([label, value]) => {
          if (typeof value === "string") {
            bits.push(
              <ExtractedBit
                key={pageKey + label}
                label={label}
                value={value}
                onChange={(changeLabel, changeText) => {
                  handleBitChange(pageKey, changeLabel, changeText);
                }}
              />
            );
            // } else if (Array.isArray(value) && value.every(v => typeof v === "string")) {
            //     bits.push(<ExtractedBit
            //         key={pageKey + label}
            //         label={label}
            //         value={`- ${value.join("\n- ")}`}
            //         disabled
            //     />);
          } else if (label.startsWith("Line Item")) {
            if (!Array.isArray(value)) {
              const res = Object.fromEntries(
                Object.entries(value).filter(
                  ([_key, _value]) => typeof _value === "string"
                )
              ) as Record<string, string>;
              lineItems.push(res as Record<string, string>);
            }
            // } else if (typeof value === "string") { // Dictionary keys that don't start with "Line Item"
            //     bits.push(<ExtractedTableBit
            //                 key={pageKey + label}
            //                 label={label}
            //                 data={[value]}
            //                 onTableChange={(changeLabel, changeText) => { handleTableBitChange(pageKey, changeLabel, changeText); }}
            //                 hideNumber
            //             />);
          } else if (label.startsWith("Estimated Monthly Billing")) {
            const extractedBilling = Object.entries(
              value as Record<string, string>
            ).map(([itemKey, itemValue]) => {
              return { Date: itemKey, Amount: itemValue };
            });
            bits.push(
              <ExtractedTableBit
                key="monthlyBilling"
                label="Estimated Monthly Billing"
                data={extractedBilling as Record<string, string>[]}
                hideNumber
              />
            );
          }
        });
      });

      if (lineItems.length > 0)
        bits.unshift(
          <ExtractedTableBit
            key="line_items"
            label="Line Items"
            data={lineItems}
          />
        );

      return bits;
    }

    if (props.selectedContract?.response) {
      setExtractedBits(getExtractedBits(props.selectedContract.response));
    } else setExtractedBits([]);
    if (!props.selectedContract?.verification)
      setSelectedTab(ExtractionTabs.EXTRACTION);
  }, [props.selectedContract, props.selectedContract?.response]);

  function handleBitChange(
    _pageKey: string,
    _itemKey: string,
    _newValue: string
  ): void {
    // const pagePattern = /^page_\d+$/;
    // if (!pagePattern.test(pageKey)) return;
    // contractsContext.changeSelectedContractBit(pageKey as `page_${number}`, itemKey, newValue);
  }

  // function handleTableBitChange(
  //   pageKey: string,
  //   tableKey: string,
  //   newTableData: Record<string, string>[]
  // ): void {
  //   const pagePattern = /^page_\d+$/;
  //   if (!pagePattern.test(pageKey)) return;
  //   // contractsContext.changeSelectedContractTableBit(pageKey as `page_${number}`, tableKey, newTableData);
  // }

  function handleManualApproval(): void {
    setIsApprovalConfirmationOpen(true);
  }

  function handleExpansion(): void {
    props.handleExpansion();
  }

  function handleReprocess(): void {
    props.reprocessSelectedContract();
  }

  function confimedApproval(): void {
    setIsApprovalConfirmationOpen(false);
  }

  return (
    <div className="pdf-extraction-container">
      <div className="pdf-extraction-header">
        <div className="pdf-extraction-controls">
          <CommonButton
            className={[
              "expansion-arrow",
              props.isExpanded ? "expanded" : undefined,
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={handleExpansion}
            noBackground
            title={
              props.isExpanded
                ? "Restore views"
                : "Maximize Extraction / Verification view"
            }
          >
            <ElevaiteIcons.SVGSideArrow />
          </CommonButton>
          <div className="extraction-label">{ExtractionTabs.EXTRACTION}</div>
          {/* <div className="tabs-container">
                        <CommonButton
                            className={[
                                "tab-button",
                                selectedTab === ExtractionTabs.EXTRACTION ? "active" : undefined,
                            ].filter(Boolean).join(" ")}
                            onClick={() => { setSelectedTab(ExtractionTabs.EXTRACTION) }}
                        >
                            {ExtractionTabs.EXTRACTION}
                        </CommonButton>
                        {!contractsContext.selectedContract?.verification ? undefined :
                            <CommonButton
                                className={[
                                    "tab-button",
                                    selectedTab === ExtractionTabs.VERIFICATION ? "active" : undefined,
                                ].filter(Boolean).join(" ")}
                                onClick={() => { setSelectedTab(ExtractionTabs.VERIFICATION) }}
                            >
                                {ExtractionTabs.VERIFICATION}
                            </CommonButton>
                        }
                    </div> */}
          <CommonButton
            className="reprocess-button"
            onClick={handleReprocess}
            noBackground
            title="Reprocess file"
          >
            <ElevaiteIcons.SVGRefresh />
          </CommonButton>
        </div>
        {props.selectedContract?.content_type !==
        CONTRACT_TYPES.INVOICE ? undefined : props.selectedContract.verification
            ?.verification_status === true ? (
          <div className="approved-label">
            <ElevaiteIcons.SVGCheckmark />
            <span>Approved</span>
          </div>
        ) : (
          <CommonButton
            onClick={handleManualApproval}
            // disabled
          >
            Approve
          </CommonButton>
        )}
      </div>

      <div className="pdf-extraction-scroller">
        <div className="pdf-extraction-contents">
          {selectedTab === ExtractionTabs.EXTRACTION ? (
            <>
              <PdfExtractionEmphasis loading={props.loading} />
              {extractedBits.length === 0 ? (
                <div className="empty-bits">
                  {props.selectedContract?.status ===
                  ContractStatus.Extracting ? (
                    <>
                      <ElevaiteIcons.SVGSpinner />
                      <span>Extraction in progress...</span>
                    </>
                  ) : (
                    <span>No extracted data</span>
                  )}
                </div>
              ) : (
                extractedBits
              )}
            </>
          ) : (
            <PdfExtractionVerification loading={props.loading} />
          )}
        </div>
      </div>

      {!isApprovalConfirmationOpen || !props.selectedContract ? undefined : (
        <CommonDialog
          title={`Approve ${props.selectedContract.content_type}?`}
          onConfirm={confimedApproval}
          disableConfirm
          onCancel={() => {
            setIsApprovalConfirmationOpen(false);
          }}
        >
          <div className="invoice-approval-dialog-contents">
            <div>
              You will manually approve {props.selectedContract.content_type}{" "}
              {props.selectedContract.label ?? props.selectedContract.filename}
            </div>
            <div className="warning">
              This functionality has not been implemented yet.
            </div>
          </div>
        </CommonDialog>
      )}
    </div>
  );
}
