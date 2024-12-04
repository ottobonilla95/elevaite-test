import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractObject, type ContractProjectObject, } from "../../interfaces";
import { ComparisonSelect } from "./ComparisonSelect";
import "./ContractComparisonBlock.scss";
import { PdfExtractionEmphasis } from "./extractionComponents/PdfExtractionEmphasis";
import { VerificationLineItems } from "./extractionComponents/VerificationLineItems";



interface ContractComparisonBlockProps {
  secondary?: boolean;
  showValidatedItems?: boolean;
  isOverviewMinimized?: boolean;
  onToggleOverview?: () => void;
  onScroll?: () => void;
  scrollRef?: React.RefObject<HTMLDivElement>;
  onFullScreenCompare?: () => void;
  barebones?: boolean;
  selectedProject: ContractProjectObject;
  contract?: ContractObject;
  projectId: string;
  selectedContractId: string;
  secondarySelectedContractId?: string;
  contractsList: ContractObject[];
}

export function ContractComparisonBlock(props: ContractComparisonBlockProps): JSX.Element {
  const [currentContract, setCurrentContract] = useState<ContractObject>();
  const [isLineItemsFullScreen, setIsLineItemsFullScreen] = useState(false);
  

  useEffect(() => {
    setCurrentContract(props.contract);
  }, [props.secondary, props.contract]);


  useEffect(() => {
    if (!props.scrollRef || !props.onScroll) return;
    const element = props.scrollRef.current;
    if (element) {
      element.addEventListener("scroll", props.onScroll);
    }
    return () => {
      if (element && props.onScroll)
        element.removeEventListener("scroll", props.onScroll);
    };
  }, [
    props.scrollRef,
    props.onScroll,
    props.secondary,
    props.contract,
  ]);



  return (
    <div
      className={[
        "contract-comparison-block-container",
        props.barebones ? "barebones" : undefined,
      ].filter(Boolean).join(" ")}
    >
      {props.barebones ? undefined : (
        <>
          <div className="contract-comparison-block-title">
            <ComparisonSelect
              contractsList={props.contractsList}
              contractId={props.selectedContractId}
              comparedContractId={props.secondarySelectedContractId}
              projectId={props.projectId}
              secondary={props.secondary}
              listFor={!props.secondary ? undefined : props.contract?.content_type}
            />
          </div>
          <div className="separator long" />
        </>
      )}

      <div ref={props.scrollRef} className="contract-comparison-block-scroller">
        {props.barebones ? undefined : (
          <>
            <div className="header-container">
              <span>Overview</span>
              {props.isOverviewMinimized === undefined ? undefined : (
                <CommonButton
                  className={[
                    "overview-toggle",
                    props.isOverviewMinimized ? "minimized" : undefined,
                  ].filter(Boolean).join(" ")}
                  onClick={props.onToggleOverview}
                  noBackground
                  title={
                    props.isOverviewMinimized
                      ? "Expand the overview section"
                      : "Minimize the overview section"
                  }
                >
                  <ElevaiteIcons.SVGChevron />
                </CommonButton>
              )}
            </div>
            <div
              className={[
                "comparison-overview-accordion",
                !props.isOverviewMinimized ? "open" : undefined,
              ].filter(Boolean).join(" ")}
            >
              <div className="comparison-overview-contents">
                <PdfExtractionEmphasis
                  secondary={props.secondary}
                  selectedContract={props.contract}
                  borderless
                />
              </div>
            </div>

            <div className="separator" />

            <div className="header-container">
              <span>Line Items</span>
              <div className="header-controls">
                {!props.onFullScreenCompare ? undefined : (
                  <CommonButton
                    className="full-screen-comparison-button"
                    onClick={props.onFullScreenCompare}
                    noBackground
                    title="View both tables in full-screen"
                  >
                    <ElevaiteIcons.SVGZoom />
                    <ElevaiteIcons.SVGZoom />
                  </CommonButton>
                )}
                <CommonButton
                  onClick={() => {
                    setIsLineItemsFullScreen(true);
                  }}
                  noBackground
                  title="View the table in full-screen"
                >
                  <ElevaiteIcons.SVGZoom />
                </CommonButton>
              </div>
            </div>
          </>
        )}

        {!currentContract?.line_items || currentContract.line_items.length === 0 ? 
          <div className="no-info">No line items.</div>
         : 
          <VerificationLineItems
            selectedProject={props.selectedProject}
            selectedContract={props.contract}
            lineItems={currentContract.line_items}
            fullScreen={isLineItemsFullScreen}
            onFullScreenClose={() => { setIsLineItemsFullScreen(false); }}
            hideValidatedItems={!props.showValidatedItems}
          />
        }
      </div>
    </div>
  );
}
