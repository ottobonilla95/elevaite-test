import { useEffect, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import "./ContractComparisonBlock.scss";
import { ContractObject } from "@/interfaces";
import { ComparisonSelect } from "./ComparisonSelect";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
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
}

export function ContractComparisonBlock(props: ContractComparisonBlockProps): JSX.Element {
    const contracts = useContracts();
    const [currentContract, setCurrentContract] = useState<ContractObject>();
    const [isLineItemsFullScreen, setIsLineItemsFullScreen] = useState(false);


    useEffect(() => {
        if (props.secondary) {
            if (contracts.secondarySelectedContract && typeof contracts.secondarySelectedContract === "object")
                setCurrentContract(contracts.secondarySelectedContract);
            else
                setCurrentContract(undefined);
        } else {
            setCurrentContract(contracts.selectedContract);
        }
    }, [props.secondary, contracts.selectedContract, contracts.secondarySelectedContract]);

    useEffect(() => {
        if (!props.scrollRef || !props.onScroll) return;
        const element = props.scrollRef.current;
        if (element) {
            element.addEventListener("scroll", props.onScroll);
        }
        return () => {
            if (element && props.onScroll) element.removeEventListener("scroll", props.onScroll);
        };
    }, [props.scrollRef, props.onScroll, props.secondary, contracts.selectedContract, contracts.secondarySelectedContract]);


    return (
        <div className={["contract-comparison-block-container", props.barebones ? "barebones" : undefined].filter(Boolean).join(" ")}>
            {props.barebones ? undefined :
                <>
                    <div className="contract-comparison-block-title">
                        <ComparisonSelect secondary={props.secondary} listFor={!props.secondary ? undefined : contracts.selectedContract?.content_type} />
                    </div>
                    <div className="separator long" />
                </>
            }

            <div
                ref={props.scrollRef}
                className="contract-comparison-block-scroller"
            >

                {props.barebones ? undefined :
                    <>
                        <div className="header-container">
                            <span>Overview</span>
                            {props.isOverviewMinimized === undefined ? undefined :
                                <CommonButton
                                    className={["overview-toggle", props.isOverviewMinimized ? "minimized" : undefined].filter(Boolean).join(" ")}
                                    onClick={props.onToggleOverview}
                                    noBackground
                                    title={props.isOverviewMinimized ? "Expand the overview section" : "Minimize the overview section"}
                                >
                                    <ElevaiteIcons.SVGChevron />
                                </CommonButton>
                            }
                        </div>
                        <div className={[
                            "comparison-overview-accordion",
                            !props.isOverviewMinimized ? "open" : undefined,
                        ].filter(Boolean).join(" ")}>
                            <div className="comparison-overview-contents">
                                <PdfExtractionEmphasis secondary={props.secondary} borderless />
                            </div>
                        </div>

                        <div className="separator" />

                        <div className="header-container">
                            <span>Line Items</span>
                            <div className="header-controls">
                                {!props.onFullScreenCompare ? undefined :
                                    <CommonButton
                                        className="full-screen-comparison-button"
                                        onClick={props.onFullScreenCompare}
                                        noBackground
                                        title="View both tables in full-screen"
                                    >
                                        <ElevaiteIcons.SVGZoom />
                                        <ElevaiteIcons.SVGZoom />
                                    </CommonButton>
                                }
                                <CommonButton
                                    onClick={() => { setIsLineItemsFullScreen(true); }}
                                    noBackground
                                    title="View the table in full-screen"
                                >
                                    <ElevaiteIcons.SVGZoom />
                                </CommonButton>
                            </div>
                        </div>
                    </>
                }

                {!currentContract?.line_items || currentContract.line_items.length === 0 ?
                    <div className="no-info">
                        No line items.
                    </div>
                    :
                    <VerificationLineItems
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