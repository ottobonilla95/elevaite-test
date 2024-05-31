"use client";
import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsHeader.scss";
import { useState } from "react";
import { RegisterModelForm } from "./modelsList/RegisterModel/RegisterModelForm";




export function ModelsHeader(): JSX.Element {
    const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);


    function handleOpenRegisterModal():void {
        setIsRegisterModalOpen(true);
    }

    function handleCloseRegisterModal(): void {
        setIsRegisterModalOpen(false);
    }

    return (
        <div className="models-header-container">

            <div className="part-container left">
                <div className="title">MODELS</div>
            </div>

            <div className="part-container right">
                <CommonButton
                    className="register-button"
                    onClick={handleOpenRegisterModal}
                >
                    <ElevaiteIcons.SVGRegister/>
                    Register Model
                </CommonButton>
            </div>

            {!isRegisterModalOpen ? null :
                <CommonModal onClose={handleCloseRegisterModal}>
                    <RegisterModelForm onClose={handleCloseRegisterModal}/>
                </CommonModal>
            }

        </div>
    );
}