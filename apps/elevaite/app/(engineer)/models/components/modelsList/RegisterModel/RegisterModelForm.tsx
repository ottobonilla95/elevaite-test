import type { CommonSelectOption} from "@repo/ui/components";
import { CommonButton, CommonFormLabels, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import "./RegisterModelForm.scss";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";






interface RegisterModelFormProps {
    onClose: () => void;
}

export function RegisterModelForm(props: RegisterModelFormProps): JSX.Element {
    const modelsContext = useModels();
    const [modelOptions, setModelOptions] = useState<CommonSelectOption[]>([]);
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);


    useEffect(() => {
        setModelOptions(formatModelOptions(modelsContext.modelTasks));
    }, [modelsContext.modelTasks]);

    
    function handleClose(): void {
        props.onClose();
    }

    function handleRegister(): void {
        console.log("registering")
    }


    function handleTaskChange(value: string): void {
        console.log("Selected task:", value);
    }

    function handleModelChange(value: string): void {
        console.log("Selected model:", value);
    }


    function formatModelOptions(tasks: string[]): CommonSelectOption[] {
        return tasks.map(item => { return  {
            label: item,
            value: item,
        }; })
    }


    return (
        <div className="register-model-form-container">

            <div className="register-header">
                <div className="register-title">
                    <div className="title-icon">
                        <ElevaiteIcons.SVGRegister/>
                    </div>
                    <span>Register Model</span>
                </div>
                <div className="close-button">                    
                    <CommonButton onClick={handleClose} noBackground>
                        <ElevaiteIcons.SVGXmark/>
                    </CommonButton>
                </div>
            </div>


            <div className="details-scroller">
                <div className="details-content">
                    <CommonFormLabels
                        label="Model Task"
                        info="Select model task to get a list of available model names"
                        required
                    >
                        <CommonSelect
                            options={modelOptions}
                            onSelectedValueChange={handleTaskChange}
                        />
                    </CommonFormLabels>

                    <div className="model-information">
                        <span>Model Information</span>


                        <CommonFormLabels
                            label="Model Name"
                            info="Select model to register"
                            required
                        >
                            <CommonSelect
                                options={[]}
                                onSelectedValueChange={handleModelChange}
                            />
                        </CommonFormLabels>
                    
                        <CommonFormLabels
                            label="Model Tags"
                        >
                            <div className="tags-container">
                                <div className="tag">Test Tag 1</div>
                                <div className="tag">Test Tag 2</div>
                            </div>
                        </CommonFormLabels>

                    </div>
                </div>
            </div>


            <div className="controls-container">
                <CommonButton
                    className="details-button"
                    onClick={handleClose}
                >
                    Cancel
                </CommonButton>
                <CommonButton
                    className="details-button submit"
                    disabled={isConfirmDisabled}
                    title={!isConfirmDisabled ? "" : "Mandatory fields (*) are missing"}
                    onClick={handleRegister}
                >
                    Register
                </CommonButton>
            </div>

        </div>
    );
}