"use client";
import { useEffect, useRef, useState } from "react";
import SVGChevron from "../icons/elevaite/svgChevron";
import { ClickOutsideDetector } from "./ClickOutsideDetector";
import { CommonButton } from "./CommonButton";
import "./CommonSelect.scss";
import SVGSpinner from "../icons/elevaite/svgSpinner";


export interface CommonSelectOption {
    label?: string;
    value: string;
    selectedLabel?: string; // Use this instead of label when it is the selected item
    icon?: React.ReactElement;
}


export interface CommonSelectProps extends React.HTMLAttributes<HTMLDivElement> {
    options: CommonSelectOption[];
    defaultValue?: string;
    noSelectionMessage?: string;
    anchor?: "left" | "right";
    showTitles?: boolean;
    disabled?: boolean;
    isLoading?: boolean;
    onSelectedValueChange: (value: string, label: string) => void;
}


export function CommonSelect({options, defaultValue, noSelectionMessage, anchor, showTitles, onSelectedValueChange, isLoading, ...props}: CommonSelectProps): React.ReactElement<CommonSelectProps> {
    const [selectedOption, setSelectedOption] = useState<CommonSelectOption>();
    const [isOpen, setIsOpen] = useState(false);
    const buttonRef = useRef<HTMLButtonElement|null>(null);


    useEffect(() => {
        if (defaultValue) {
            const defaultOption = options.find((item) => { return item.value === defaultValue;})
            if (defaultOption) setSelectedOption(defaultOption);
            else setSelectedOption(options[0]);
        }
    }, [defaultValue]);


    function handleClick(option: CommonSelectOption): void {
        if (option !== selectedOption) {
            setSelectedOption(option);
            onSelectedValueChange(option.value, option.label ? option.label : option.value);
        }
        setIsOpen(false);
    }

    function handleDoubleClick(): void {
        if (options.length === 2 && selectedOption?.value === options[0].value) handleClick(options[1]);
        else if (options.length === 2 && selectedOption?.value === options[1].value) handleClick(options[0]);
        else setIsOpen((currentValue) => !currentValue);
    }



    return (
        <div
            {...props}
            className={[
                "common-select",
                props.className,
            ].filter(Boolean).join(" ")}
        >
            <CommonButton 
                passedRef={buttonRef}
                className="common-select-display"
                onClick={() => { setIsOpen((currentValue) => !currentValue); }}
                onDoubleClick={handleDoubleClick}
                noBackground
                title={selectedOption && (selectedOption?.selectedLabel || showTitles) ? (selectedOption.label ? selectedOption.label : selectedOption.value) : ""}
                disabled={props.disabled || isLoading}
            >
                <span>
                    {isLoading ? "Please wait..." :
                        !selectedOption ? noSelectionMessage ? noSelectionMessage : "No selected option" :
                        selectedOption.selectedLabel ? selectedOption.selectedLabel : (selectedOption.label ? selectedOption.label : selectedOption.value)
                    }
                </span>
                {isLoading ? 
                    <SVGSpinner className="spinner"/>
                    :
                    <SVGChevron/>
                }
            </CommonButton>

            <ClickOutsideDetector onOutsideClick={() => setIsOpen(false)} ignoredRefs={[buttonRef]} >
                <div className={[
                    "common-select-options-container",
                    anchor ? `anchor-${anchor}` : undefined,
                    isOpen ? "open" : undefined,
                ].filter(Boolean).join(" ")}>
                    <div className="common-select-options-accordion">
                        <div className="common-select-options-contents">
                            {options.map((option) => 
                                <CommonButton
                                    className="common-select-option"
                                    key={option.value}
                                    onClick={() => { handleClick(option); } }
                                    noBackground
                                    title={showTitles ? (option.label ? option.label : option.value) : ""}
                                >
                                    <span>{option.label ? option.label : option.value}</span>
                                </CommonButton>
                            )}
                        </div>
                    </div>
                </div>
            </ClickOutsideDetector>
        </div>
    );
}