"use client";
import { useState } from "react";
import { useModels } from "../../../lib/contexts/ModelsContext";
import "./ModelsList.scss";
import { ModelsDetailsView } from "./modelsList/DetailsView/ModelsDetailsView";
import { MODELS_LIST_TABS, ModelsListHeader } from "./modelsList/ModelsListHeader";
import { ModelsListTable } from "./modelsList/ModelsListTable";






export function ModelsList(): JSX.Element {
    const modelsContext = useModels();
    const [selectedTab, setSelectedTab] = useState<MODELS_LIST_TABS>(MODELS_LIST_TABS.MODELS);

    function handleTabChange(tab: MODELS_LIST_TABS): void {
        if (tab !== selectedTab) modelsContext.setSelectedModel(undefined);
        setSelectedTab(tab);
    }

    return (
        <div
            className={[
                "models-list-container",
                modelsContext.selectedModel ? "details" : undefined,
            ].filter(Boolean).join(" ")}
        >            
            <div className="models-list-table">
                <ModelsListHeader
                    selectedTab={selectedTab}
                    onTabSelected={handleTabChange}
                />
                <ModelsListTable
                    isVisible={selectedTab === MODELS_LIST_TABS.MODELS}
                />
                <ModelsListTable
                    isEmbedding
                    isVisible={selectedTab === MODELS_LIST_TABS.EMBEDDING}
                />
            </div>
            <ModelsDetailsView/>
        </div>
    );
}