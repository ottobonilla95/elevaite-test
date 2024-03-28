"use client";
import { useState } from "react";
import "./ModelsList.scss";
import { MODELS_LIST_TABS, ModelsListHeader } from "./modelsList/ModelsListHeader";
import { ModelsListTable } from "./modelsList/ModelsListTable";






export function ModelsList(): JSX.Element {
    const [selectedTab, setSelectedTab] = useState<MODELS_LIST_TABS>(MODELS_LIST_TABS.MODELS);



    return (
        <div className="models-list-container">
            <ModelsListHeader
                selectedTab={selectedTab}
                onTabSelected={setSelectedTab}
            />
            <ModelsListTable
                isVisible={selectedTab === MODELS_LIST_TABS.MODELS}
            />
        </div>
    );
}