"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, CommonInput, CommonSelect } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { getApplicationConfigurations } from "../../../../lib/actions";
import type { ApplicationConfigurationObject, Initializers } from "../../../../lib/interfaces";
import "./Configurations.scss";



const NO_CONFIGURATION = {label: "None", value: "0"};



interface ConfigurationsProps {
    applicationId: string | null;
    isConfigNameOpen: boolean;
    onCancel: () => void;
    onConfirm: (name: string, updateId?: string) => void;
    onSelectedConfigurationChange: (config: Initializers, configId: string) => void;
}

export function Configurations(props: ConfigurationsProps): JSX.Element {
    const [isLoading, setIsLoading] = useState(false);
    const [name, setName] = useState("");
    const [savedConfigurations, setSavedConfigurations] = useState<ApplicationConfigurationObject[]>([]);
    const [selectedConfiguration, setSelectedConfiguration] = useState<ApplicationConfigurationObject|undefined>();
    const [configurationOptions, setConfigurationOptions] = useState<CommonSelectOption[]>([NO_CONFIGURATION]);


    useEffect(() => {
        const sortedConfigurations = JSON.parse(JSON.stringify(savedConfigurations)) as ApplicationConfigurationObject[];
        sortedConfigurations.sort((a,b) => {
            if (a.updateDate && b.updateDate) return dayjs(a.updateDate).isBefore(b.updateDate) ? -1 : +1;
            return dayjs(a.createDate).isBefore(b.createDate) ? -1 : +1;
        })
        const configOptions = [NO_CONFIGURATION];
        configOptions.push(...savedConfigurations.map(item => { return {label: item.name ? item.name : "Unnamed Configuration", value: item.id}; }));
        
        setConfigurationOptions(configOptions);
    }, [savedConfigurations]);

    useEffect(() => {
        void (async () => {
            if (props.applicationId === null) return;
            await fetchConfigurations(props.applicationId);
        })();
    }, [props.applicationId]);


    async function fetchConfigurations(applicationId: string): Promise<void> {
        try {
            setIsLoading(true);
            const configList = await getApplicationConfigurations(applicationId);
            setSavedConfigurations(configList ? configList : []);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsLoading(false);
        }
    }

    function handleSelectedConfig(id: string): void {
        if (id === NO_CONFIGURATION.value) return;
        const config = savedConfigurations.find(item => item.id === id);
        if (!config) return;
        setSelectedConfiguration(config);

        props.onSelectedConfigurationChange(config.raw, id);
    }


    function handleCancel(): void {
        props.onCancel();
    }

    function handleConfirm(): void {
        props.onConfirm(name, selectedConfiguration && selectedConfiguration.name === name ? selectedConfiguration.id : undefined);
    }
    

    return (
        <div className="configurations-container">

            {!props.isConfigNameOpen ? null :
                <div className="configuration-name-dialog">
                    <div className="configuration-name-panel">
                        <CommonInput
                            initialValue={selectedConfiguration?.name}
                            label="Enter Configuration Name:"
                            onChange={setName}
                        />
                        <div className="configuration-notes">
                            Keep the name unchanged to update the selected configuration.
                        </div>
                        <div className="configuration-controls-container">
                            <CommonButton
                                className="config-button"
                                onClick={handleCancel}
                            >
                                Cancel
                            </CommonButton>
                            <CommonButton
                                className="config-button save"
                                onClick={handleConfirm}
                                disabled={!name.trim()}
                                title={!name.trim() ? "Missing name" : ""}
                            >
                                {selectedConfiguration?.name && selectedConfiguration.name === name ? "Update" : "Save"}
                            </CommonButton>
                        </div>
                    </div>
                </div>
            }

            <div className="configuration-selection-container">
                <span>Use existing configuration:</span>
                <CommonSelect
                    options={configurationOptions}
                    onSelectedValueChange={handleSelectedConfig}
                    defaultValue={NO_CONFIGURATION.value}
                    anchor="right"
                    showTitles
                    isLoading={isLoading}
                />
            </div>

        </div>
    );
}