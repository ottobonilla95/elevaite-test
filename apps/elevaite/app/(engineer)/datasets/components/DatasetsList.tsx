"use client";
import { useState } from "react";
import "./DatasetsList.scss";
import { DATASETS_LIST_TABS, DatasetsListHeader } from "./datasetsList/DatasetsListHeader";
import { DatasetsListTable } from "./datasetsList/DatasetsListTable";






export function DatasetsList(): JSX.Element {
    const [selectedTab, setSelectedTab] = useState<DATASETS_LIST_TABS>(DATASETS_LIST_TABS.EVALUATION);

    function handleTabChange(tab: DATASETS_LIST_TABS): void {
        setSelectedTab(tab);
    }

    return (
        <div
            className={[
                "datasets-list-container",
            ].filter(Boolean).join(" ")}
        >            
            <div className="datasets-list-table">
                <DatasetsListHeader
                    selectedTab={selectedTab}
                    onTabSelected={handleTabChange}
                />
                <DatasetsListTable
                    isVisible={selectedTab === DATASETS_LIST_TABS.EVALUATION}
                />
            </div>
        </div>
    );
}