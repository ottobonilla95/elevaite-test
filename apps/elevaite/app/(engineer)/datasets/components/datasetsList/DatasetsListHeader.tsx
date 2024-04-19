import { CommonButton } from "@repo/ui/components";
import { TableFilters } from "../../../../lib/components/TableFilters/TableFilters";
import "./DatasetsListHeader.scss";


export enum DATASETS_LIST_TABS {
    EVALUATION = "Evaluation",
    DOMAIN = "Domain",
};


const DatasetsListTabsArray: {label: DATASETS_LIST_TABS, isDisabled?: boolean}[] = [
    { label: DATASETS_LIST_TABS.EVALUATION },
    { label: DATASETS_LIST_TABS.DOMAIN },
];


interface DatasetsListHeaderProps {
    selectedTab: DATASETS_LIST_TABS;
    onTabSelected: (tab: DATASETS_LIST_TABS) => void;
}

export function DatasetsListHeader(props: DatasetsListHeaderProps): JSX.Element {


    return (
        <div className="datasets-list-header-container">

            <div className="tabs-container">
                {DatasetsListTabsArray.map((item: {label: DATASETS_LIST_TABS, isDisabled?: boolean}) => 
                    <CommonButton
                        key={item.label}
                        className={[
                            "tab-button",
                            props.selectedTab === item.label ? "active" : undefined,
                        ].filter(Boolean).join(" ")}                        
                        onClick={() => { props.onTabSelected(item.label)}}
                        disabled={item.isDisabled}
                    >
                        {item.label}
                    </CommonButton>
                )}
            </div>

            <div className="controls-container">
                <TableFilters
                    
                />
            </div>

        </div>
    );
}