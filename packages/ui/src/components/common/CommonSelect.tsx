"use client";
import { useEffect, useRef, useState } from "react";
import { ElevaiteIcons } from "../icons";
import SVGChevron from "../icons/elevaite/svgChevron";
import SVGSpinner from "../icons/elevaite/svgSpinner";
import { type CommonSelectOption } from "../interfaces";
import { type AdvancedSelectOptionProps } from "./AdvancedSelectOption";
import { ClickOutsideDetector } from "./ClickOutsideDetector";
import { CommonButton } from "./CommonButton";
import "./CommonSelect.scss";


export interface CommonSelectProps extends React.HTMLAttributes<HTMLDivElement> {
    options: CommonSelectOption[];
    defaultValue?: string;
    controlledValue?: string; // Use this to control the value externally
    callbackOnDefaultValue?: boolean;
    noSelectionMessage?: string;
    anchor?: "left" | "right";
    showTitles?: boolean;
    showSelected?: boolean;
    emptyListLabel?: string;
    disabled?: boolean;
    isLoading?: boolean;
    onSelectedValueChange: (value: string, label: string) => void;
    onAdd?: () => void;
    addLabel?: string;
    noDoubleClick?: boolean;
    useCommonStyling?: boolean;
    AdvancedOptionComponent?: (props: AdvancedSelectOptionProps) => JSX.Element;
}


export function CommonSelect({
    options, defaultValue, controlledValue, callbackOnDefaultValue, noSelectionMessage,
    anchor, showTitles, showSelected, emptyListLabel, onSelectedValueChange, onAdd, addLabel, useCommonStyling,
    noDoubleClick, isLoading, AdvancedOptionComponent, ...props}: CommonSelectProps): React.ReactElement<CommonSelectProps> {
    const [selectedOption, setSelectedOption] = useState<CommonSelectOption>();
    const [isOpen, setIsOpen] = useState(false);
    const buttonRef = useRef<HTMLButtonElement|null>(null);


    useEffect(() => {
        if (controlledValue === undefined && selectedOption !== undefined) setSelectedOption(undefined);
        else if (controlledValue !== undefined && controlledValue !== selectedOption?.value) {
            findAndSelectOption(controlledValue, true);
        }
    }, [controlledValue, options.length]);

    useEffect(() => {
        if (defaultValue) {
            findAndSelectOption(defaultValue);
        }
    }, [isLoading, defaultValue, options.length]);


    function findAndSelectOption(value: string, checkCallback?: boolean): void {
        if (options.length === 0) {
            setSelectedOption(undefined);
            return;
        }
        const foundOption = options.find((item) => { return item.value === value;});
        if (foundOption) {
            setSelectedOption(foundOption);
            if (checkCallback || callbackOnDefaultValue) onSelectedValueChange(foundOption.value, foundOption.label ? foundOption.label : foundOption.value);
        }
        else if (options[0]) {
            setSelectedOption(options[0]);
            if (checkCallback || callbackOnDefaultValue) onSelectedValueChange(options[0].value, options[0].label ? options[0].label : options[0].value);
        }
    }


    function handleClick(option: CommonSelectOption): void {
        if (option !== selectedOption) {
            setSelectedOption(option);
            onSelectedValueChange(option.value, option.label ? option.label : option.value);
        }
        setIsOpen(false);
    }

    function handleDoubleClick(): void {
        if (noDoubleClick) return;
        if (options.length === 2 && selectedOption?.value === options[0].value) handleClick(options[1]);
        else if (options.length === 2 && selectedOption?.value === options[1].value) handleClick(options[0]);
        else setIsOpen((currentValue) => !currentValue);
    }

    function handleAdd(): void {
        if (onAdd) onAdd();
    }

    function handleToggle(): void {
        setIsOpen((currentValue) => !currentValue);
    }
    function handleClose(): void {
        setIsOpen(false)
    }



    return (
        <div
            {...props}
            className={[
                "common-select",
                props.className,
                useCommonStyling ? "common-style" : undefined,
                props.disabled ? "disabled" : undefined,
                AdvancedOptionComponent ? "advanced" : undefined,
            ].filter(Boolean).join(" ")}
        >
            <CommonButton 
                passedRef={buttonRef}
                className="common-select-display"
                onClick={handleToggle}
                onDoubleClick={handleDoubleClick}
                noBackground
                title={selectedOption && (selectedOption.selectedLabel || showTitles) ? (selectedOption.label ? selectedOption.label : selectedOption.value) : ""}
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

            <ClickOutsideDetector onOutsideClick={handleClose} ignoredRefs={[buttonRef]} >
                <div className={[
                    "common-select-options-container",
                    anchor ? `anchor-${anchor}` : undefined,
                    isOpen ? "open" : undefined,
                ].filter(Boolean).join(" ")}>
                    <div className="common-select-options-accordion">
                        <div className="common-select-options-contents">
                            {options.length === 0 ? 
                                <div className="empty-list">
                                    {emptyListLabel ? emptyListLabel : "No options"}
                                </div>
                            :
                            options.map((option) => 
                                option.isSeparator ? typeof option.isSeparator === "boolean" ? 
                                    <div key={option.value} className="select-separator-container">
                                        {!option.label ? undefined : <><div className="select-separator start"/><span>{option.label}</span></>}
                                        <div className="select-separator"/>
                                    </div>
                                : <div key={option.value}>{option.isSeparator}</div> :
                                    AdvancedOptionComponent ? 
                                    <AdvancedOptionComponent key={option.value} {...option} onOptionClick={handleClick} showTitles={showTitles} />
                                :
                                <CommonButton
                                    className={["common-select-option", showSelected && selectedOption?.value === option.value ? "selected" : undefined].filter(Boolean).join(" ")}
                                    key={option.value}
                                    onClick={() => { handleClick(option); } }
                                    noBackground
                                    disabled={option.disabled}
                                    title={showTitles ? (option.label ? option.label : option.value) : ""}
                                >
                                    {!showSelected || selectedOption?.value !== option.value ? undefined :
                                        <ElevaiteIcons.SVGCheckmark />
                                    }
                                    <span>{option.label ? option.label : option.value}</span>
                                </CommonButton>
                            )}
                            {!onAdd ? undefined :
                                <CommonButton
                                    className="common-select-add-option"
                                    onClick={handleAdd}
                                    noBackground
                                >
                                    <span>{addLabel ? addLabel : "+"}</span>
                                </CommonButton>
                            }
                        </div>
                    </div>
                </div>
            </ClickOutsideDetector>
        </div>
    );
}