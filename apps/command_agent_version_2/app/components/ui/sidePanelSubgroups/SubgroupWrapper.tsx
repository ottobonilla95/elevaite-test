import { ElevaiteIcons } from "@repo/ui";
import { type SidePanelOption } from "../../../lib/interfaces";
import SidePanelItem from "./SidePanelItem";
import "./SubgroupWrapper.scss";



interface SubgroupWrapperProps {
    layout?: SidePanelOption[];
    onClick?: (option?: SidePanelOption) => void;
    isLoading?: boolean;
    errorMessage?: string;
    ignoreEmpty?: boolean;
}

export function SubgroupWrapper(props: SubgroupWrapperProps): React.ReactNode {

    function handleOptionClick(option?: SidePanelOption): void {
        if (props.onClick) props.onClick(option);
    }

    return (
        props.errorMessage ? 
            <div className="subgroup-error-message">
                {props.errorMessage}
            </div>
        :
        props.isLoading ? 
            <div className="subgroup-loading">
                <span>Loading. Please wait...</span>
                <ElevaiteIcons.SVGSpinner/>
            </div>
        :
        !props.layout || props.layout.length === 0 ? 
            props.ignoreEmpty ? undefined
            :
            <div className="subgroup-empty">
                No available options
            </div>
        :
            props.layout.map(option =>
                <SidePanelItem
                    key={option.id}
                    option={option}
                    onClick={handleOptionClick}
                />
            )
    );
}