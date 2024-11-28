import { CommonButton, CommonCheckbox, CommonModal, ElevaiteIcons, } from "@repo/ui/components";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { type ContractObject, type ContractProjectObject, } from "../../interfaces";
import "./ContractComparison.scss";
import { ContractComparisonBlock } from "./ContractComparisonBlock";



interface ContractComparisonProps {
  contract: ContractObject;
  comparedContract?: ContractObject;
  projectId: string;
  project: ContractProjectObject;
}

export function ContractComparison(props: ContractComparisonProps): JSX.Element {
  const router = useRouter();
  const scrollingRef = useRef(false);
  const [selectedContract, setSelectedContract] = useState<ContractObject>();
  const [secondarySelectedContract, setSecondarySelectedContract] = useState<ContractObject | undefined>();
  const [isShowingMatching, setIsShowingMatching] = useState(false);
  const [isOverviewMinimized, setIsOverviewMinimized] = useState(false);
  const scrollableRefMain = useRef<HTMLDivElement>(null);
  const scrollableRefSecondary = useRef<HTMLDivElement>(null);
  const scrollableRefMainFull = useRef<HTMLDivElement>(null);
  const scrollableRefSecondaryFull = useRef<HTMLDivElement>(null);
  const [isFullScreenCompare, setIsFullScreenCompare] = useState(false);

  useEffect(() => {
    setSelectedContract(props.contract);
    if (props.comparedContract && typeof props.comparedContract !== "boolean") {
      setSecondarySelectedContract(props.comparedContract);
    }
  }, [props.comparedContract, props.contract]);

  function handleHome(): void {
    router.push(`/${props.projectId}`);
  }

  function handleMainView(): void {
    router.push(`/${props.projectId}/${props.contract.id}/`);
  }

  function handleToggleOverview(): void {
    setIsOverviewMinimized((current) => !current);
  }

  function handleFullScreenCompare(): void {
    setIsFullScreenCompare(true);
  }

  function handleCloseFullScreenCompare(): void {
    setIsFullScreenCompare(false);
  }

  const syncScroll = useCallback((source: HTMLDivElement, target: HTMLDivElement) => {
    if (!scrollingRef.current) {
      scrollingRef.current = true;
      target.scrollLeft = source.scrollLeft;
      target.scrollTop = source.scrollTop;
      scrollingRef.current = false;
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
          <CommonButton noBackground onClick={handleHome}>
            Home
          </CommonButton>
          <span className="breadcrumb-separator">/</span>
          <CommonButton noBackground onClick={handleMainView}>
            Main View
          </CommonButton>
          <span className="breadcrumb-separator">/</span>
          <span className="current-page">Comparison</span>
        </div>

        <div className="matching-controls">
          <span>Include matching line items</span>
          <CommonCheckbox onChange={setIsShowingMatching} />
        </div>
      </div>

      <ContractComparisonBlock
        contract={selectedContract}
        showValidatedItems={isShowingMatching}
        contractsList={props.project.reports ?? []}
        projectId={props.projectId}
        selectedContractId={props.contract.id.toString()}
        secondarySelectedContractId={props.comparedContract?.id.toString()}
        selectedProject={props.project}
        isOverviewMinimized={isOverviewMinimized}
        onToggleOverview={handleToggleOverview}
        scrollRef={scrollableRefMain}
        onScroll={handleScrollMain}
        onFullScreenCompare={handleFullScreenCompare}
      />

      <ContractComparisonBlock
        secondary
        contract={secondarySelectedContract}
        showValidatedItems={isShowingMatching}
        contractsList={props.project.reports ?? []}
        projectId={props.projectId}
        selectedContractId={props.contract.id.toString()}
        secondarySelectedContractId={props.comparedContract?.id.toString()}
        selectedProject={props.project}
        isOverviewMinimized={isOverviewMinimized}
        onToggleOverview={handleToggleOverview}
        scrollRef={scrollableRefSecondary}
        onScroll={handleScrollSecondary}
        onFullScreenCompare={handleFullScreenCompare}
      />

      {!isFullScreenCompare ? undefined : (
        <CommonModal
          className="full-screen-compare-line-items-modal"
          onClose={handleCloseFullScreenCompare}
        >
          <div className="full-screen-compare-container">
            <div className="close-button-container">
              <CommonButton onClick={handleCloseFullScreenCompare} noBackground>
                <ElevaiteIcons.SVGXmark />
              </CommonButton>
            </div>
            <ContractComparisonBlock
              contract={selectedContract}
              contractsList={props.project.reports ?? []}
              projectId={props.projectId}
              selectedContractId={props.contract.id.toString()}
              secondarySelectedContractId={props.comparedContract?.id.toString()}
              selectedProject={props.project}
              isOverviewMinimized={isOverviewMinimized}
              onToggleOverview={handleToggleOverview}
              scrollRef={scrollableRefMainFull}
              onScroll={handleScrollMainFull}
              barebones
            />
            <ContractComparisonBlock
              secondary
              contract={secondarySelectedContract}
              contractsList={props.project.reports ?? []}
              projectId={props.projectId}
              selectedContractId={props.contract.id.toString()}
              secondarySelectedContractId={props.comparedContract?.id.toString()}
              selectedProject={props.project}
              isOverviewMinimized={isOverviewMinimized}
              onToggleOverview={handleToggleOverview}
              scrollRef={scrollableRefSecondaryFull}
              onScroll={handleScrollSecondaryFull}
              barebones
            />
          </div>
        </CommonModal>
      )}
    </div>
  );
}
