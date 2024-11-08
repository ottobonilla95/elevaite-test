import {
  CommonButton,
  CommonCheckbox,
  CommonModal,
  ElevaiteIcons,
} from "@repo/ui/components";
import { useCallback, useRef, useState } from "react";
import "./ContractComparison.scss";
import { useRouter } from "next/router";
import { ContractComparisonBlock } from "./ContractComparisonBlock";
import {
  type CONTRACT_TYPES,
  type ContractObject,
  type LoadingListObject,
} from "@/interfaces";

interface ContractComparisonProps {
  loading: LoadingListObject;
  setSelectedContract: (contract?: ContractObject) => void;
  setSecondarySelectedContract: (
    contract?: ContractObject | CONTRACT_TYPES
  ) => void;
  setSelectedContractById: (id?: string | number) => void;
  setSecondarySelectedContractById: (id: string) => void;
}

export function ContractComparison(
  props: ContractComparisonProps
): JSX.Element {
  const router = useRouter();
  const [isShowingMatching, setIsShowingMatching] = useState(false);
  const [isOverviewMinimized, setIsOverviewMinimized] = useState(false);
  const scrollableRefMain = useRef<HTMLDivElement>(null);
  const scrollableRefSecondary = useRef<HTMLDivElement>(null);
  const scrollableRefMainFull = useRef<HTMLDivElement>(null);
  const scrollableRefSecondaryFull = useRef<HTMLDivElement>(null);
  const [isFullScreenCompare, setIsFullScreenCompare] = useState(false);

  function handleHome(): void {
    const currentPath = router.asPath;
    const segments = currentPath.split("/").filter(Boolean);

    const newSegments = segments.slice(0, segments.length - 2);

    const newPath = `/${newSegments.join("/")}`;

    void router.push(newPath);
  }

  function handleMainView(): void {
    const currentPath = router.asPath;
    const newPath = currentPath.substring(0, currentPath.lastIndexOf("/"));
    void router.push(newPath);
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

  const scrollingRef = useRef(false);
  const syncScroll = useCallback(
    (source: HTMLDivElement, target: HTMLDivElement) => {
      scrollingRef.current = true;
      target.scrollLeft = source.scrollLeft;
      target.scrollTop = source.scrollTop;
      scrollingRef.current = false;
    },
    []
  );

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
      syncScroll(
        scrollableRefMainFull.current,
        scrollableRefSecondaryFull.current
      );
    }
  }, [syncScroll]);
  const handleScrollSecondaryFull = useCallback(() => {
    if (scrollableRefMainFull.current && scrollableRefSecondaryFull.current) {
      syncScroll(
        scrollableRefSecondaryFull.current,
        scrollableRefMainFull.current
      );
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
        showValidatedItems={isShowingMatching}
        isOverviewMinimized={isOverviewMinimized}
        onToggleOverview={handleToggleOverview}
        scrollRef={scrollableRefMain}
        onScroll={handleScrollMain}
        onFullScreenCompare={handleFullScreenCompare}
        loading={props.loading}
        setSelectedContract={props.setSelectedContract}
        setSelectedContractById={props.setSelectedContractById}
        setSecondarySelectedContractById={
          props.setSecondarySelectedContractById
        }
      />

      <ContractComparisonBlock
        secondary
        showValidatedItems={isShowingMatching}
        isOverviewMinimized={isOverviewMinimized}
        onToggleOverview={handleToggleOverview}
        scrollRef={scrollableRefSecondary}
        onScroll={handleScrollSecondary}
        onFullScreenCompare={handleFullScreenCompare}
        loading={props.loading}
        setSelectedContract={props.setSelectedContract}
        setSelectedContractById={props.setSelectedContractById}
        setSecondarySelectedContractById={
          props.setSecondarySelectedContractById
        }
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
              showValidatedItems={isShowingMatching}
              isOverviewMinimized={isOverviewMinimized}
              onToggleOverview={handleToggleOverview}
              scrollRef={scrollableRefMainFull}
              onScroll={handleScrollMainFull}
              barebones
              loading={props.loading}
              onFullScreenCompare={handleFullScreenCompare}
              setSelectedContract={props.setSelectedContract}
              setSelectedContractById={props.setSelectedContractById}
              setSecondarySelectedContractById={
                props.setSecondarySelectedContractById
              }
            />
            <ContractComparisonBlock
              secondary
              showValidatedItems={isShowingMatching}
              isOverviewMinimized={isOverviewMinimized}
              onToggleOverview={handleToggleOverview}
              scrollRef={scrollableRefSecondaryFull}
              onScroll={handleScrollSecondaryFull}
              barebones
              loading={props.loading}
              onFullScreenCompare={handleFullScreenCompare}
              setSelectedContract={props.setSelectedContract}
              setSelectedContractById={props.setSelectedContractById}
              setSecondarySelectedContractById={
                props.setSecondarySelectedContractById
              }
            />
          </div>
        </CommonModal>
      )}
    </div>
  );
}
