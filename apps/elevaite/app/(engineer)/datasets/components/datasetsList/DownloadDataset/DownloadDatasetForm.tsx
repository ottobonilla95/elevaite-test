"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, CommonFormLabels, CommonInput, CommonSelect, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useDatasets } from "../../../../../lib/contexts/DatasetsContext";
import type { HuggingfaceDatasetObject } from "../../../../../lib/interfaces";
import "./DownloadDatasetForm.scss";






interface DownloadDatasetFormProps {
    onClose: () => void;
}

export function DownloadDatasetForm(props: DownloadDatasetFormProps): JSX.Element {
    const datasetContext = useDatasets();
    const [datasetOptions, setDatasetOptions] = useState<CommonSelectOption[]>([]);
    const [selectedDatasetTask, setSelectedDatasetTask] = useState("");
    const [availableDatasetOptions, setAvailableDatasetOptions] = useState<CommonSelectOption[]>([]);
    const [selectedAvailableDataset, setSelectedAvailableDataset] = useState<HuggingfaceDatasetObject|undefined>();
    const [name, setName] = useState("");
    const [searchName, setSearchName] = useState("");
    const [currentTag, setCurrentTag] = useState("");
    const [tags, setTags] = useState<string[]>([]);
    const [readyToClose, setReadyToClose] = useState(false);

    
    useEffect(() => {
        setDatasetOptions(formatDatasetOptions(datasetContext.datasetTasks));
    }, [datasetContext.datasetTasks]);

    useEffect(() => {
        setAvailableDatasetOptions(formatAvailableDatasetOptions(datasetContext.availableDatasets));
    }, [datasetContext.availableDatasets]);

    useEffect(() => {
        if (datasetContext.loading.registerDataset) {
            setReadyToClose(true);
        } else if (readyToClose) props.onClose();
    }, [datasetContext.loading.registerDataset]);

    useEffect(() => {
        let defaultName = "";
        if (selectedAvailableDataset) {
            const defaultNameList = selectedAvailableDataset.id.split("/");
            if (defaultNameList.length >= 1) {
                const lastItem = defaultNameList.at(-1);
                defaultName = lastItem ? lastItem : "";
            }
        } else defaultName = "";
        setName(defaultName);
    }, [selectedAvailableDataset]);

    useEffect(() => {
        const delayInputTimeoutId = setTimeout(() => {
            searchForAvailableDatasetsByName(searchName);
        }, 500);
        return () => { clearTimeout(delayInputTimeoutId); };
    }, [searchName, 500]);

    



    function handleClose(): void {
        props.onClose();
    }

    function searchForAvailableDatasetsByName(searchTerm: string|undefined): void {
        if (!searchTerm) return;
        datasetContext.getAvailableDatasetsByName(searchTerm);
    }

    function handleTaskChange(value: string): void {
        setSelectedDatasetTask(value);
        setSelectedAvailableDataset(undefined);
        datasetContext.getAvailableDatasetsByTask(value);
    }

    function handleDatasetChange(value: string): void {
        const selected = datasetContext.availableDatasets.find(item => item.id === value);
        if (selected) setSelectedAvailableDataset(selected);
        else setSelectedAvailableDataset(undefined);
    }

    function handleRegister(): void {
        if (!name || !selectedAvailableDataset) return;
        void datasetContext.registerDataset(name, selectedAvailableDataset.id, tags);
    }

    function handleKeyDown(key: string): void {
        if (key !== "Enter") return;
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

    function formatDatasetOptions(tasks: string[]): CommonSelectOption[] {
        return tasks.map(item => { return  {
            label: item,
            value: item,
        }; })
    }

    function formatAvailableDatasetOptions(availableDatasets: HuggingfaceDatasetObject[]): CommonSelectOption[] {
        return availableDatasets.map(item => { return {
            label: getAvailableDatasetLabel(item),
            value: item.id,
        }; })

        function getAvailableDatasetLabel(dataset: HuggingfaceDatasetObject): string {
            let label = dataset.id;
            label = `${label} (${dataset.gated ? "gated" :"not gated"}`;
            label = `${label})`;
            return label;
        }
    }


    return (
        <div className="download-dataset-form-container">

            {!datasetContext.loading.registerDataset ? undefined :
                <div className="download-loading">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            } 

            <div className="download-header">
                <div className="download-title">
                    <div className="title-icon">
                        <ElevaiteIcons.SVGRegister/>
                    </div>
                    <span>Register Dataset</span>
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
                        info="Repository name (also known as dataset id)"
                    />

                    <CommonFormLabels
                        label="Or search by Dataset Task"
                        info="Select dataset task to get a list of available dataset names"
                    >
                        <CommonSelect
                            options={datasetOptions}
                            onSelectedValueChange={handleTaskChange}
                            isLoading={datasetContext.loading.datasetTasks}
                        />
                    </CommonFormLabels>


                    <div className="dataset-information">
                        <span>Dataset Information</span>

                        <CommonFormLabels
                            label="Dataset Repository"
                            info="Select dataset to register"
                            required
                        >
                            <CommonSelect
                                key={selectedDatasetTask}
                                options={availableDatasetOptions}
                                noSelectionMessage={selectedDatasetTask || (searchName && availableDatasetOptions.length > 0) ? "No selected dataset" : "Search for a dataset or select a dataset task"}
                                disabled={!selectedDatasetTask && !searchName}
                                isLoading={datasetContext.loading.availableDatasets}
                                onSelectedValueChange={handleDatasetChange}
                            />
                        </CommonFormLabels>

                        <CommonInput
                            label="Dataset Name"
                            controlledValue={name}
                            onChange={setName}
                            info="A name to reference the downloaded dataset"
                            required
                        />
                    
                        <CommonFormLabels
                            label="Dataset Tags"
                            info="Add any tags to append to the dataset when downloaded"
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
                    disabled={!selectedAvailableDataset || !name}
                    title={selectedAvailableDataset && name ? "" : "Mandatory fields (*) are missing"}
                    onClick={handleRegister}
                >
                    Download
                </CommonButton>
            </div>

        </div>
    );
}