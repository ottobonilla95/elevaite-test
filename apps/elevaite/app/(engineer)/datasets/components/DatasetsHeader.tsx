"use client";
import { useState } from "react";
import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import "./DatasetsHeader.scss";
import { DownloadDatasetForm } from "./datasetsList/DownloadDataset/DownloadDatasetForm";




export function DatasetsHeader(): JSX.Element {
    const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false);


    function handleDownloadModal():void {
        setIsDownloadModalOpen(true);
    }

    function handleCloseDownloadModal(): void {
        setIsDownloadModalOpen(false);
    }

    return (
        <div className="datasets-header-container">

            <div className="part-container left">
                <div className="title">DATASETS</div>
            </div>

            <div className="part-container right">
                <CommonButton
                    className="register-button"
                    onClick={handleDownloadModal}
                >
                    <ElevaiteIcons.SVGRegister/>
                    Register Dataset from Hugging Face
                </CommonButton>
            </div>

            {!isDownloadModalOpen ? null :
                <CommonModal onClose={handleCloseDownloadModal}>
                    <DownloadDatasetForm onClose={handleCloseDownloadModal}/>
                </CommonModal>
            }

        </div>
    );
}