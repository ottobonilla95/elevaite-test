import { CommonButton, CommonFormLabels, CommonInput, CommonSelect, type CommonSelectOption, ElevaiteIcons } from "@repo/ui/components";
import { useRef, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { CONTRACT_TYPES, CONTRACTS_TABS } from "../../../lib/interfaces";
import "./ContractUpload.scss";



const contractTypesOptions: CommonSelectOption[] = [
    { label: "VSOW", value: CONTRACT_TYPES.VSOW },
    { label: "CSOW", value: CONTRACT_TYPES.CSOW, disabled: true },
    { label: "Invoice", value: CONTRACT_TYPES.INVOICE },
    { label: "Purchase Order", value: CONTRACT_TYPES.PURCHASE_ORDER },    
];




interface ContractUploadProps {
    selectedTab: CONTRACTS_TABS;
    onClose: () => void;
}

export function ContractUpload(props: ContractUploadProps): JSX.Element {
    const contractsContext = useContracts();
    const hiddenFileInput = useRef<HTMLInputElement|null>(null);
    const [uploadingFile, setUploadingFile] = useState<File|undefined>();
    const [name, setName] = useState("");
    const [pdfType, setPdfType] = useState<CONTRACT_TYPES>();


    function handleCloseModal(): void {
        props.onClose();
    }

    function handleContractTypeChange(newType: CONTRACT_TYPES): void {
        setPdfType(newType);
    }

    function handleUpload(): void {
        hiddenFileInput.current?.click();
    }

    function handleFileChange(event: React.ChangeEvent<HTMLInputElement>): void {
        if (event.target.files?.[0])
            setUploadingFile(event.target.files[0]);
        else setUploadingFile(undefined);
    }

    function handleSubmit(): void {
        if (!uploadingFile || !pdfType || !contractsContext.selectedProject?.id) return;
        contractsContext.submitCurrentContractPdf(uploadingFile, pdfType, contractsContext.selectedProject.id, name);
        props.onClose();
    }

    return (
        <div className="contract-upload-container">
            <div className="contract-upload-header">
                <div className="contract-upload-title">
                    <span>Upload</span>
                </div>
                <div className="close-button">                    
                    <CommonButton onClick={handleCloseModal} noBackground>
                        <ElevaiteIcons.SVGXmark/>
                    </CommonButton>
                </div>
            </div>

            <div className="top-row">

                <CommonInput
                    label="Name"
                    onChange={setName}                    
                />

                <CommonFormLabels
                    label="Choose File Type"
                    required
                >
                    <CommonSelect
                        options={contractTypesOptions}
                        onSelectedValueChange={handleContractTypeChange}
                        defaultValue={props.selectedTab === CONTRACTS_TABS.SUPPLIER_INVOICES ? CONTRACT_TYPES.INVOICE :
                                        props.selectedTab === CONTRACTS_TABS.SUPPLIER_POS ? CONTRACT_TYPES.PURCHASE_ORDER : 
                                        props.selectedTab === CONTRACTS_TABS.CUSTOMER_CONTRACTS ? undefined : // CONTRACT_TYPES.CSOW :
                                        CONTRACT_TYPES.VSOW
                        }
                        callbackOnDefaultValue
                    />
                </CommonFormLabels>

            </div>

            <div className="drag-field">

                <div className="upload-controls">
                    <div className="upload-icon">
                        <ElevaiteIcons.SVGCloudUpload/>
                    </div>
                    <input
                        ref={hiddenFileInput}
                        className="hidden-input"
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                    />
                    <CommonButton
                        className="upload-button"
                        onClick={handleUpload}
                    >
                        Upload
                    </CommonButton>
                    <span>or drag and drop your file</span>
                </div>

            </div>

            <div className="submit-controls">

                <div className="submit-file-name" title={uploadingFile?.name ?? ""}>
                    {uploadingFile?.name}
                </div>

                <CommonButton
                    className="submit-button"
                    onClick={handleSubmit}
                    disabled={!pdfType || !uploadingFile}
                >
                    Submit
                </CommonButton>

            </div>

        </div>
    );
}