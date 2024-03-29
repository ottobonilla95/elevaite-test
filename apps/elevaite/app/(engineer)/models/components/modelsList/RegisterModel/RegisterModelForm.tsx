import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, CommonFormLabels, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import type { AvailableModelObject } from "../../../../../lib/interfaces";
import "./RegisterModelForm.scss";






interface RegisterModelFormProps {
    onClose: () => void;
}

export function RegisterModelForm(props: RegisterModelFormProps): JSX.Element {
    const modelsContext = useModels();
    const [modelOptions, setModelOptions] = useState<CommonSelectOption[]>([]);
    const [selectedModelTask, setSelectedModelTask] = useState("");
    const [availableModelOptions, setAvailableModelOptions] = useState<CommonSelectOption[]>([]);
    const [selectedAvailableModel, setSelectedAvailableModel] = useState<AvailableModelObject|undefined>();
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);


    useEffect(() => {
        setModelOptions(formatModelOptions(modelsContext.modelTasks));
    }, [modelsContext.modelTasks]);

    useEffect(() => {
        setAvailableModelOptions(formatAvailableModelOptions(modelsContext.availableModels));
    }, [modelsContext.availableModels]);


    
    function handleClose(): void {
        props.onClose();
    }

    function handleTaskChange(value: string): void {
        setSelectedModelTask(value);
        setSelectedAvailableModel(undefined);
        modelsContext.getAvailableRemoteModels(value);
    }

    function handleModelChange(value: string): void {
        const selected = modelsContext.availableModels.find(item => item.id === value);
        if (selected) setSelectedAvailableModel(selected);
        else setSelectedAvailableModel(undefined);
    }

    function handleRegister(): void {
        console.log("Registering", selectedAvailableModel);
    }


    function formatModelOptions(tasks: string[]): CommonSelectOption[] {
        return tasks.map(item => { return  {
            label: item,
            value: item,
        }; })
    }

    function formatAvailableModelOptions(availableModels: AvailableModelObject[]): CommonSelectOption[] {
        return availableModels.map(item => { return {
            label: getAvailableModelLabel(item),
            value: item.id,
        }; })

        function getAvailableModelLabel(model: AvailableModelObject): string {
            let label = model.id;
            label = `${label} (${model.gated ? "gated" :"not gated"}`;
            if (model.memory_requirements) {
                label = `${label} / ${model.memory_requirements.float32.total_size.value_str}`;
                label = `${label} / ${model.memory_requirements.float32.training_using_adam.value_str}`;
            }
            label = `${label})`;
            return label;
        }
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
                            isLoading={modelsContext.loading.modelTasks}
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
                                key={selectedModelTask}
                                options={availableModelOptions}
                                noSelectionMessage={selectedModelTask ? "No selected model" : "Please select a model task"}
                                disabled={!selectedModelTask}
                                isLoading={modelsContext.loading.availableModels}
                                onSelectedValueChange={handleModelChange}
                            />
                        </CommonFormLabels>
                    
                        <CommonFormLabels
                            label="Model Tags"
                        >
                            <div className="tags-container">
                                {/* <div className="tag">Test Tag 1</div>
                                <div className="tag">Test Tag 2</div> */}
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
                    disabled={!selectedAvailableModel}
                    title={selectedAvailableModel ? "" : "Mandatory fields (*) are missing"}
                    onClick={handleRegister}
                >
                    Register
                </CommonButton>
            </div>

        </div>
    );
}