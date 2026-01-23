import type { JSX } from "react";
import { CommonSelectOption } from "../interfaces";
import "./AdvancedSelectOption.scss";
import { CommonButton } from "./CommonButton";


interface AdvancedSelectOptionUniqueProps {
    onOptionClick: (option: CommonSelectOption) => void;
    showTitles?: boolean;
}
export type AdvancedSelectOptionProps = AdvancedSelectOptionUniqueProps & CommonSelectOption;

export function AdvancedSelectOption({onOptionClick, showTitles, ...props}: AdvancedSelectOptionProps): JSX.Element {

    function handleClick(): void {
        onOptionClick(props);
    }


    return (
        <CommonButton
            className="advanced-select-option-container"
            onClick={handleClick}
            noBackground
            disabled={props.disabled}
            title={showTitles ? (props.label ? props.label : props.value) : ""}
        >
            <div className="advanced-select-option-contents">

                {!props.icon ? undefined : <div className="icon">{props.icon}</div> }

                <div className="advanced-select-option-text-block">
                    <div className="main-labels">
                        {!props.extras?.prefix ? undefined :
                            <span className="prefix" title={props.extras?.prefix?.tooltip ?? ""}>
                                {props.extras?.prefix?.label}
                            </span>
                        }
                        <span className="label">{props.label ? props.label : props.value}</span>
                        {!props.extras?.postfix ? undefined :
                            <span className="postfix" title={props.extras?.postfix?.tooltip ?? ""}>
                                {props.extras?.postfix?.label}
                            </span>
                        }
                    </div>

                    {!props.extras?.footer ? undefined : 
                        <div className="footer-items-container">
                            {props.extras.footer.map(item => 
                                <span key={item.label + item.tooltip} className="footer-item" title={item.tooltip ?? ""}>
                                    {item.label}
                                </span>
                            )}
                        </div>
                    }
                </div>
            </div>
        </CommonButton>
    );
}
