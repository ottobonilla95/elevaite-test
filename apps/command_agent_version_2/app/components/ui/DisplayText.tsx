import { cls, CommonButton, CommonModal } from "@repo/ui";
import { type KeyboardEvent, useRef, useState, type JSX } from "react";
import { toast } from "../../lib/utilities/toast";
import { Icons } from "../icons";
import { AddVariable } from "./AddVariable";
import "./DisplayText.scss";



interface DisplayTextProps {
    value: string;
    onChange?: (value: string) => void;
    onKeyDown?: (key: string) => void;
    className?: string;
    label?: string;
    info?: string;
    placeholder?: string;
    readOnly?: boolean;
    disabled?: boolean;
    showExpand?: boolean;
    isExpanded?: boolean;
    expandedHeader?: string | React.ReactNode;
    showDownload?: boolean;
    showAIAssist?: boolean;
    showAddVariable?: boolean;
    topRightIcons?: React.ReactNode[];
    leftIcons?: React.ReactNode[];
    rightIcons?: React.ReactNode[];
}


export function DisplayText(props: DisplayTextProps): JSX.Element {
    const { value, onChange, onKeyDown, className, readOnly, disabled, placeholder, showExpand, showAddVariable, showDownload, showAIAssist, leftIcons, rightIcons, isExpanded, expandedHeader } = props;
    const [isModalOpen, setIsModalOpen] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const cursorPositionRef = useRef<number | null>(null);
    const selectionEndRef = useRef<number | null>(null);

    const showExpandButton = showExpand && !isExpanded;
    const hasLeftActions = showDownload || showAddVariable || leftIcons && leftIcons.length > 0;
    const hasRightActions = showExpandButton || showAIAssist || (rightIcons && rightIcons.length > 0);
    const isActionsBarVisible = hasLeftActions || hasRightActions;


    function handleChange(event: React.FormEvent<HTMLTextAreaElement>): void {
        if (onChange) onChange(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
        if (onKeyDown) onKeyDown(event.key);
    }

    function handleSelect(event: React.SyntheticEvent<HTMLTextAreaElement>): void {
        cursorPositionRef.current = event.currentTarget.selectionStart;
        selectionEndRef.current = event.currentTarget.selectionEnd;
    }

    function handleBlur(event: React.FocusEvent<HTMLTextAreaElement>): void {
        cursorPositionRef.current = event.currentTarget.selectionStart;
        selectionEndRef.current = event.currentTarget.selectionEnd;
    }

    function handleVariableSelect(variableLabel: string): void {
        if (!onChange) return;

        const currentValue = textareaRef.current?.value ?? value;
        const cursorPos = cursorPositionRef.current ?? currentValue.length;
        const selectionEnd = selectionEndRef.current ?? cursorPos;

        const newValue = currentValue.slice(0, cursorPos) + variableLabel + currentValue.slice(selectionEnd);
        onChange(newValue);

        const newCursorPos = cursorPos + variableLabel.length;
        cursorPositionRef.current = newCursorPos;
        selectionEndRef.current = newCursorPos;

        requestAnimationFrame(() => {
            if (textareaRef.current) {
                textareaRef.current.focus();
                textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
            }
        });
    }

    function handleExpand(): void {
        setIsModalOpen(true);
    }

    function handleCloseModal(): void {
        setIsModalOpen(false);
    }

    function handleAIAssist(): void {
        console.log("AI Assist coming soon!");
    }

    function handleDownload(): void {
        if (!value) {
            toast.warning("Nothing to download.", { position: "top-center" });
            return;
        };
        const blob = new Blob([value], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);

        const link: HTMLAnchorElement = document.createElement("a");
        link.href = url;
        link.download = "Downloaded text.txt";

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }


    return (
        <>
            <div className={cls("display-text-container nodrag nopan", className, disabled && "disabled")}>
                {isExpanded || (!props.label && !props.info && !props.topRightIcons) ? undefined :
                    <div className="header-container">
                        <div className="label-container">
                            <span>{props.label}</span>
                            {!props.info ? undefined :
                                <div title={props.info}>
                                    <Icons.SVGInfo />
                                </div>
                            }
                        </div>
                        {!props.topRightIcons || props.topRightIcons.length === 0 ? undefined :
                            props.topRightIcons.map(icon => icon)
                        }
                    </div>
                }
                <div className={cls("text-area-wrapper", readOnly && "read-only", disabled && "disabled", isActionsBarVisible && "flat-bottom")}>
                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={handleChange}
                        onKeyDown={handleKeyDown}
                        onSelect={handleSelect}
                        onBlur={handleBlur}
                        onWheelCapture={(event) => { event.stopPropagation(); }}
                        readOnly={Boolean(readOnly)}
                        disabled={disabled}
                        placeholder={placeholder}
                    />
                </div>
                {!isActionsBarVisible ? undefined :
                    <div className="actions-bar">
                        <div className="actions-side left">
                            {!showAddVariable ? undefined :
                                <AddVariable onSelect={handleVariableSelect} />
                            }
                            {!leftIcons || leftIcons.length === 0 ? undefined :
                                leftIcons.map(icon => icon)
                            }
                            {!showDownload ? undefined :
                                <CommonButton noBackground onClick={handleDownload} title="Save to your device">
                                    <Icons.Node.SVGDownload />
                                </CommonButton>
                            }
                        </div>
                        <div className="actions-side right">
                            {!rightIcons || rightIcons.length === 0 ? undefined :
                                rightIcons.map(icon => icon)
                            }
                            {!showAIAssist ? undefined :
                                <CommonButton noBackground onClick={handleAIAssist} title="Get some context-relevant help from Elai!">
                                    <Icons.SVGElai /> AI Assist
                                </CommonButton>
                            }
                            {!showExpandButton ? undefined :
                                <CommonButton noBackground onClick={handleExpand} title="Expand">
                                    <Icons.Node.SVGExpand />
                                </CommonButton>
                            }
                        </div>
                    </div>
                }
            </div>

            {!isModalOpen ? undefined :
                <CommonModal
                    className="display-text-modal-container"
                    onClose={handleCloseModal}
                >
                    <div className="header-bar">
                        <div className="label">
                            {expandedHeader ?
                                typeof expandedHeader === "string" ? <span>{expandedHeader}</span> : expandedHeader
                                : props.label ? <span>{props.label}</span> : undefined
                            }
                            {!props.info ? undefined :
                                <div title={props.info}>
                                    <Icons.SVGInfo />
                                </div>
                            }
                        </div>
                        <CommonButton noBackground onClick={handleCloseModal} title="Close">
                            <Icons.SVGClose />
                        </CommonButton>
                    </div>
                    <DisplayText
                        {...props}
                        isExpanded
                    />
                </CommonModal>
            }
        </>
    );
}