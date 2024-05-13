import type { CommonSelectOption } from "@repo/ui/components";
import { AdvancedSelectOption, CommonButton, CommonFormLabels, CommonInput, CommonSelect, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
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
    const [name, setName] = useState("");
    const [searchName, setSearchName] = useState("");
    const [currentTag, setCurrentTag] = useState("");
    const [tags, setTags] = useState<string[]>([]);
    const [readyToClose, setReadyToClose] = useState(false);


    
    useEffect(() => {
        setModelOptions(formatModelOptions(modelsContext.modelTasks));
    }, [modelsContext.modelTasks]);

    useEffect(() => {
        setAvailableModelOptions(formatAvailableModelOptions(modelsContext.availableModels));
    }, [modelsContext.availableModels]);

    useEffect(() => {
        if (modelsContext.loading.registerModel) {
            setReadyToClose(true);
        } else if (readyToClose) props.onClose();
    }, [modelsContext.loading.registerModel]);

    useEffect(() => {
        let defaultName = "";
        if (selectedAvailableModel) {
            const defaultNameList = selectedAvailableModel.id.split("/");
            if (defaultNameList.length > 1) {
                const lastItem = defaultNameList.at(-1);
                defaultName = lastItem ? lastItem : "";
            }
        } else defaultName = "";
        setName(defaultName);
    }, [selectedAvailableModel]);

    useEffect(() => {
        const delayInputTimeoutId = setTimeout(() => {
            searchForAvailableModelsByName(searchName);
        }, 500);
        return () => { clearTimeout(delayInputTimeoutId); };
    }, [searchName, 500]);

    



    function handleClose(): void {
        props.onClose();
    }

    function searchForAvailableModelsByName(searchTerm: string|undefined): void {
        if (!searchTerm) return;
        modelsContext.getAvailableRemoteModelsByName(searchTerm);
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
        if (!name || !selectedAvailableModel) return;
        void modelsContext.registerModel(name, selectedAvailableModel.id, tags);
    }

    function handleKeyDown(key: string): void {
        if (key !== "Enter" || !currentTag) return;
        if (!tags.includes(currentTag)) {
            const newTags = [...tags, currentTag].sort();
            setTags(newTags);
        }
        setCurrentTag("");
    }

    function removeTag(tag: string): void {
        if (!tags.includes(tag)) return;
        const newTags = tags.filter(item => item !== tag);
        setTags(newTags);
    }

    function formatModelOptions(tasks: string[]): CommonSelectOption[] {
        return tasks.map(item => { return  {
            label: item,
            value: item,
        }; })
    }

    function formatAvailableModelOptions(availableModels: AvailableModelObject[]): CommonSelectOption[] {
        return availableModels.map(item => { return {
            label: item.id, //getAvailableModelLabel(item),
            value: item.id,
            extras: {
                postfix: { label: item.gated ? "gated" :"not gated" },
                footer: !item.memory_requirements ? undefined : [
                    { label: item.memory_requirements.total_size.value_str, tooltip: "Size to download" },
                    { label: item.memory_requirements.training_using_adam.value_str, tooltip: "Size to train" },
                ]
            }
        }});
    }


    return (
        <div className="register-model-form-container">

            {!modelsContext.loading.registerModel ? undefined :
                <div className="register-loading">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            } 

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



                    <CommonInput
                        label="Search by Repository Name"
                        controlledValue={searchName}
                        onChange={setSearchName}
                        info="Repository name (also known as model id)"
                    />

                    <CommonFormLabels
                        label="Or search by Model Task"
                        info="Select model task to get a list of available model names"
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
                            label="Model Repository"
                            info="Select model to register"
                            required
                        >
                            <CommonSelect
                                key={selectedModelTask}
                                options={availableModelOptions}
                                noSelectionMessage={selectedModelTask || (searchName && availableModelOptions.length > 0) ? "No selected model" : "Search for a model or select a model task"}
                                disabled={!selectedModelTask && !searchName}
                                isLoading={modelsContext.loading.availableModels}
                                onSelectedValueChange={handleModelChange}
                                AdvancedOptionComponent={AdvancedSelectOption}
                            />
                        </CommonFormLabels>

                        <CommonInput
                            label="Model Name"
                            controlledValue={name}
                            onChange={setName}
                            info="A name to reference the registered model"
                            required
                        />
                    
                        <CommonFormLabels
                            label="Model Tags"
                            info="Add any tags to append to the model when registering"
                        >
                            <div className="tags-container">
                                {tags.map(tag => 
                                    <div key={tag} className="tag">
                                        <span>{tag}</span>
                                        <CommonButton
                                            onClick={() => { removeTag(tag); }}
                                            noBackground
                                        >
                                            <ElevaiteIcons.SVGXmark/>
                                        </CommonButton>
                                    </div>
                                )}
                                <SimpleInput
                                    value={currentTag}
                                    onChange={setCurrentTag}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Type tag and press enter"
                                />
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
                    disabled={!selectedAvailableModel || !name}
                    title={selectedAvailableModel && name ? "" : "Mandatory fields (*) are missing"}
                    onClick={handleRegister}
                >
                    Register
                </CommonButton>
            </div>

        </div>
    );
}