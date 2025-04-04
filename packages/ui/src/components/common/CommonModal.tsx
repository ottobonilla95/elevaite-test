/* eslint-disable jsx-a11y/no-static-element-interactions -- This is a catch-all, disabled users will have other means to do the same thing. >.< */
"use client";
import { createPortal } from 'react-dom';
import "./CommonModal.scss";
import { useState } from 'react';


export interface CommonModalProps extends React.HTMLAttributes<HTMLDivElement> {
    onClose?: () => void;
    zIndex?: number;
}


export function CommonModal(props: CommonModalProps): React.ReactElement<CommonModalProps> {
    const [hasClickedDown, setHasClickedDown] = useState(false);

    function handleMouseDown(event: React.FormEvent<HTMLDivElement>): void {
        setHasClickedDown(event.target === event.currentTarget);
    }
    function handleMouseUp(event: React.FormEvent<HTMLDivElement>): void {
        if (props.onClose && event.target === event.currentTarget && hasClickedDown) {
            props.onClose();
        }
    }


    return (
        <>
            {createPortal(

                <div
                    className={[
                        "common-modal-container",
                        props.className,
                    ].filter(Boolean).join(" ")}
                    onMouseDown={handleMouseDown}
                    onMouseUp={handleMouseUp}
                    style={{
                        zIndex: props.zIndex ? props.zIndex.toString() : undefined
                    }}
                >
                    <div className="common-modal-contents">
                        {props.children}
                    </div>
                </div>
                
            , document.body)}
        </>
    );
}
