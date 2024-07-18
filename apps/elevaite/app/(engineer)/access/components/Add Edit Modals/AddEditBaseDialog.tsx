import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./AddEditBaseDialog.scss";
import React from "react";



interface AddEditBaseDialogProps {
    header: React.ReactNode;
    subHeader?: React.ReactNode;
    buttonLabel: string;
    buttonTitle?: string;
    disabled?: boolean;
    onClick: () => void;
    onClose: () => void;
    children?: React.ReactNode;
    loading?: boolean;
}

export function AddEditBaseDialog(props: AddEditBaseDialogProps): JSX.Element {


    function handleClick(): void {
        props.onClick();
    }

    function handleClose(): void {
        props.onClose();
    }


    return (
        <div className="add-edit-base-dialog-container">

            {!props.loading ? undefined :
                <div className="base-dialog-loading">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            } 

            <div className="base-dialog-header">
                <div className="base-dialog-title">
                    {props.header}
                </div>
                <div className="close-button">                    
                    <CommonButton onClick={handleClose} noBackground>
                        <ElevaiteIcons.SVGXmark/>
                    </CommonButton>
                </div>
                {!props.subHeader ? null :
                    <div className="base-dialog-subtitle">
                        {props.subHeader}
                    </div>
                }
            </div>

            <div className="details-scroller">
                <div className="details-content">
                    {props.children}
                </div>
            </div>
            
            <div className="controls-container">
                <CommonButton
                    className="base-dialog-button"
                    onClick={handleClose}
                >
                    Cancel
                </CommonButton>
                <CommonButton
                    className="base-dialog-button submit"
                    disabled={props.disabled}
                    title={props.buttonTitle}
                    onClick={handleClick}
                >
                    {props.buttonLabel}
                </CommonButton>
            </div>
        </div>
    );
}

