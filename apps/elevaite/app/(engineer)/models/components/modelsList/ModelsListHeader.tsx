import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsListHeader.scss";


export enum MODELS_LIST_TABS {
    MODELS = "Models",
    EMBEDDING = "Embedding Models",
};


const ModelsListTabsArray: {label: MODELS_LIST_TABS, isDisabled?: boolean}[] = [
    { label: MODELS_LIST_TABS.MODELS },
    { label: MODELS_LIST_TABS.EMBEDDING, isDisabled: true },
];


interface ModelsListHeaderProps {
    selectedTab: MODELS_LIST_TABS;
    onTabSelected: (tab: MODELS_LIST_TABS) => void;
}

export function ModelsListHeader(props: ModelsListHeaderProps): JSX.Element {


    return (
        <div className="models-list-header-container">

            <div className="tabs-container">
                {ModelsListTabsArray.map((item: {label: MODELS_LIST_TABS, isDisabled?: boolean}) => 
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
                <CommonButton
                    noBackground
                >
                    <ElevaiteIcons.SVGFilter/>
                </CommonButton>
            </div>

        </div>
    );
}