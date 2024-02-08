"use client";
import { useEffect, useRef, useState } from "react";
import SVGChevron from "../icons/elevaite/svgChevron";
import { ClickOutsideDetector } from "./ClickOutsideDetector";
import { CommonButton } from "./CommonButton";
import "./CommonSelect.scss";


export interface CommonSelectOption {
    label: string;
    value: string;
    icon?: React.ReactElement;
}


export interface CommonSelectProps extends React.HTMLAttributes<HTMLDivElement> {
    theme?: "light" | "dark";
    options: CommonSelectOption[];
    defaultValue?: string;
    anchor?: "left" | "right";
    onSelectedValueChange: (value: string) => void;
}


export function CommonSelect({theme, options, defaultValue, onSelectedValueChange, ...props}: CommonSelectProps): React.ReactElement<CommonSelectProps> {
    const [selectedOption, setSelectedOption] = useState<CommonSelectOption>();
    const [isOpen, setIsOpen] = useState(false);
    const buttonRef = useRef<HTMLButtonElement|null>(null);


    useEffect(() => {
        if (defaultValue) {
            const defaultOption = options.find((item) => { return item.value === defaultValue;})
            if (defaultOption) setSelectedOption(defaultOption);
            else setSelectedOption(options[0]);
        }
    }, []);


    function handleClick(option: CommonSelectOption): void {
        if (option !== selectedOption) {
            setSelectedOption(option);
            onSelectedValueChange(option.value);
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
                theme,
            ].filter(Boolean).join(" ")}
        >
            <CommonButton 
                passedRef={buttonRef}
                className="common-select-display"
                onClick={() => { setIsOpen((currentValue) => !currentValue); }}
                onDoubleClick={handleDoubleClick}
                noBackground
            >
                {selectedOption?.label ? selectedOption.label : "No selected option"}
                <SVGChevron/>
            </CommonButton>

            <ClickOutsideDetector onOutsideClick={() => setIsOpen(false)} ignoredRefs={[buttonRef]} >
                <div className={[
                    "common-select-options-container",
                    props.anchor ? `anchor-${props.anchor}` : undefined,
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
                                >
                                    {option.label}
                                </CommonButton>
                            )}
                        </div>
                    </div>
                </div>
            </ClickOutsideDetector>
        </div>
    );
}