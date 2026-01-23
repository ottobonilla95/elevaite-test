import type { JSX } from "react";
import { ElevaiteIcons } from "../icons/elevaite";
import { CommonButton } from "./CommonButton";
import "./CommonDialog.scss";
import { CommonModal } from "./CommonModal";



interface CommonDialogProps {
    className?: string;
    title: string;
    onConfirm: () => void;
    onCancel?: () => void;
    confirmLabel?: string;
    cancelLabel?: string;
    disableConfirm?: boolean;
    confirmTooltip?: string;
    dangerSubmit?: boolean;
    icon?: React.ReactNode;
    innerClassName?: string;
    children?: React.ReactNode;
}

export function CommonDialog(props: CommonDialogProps): JSX.Element {

    function handleCancel(): void {
        if (props.onCancel) props.onCancel();
    }

    function handleConfirm(): void {
        props.onConfirm();
    }


    return (
        <div className="common-dialog-container">
            <CommonModal onClose={handleCancel}>
                <div className={["common-dialog-contents", props.innerClassName].filter(Boolean).join(" ")}>
                    
                    <div className="dialog-header">
                        <div className="dialog-title">
                            {!props.icon ? undefined :
                                <div className="title-icon">
                                    {props.icon}
                                </div>
                            }
                            <span>{props.title}</span>
                        </div>
                        {!props.onCancel ? undefined :
                            <div className="close-button">                    
                                <CommonButton onClick={handleCancel} noBackground>
                                    <ElevaiteIcons.SVGXmark/>
                                </CommonButton>
                            </div>
                        }
                    </div>

                    
                    {props.children}


                    <div className="controls-container">
                        {!props.onCancel ? undefined :
                            <CommonButton
                                className="dialog-button"
                                onClick={handleCancel}
                            >
                                {props.cancelLabel ? props.cancelLabel : "Cancel"}
                            </CommonButton>
                        }
                        <CommonButton
                            className={[
                                "dialog-button",
                                props.dangerSubmit ? "danger" : "submit"
                            ].join(" ")}
                            onClick={handleConfirm}
                            disabled={props.disableConfirm}
                            title={props.confirmTooltip}
                        >
                            {props.confirmLabel ? props.confirmLabel : "Confirm"}
                        </CommonButton>
                    </div>


                </div>
            </CommonModal>
        </div>
    );
}