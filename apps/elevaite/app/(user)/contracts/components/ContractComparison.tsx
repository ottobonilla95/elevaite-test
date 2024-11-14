import { CommonButton, CommonCheckbox, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useCallback, useRef, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import "./ContractComparison.scss";
import { ContractComparisonBlock } from "./ContractComparisonBlock";




export function ContractComparison(): JSX.Element {
    const contracts = useContracts();
    const [isShowingMatching, setIsShowingMatching] = useState(false);
    const [isOverviewMinimized, setIsOverviewMinimized] = useState(false);
    const scrollableRefMain = useRef<HTMLDivElement>(null);
    const scrollableRefSecondary = useRef<HTMLDivElement>(null);
    const scrollableRefMainFull = useRef<HTMLDivElement>(null);
    const scrollableRefSecondaryFull = useRef<HTMLDivElement>(null);
    const [isFullScreenCompare, setIsFullScreenCompare] = useState(false);
  

    function handleHome(): void {
        contracts.setSelectedContract(undefined);
        contracts.setSecondarySelectedContract(undefined);
    }

    function handleMainView(): void {
        contracts.setSecondarySelectedContract(undefined);
    }

    function handleToggleOverview(): void {
        setIsOverviewMinimized(current => !current);
    }

    function handleFullScreenCompare(): void {
        setIsFullScreenCompare(true);
    }

    function handleCloseFullScreenCompare(): void {
        setIsFullScreenCompare(false);
    }


    let scrolling = false;
    const syncScroll = useCallback((source: HTMLDivElement, target: HTMLDivElement) => {
        if (!scrolling) {
            scrolling = true;
            target.scrollLeft = source.scrollLeft;
            target.scrollTop = source.scrollTop;
            scrolling = false;
        }
    }, []);

    const handleScrollMain = useCallback(() => {
        if (scrollableRefMain.current && scrollableRefSecondary.current) {
            syncScroll(scrollableRefMain.current, scrollableRefSecondary.current);
        }
    }, [syncScroll]);
    const handleScrollSecondary = useCallback(() => {
        if (scrollableRefMain.current && scrollableRefSecondary.current) {
            syncScroll(scrollableRefSecondary.current, scrollableRefMain.current);
        }
    }, [syncScroll]);
    const handleScrollMainFull = useCallback(() => {
        if (scrollableRefMainFull.current && scrollableRefSecondaryFull.current) {
            syncScroll(scrollableRefMainFull.current, scrollableRefSecondaryFull.current);
        }
    }, [syncScroll]);
    const handleScrollSecondaryFull = useCallback(() => {
        if (scrollableRefMainFull.current && scrollableRefSecondaryFull.current) {
            syncScroll(scrollableRefSecondaryFull.current, scrollableRefMainFull.current);
        }
    }, [syncScroll]);



    return (
        <div className="contract-comparison-container">

            <div className="contract-comparison-header">
                <div className="comparison-breadcrumbs">
                    <CommonButton noBackground onClick={handleHome}>Home</CommonButton>
                    <span className="breadcrumb-separator">/</span>
                    <CommonButton noBackground onClick={handleMainView}>Main View</CommonButton>
                    <span className="breadcrumb-separator">/</span>
                    <span className="current-page">Comparison</span>
                </div>

                <div className="matching-controls">
                    <span>Include matching line items</span>
                    <CommonCheckbox onChange={setIsShowingMatching} />
                </div>
            </div>

            <ContractComparisonBlock
                showValidatedItems={isShowingMatching}
                isOverviewMinimized={isOverviewMinimized}
                onToggleOverview={handleToggleOverview}
                scrollRef={scrollableRefMain}
                onScroll={handleScrollMain}
                onFullScreenCompare={handleFullScreenCompare}
            />

            <ContractComparisonBlock
                secondary
                showValidatedItems={isShowingMatching}
                isOverviewMinimized={isOverviewMinimized}
                onToggleOverview={handleToggleOverview}
                scrollRef={scrollableRefSecondary}
                onScroll={handleScrollSecondary}
                onFullScreenCompare={handleFullScreenCompare}
            />

            {!isFullScreenCompare ? undefined :
                <CommonModal
                    className="full-screen-compare-line-items-modal"
                    onClose={handleCloseFullScreenCompare}
                >
                    <div className="full-screen-compare-container">
                        <div className="close-button-container">
                            <CommonButton
                                onClick={handleCloseFullScreenCompare}
                                noBackground
                            >
                                <ElevaiteIcons.SVGXmark />
                            </CommonButton>
                        </div>   
                        <ContractComparisonBlock
                            showValidatedItems={isShowingMatching}
                            isOverviewMinimized={isOverviewMinimized}
                            onToggleOverview={handleToggleOverview}
                            scrollRef={scrollableRefMainFull}
                            onScroll={handleScrollMainFull}
                            barebones
                        />
                        <ContractComparisonBlock
                            secondary
                            showValidatedItems={isShowingMatching}
                            isOverviewMinimized={isOverviewMinimized}
                            onToggleOverview={handleToggleOverview}
                            scrollRef={scrollableRefSecondaryFull}
                            onScroll={handleScrollSecondaryFull}
                            barebones
                        />
                    </div>
                </CommonModal>
            }

        </div>
    );
}