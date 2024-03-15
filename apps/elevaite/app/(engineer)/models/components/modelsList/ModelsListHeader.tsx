import { CommonButton, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsListHeader.scss";


export enum MODELS_LIST_TABS {
    MODELS = "Models",
    VECTOR = "Embedding Models",
};


const ModelsListTabsArray: MODELS_LIST_TABS[] = [
    MODELS_LIST_TABS.MODELS,
    MODELS_LIST_TABS.VECTOR,
];


interface ModelsListHeaderProps {
    selectedTab: MODELS_LIST_TABS;
    onTabSelected: (tab: MODELS_LIST_TABS) => void;
}

export function ModelsListHeader(props: ModelsListHeaderProps): JSX.Element {


    return (
        <div className="models-list-header-container">

            <div className="tabs-container">
                {ModelsListTabsArray.map((item: MODELS_LIST_TABS) => 
                    <CommonButton
                        key={item}
                        className={[
                            "tab-button",
                            props.selectedTab === item ? "active" : undefined,
                        ].filter(Boolean).join(" ")}                        
                        onClick={() => { props.onTabSelected(item)}}
                    >
                        {item}
                    </CommonButton>
                )}
            </div>

            <div className="controls-container">
                <CommonSelect
                    options={[{label: "Filtered by", value: "none"}]}
                    defaultValue="none"
                    onSelectedValueChange={() => {console.log("Value changed")}}
                />
                <CommonButton
                    noBackground
                >
                    <ElevaiteIcons.SVGFilter/>
                </CommonButton>
                {/* Sortable by field type */}
                {/* Filters? */}
            </div>

        </div>
    );
}