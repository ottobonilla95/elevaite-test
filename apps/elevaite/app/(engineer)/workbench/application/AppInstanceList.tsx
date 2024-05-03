"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { ClickOutsideDetector, CommonButton, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import { useElapsedTime } from "@repo/ui/hooks";
import dayjs from "dayjs";
import { useSession } from "next-auth/react";
import { useEffect, useRef, useState } from "react";
import { getApplicationInstanceById, getApplicationInstanceList } from "../../../lib/actions/applicationActions";
import type { AppInstanceConfigurationObject, AppInstanceObject, PipelineObject } from "../../../lib/interfaces";
import { AppInstanceStatus } from "../../../lib/interfaces";
import type { AppInstanceFiltersObject } from "./AppInstanceFilters";
import { AppInstanceFilters, ScopeInstances, SortingInstances, initialFilters } from "./AppInstanceFilters";
import "./AppInstanceList.scss";



interface AppInstanceListProps {
    applicationId: string | null;
    pipelines?: PipelineObject[];
    onSelectedInstanceChange: (instance: AppInstanceObject|undefined) => void;
    onSelectedFlowChange?: (flowValue: string, flowLabel: string) => void;
    onAddInstanceClick: () => void;
    addId?: string;
    onClearAddId?: (id: string) => void;
    onConfigClone?: (config: AppInstanceConfigurationObject|undefined) => void;
}

export default function AppInstanceList(props: AppInstanceListProps): JSX.Element {
    const session = useSession();
    const [isLoading, setIsLoading] = useState(true);
    const [selectedInstance, setSelectedInstance] = useState<AppInstanceObject>();
    const [allInstances, setAllInstances] = useState<AppInstanceObject[]>([]);
    const [visibleInstances, setVisibleInstances] = useState<AppInstanceObject[]>([]);
    const [filters, setFilters] = useState<AppInstanceFiltersObject>(initialFilters);
    const [flowOptions, setFlowOptions] = useState<CommonSelectOption[]>();
    const [selectedFlowId, setSelectedFlowId] = useState("");



    useEffect(() => {
        void (async () => {
            try {
                if (!props.applicationId) return;
                const data = await getApplicationInstanceList(props.applicationId);
                initializeInstances(data);
            } catch (error) {
                // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
                console.error('Error fetching instances list:', error);
            } finally {
                setIsLoading(false);
            }
        })();
    }, [props.applicationId]);

    useEffect(() => {
        if (!props.pipelines || props.pipelines.length === 0) return;
        initializePipelines(props.pipelines);
    }, [props.pipelines]);

    useEffect(() => {
        assignVisibleInstances();
    }, [allInstances, filters, selectedFlowId]);

    useEffect(() => {
        // console.log("selected instance", selectedInstance);
        props.onSelectedInstanceChange(selectedInstance);
    }, [selectedInstance]);

    useEffect(() => {
        if (props.addId) {
            void fetchAddedInstance(props.addId);
        }
    }, [props.addId]);


    // Data Functions

    async function fetchAddedInstance(id: string): Promise<void> {
        if (!props.applicationId || !id) return;
        try {
            const data = await getApplicationInstanceById(props.applicationId, id);
            handleInstanceUpdate(data);
            if (props.onClearAddId) props.onClearAddId(id);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error('Error fetching added instance:', error);
        }
    }



    // Display Functions

    function initializeInstances(instances: AppInstanceObject[]): void {
        setAllInstances(instances);
    }

    function initializePipelines(pipelines: PipelineObject[]): void {
        const flow = pipelines.map(pipeline => {
            return {
                label: pipeline.label,
                value: pipeline.id,
            }
        });
        if (flow.length > 0) handleFlowChange(flow[0].value, flow[0].label);
        setFlowOptions(flow);
    }

    function sortInstances(instances: AppInstanceObject[]): void {
        const sortingOrder = [AppInstanceStatus.STARTING, AppInstanceStatus.RUNNING, AppInstanceStatus.FAILED, AppInstanceStatus.COMPLETED];
        instances.sort((a, b) => dayjs(a.startTime).valueOf() - dayjs(b.startTime).valueOf() );
        if (filters.sorting === SortingInstances.Descending) instances.reverse();
        instances.sort((a, b) => sortingOrder.indexOf(a.status) - sortingOrder.indexOf(b.status));
    }

    function assignVisibleInstances(): void {
        const filteredInstances = [...allInstances].filter(instance => {
            // Check scope
            if (filters.scope === ScopeInstances.AllInstances ||
                // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- This does not convert to ?? without issues. Leave it as it is.
                (session.data?.user?.name && instance.creator === session.data.user.name) ||
                (!session.data?.user?.name && instance.creator === "Unknown User")) {
                // Check Flow
                if (!selectedFlowId || props.applicationId === "1" || instance.selectedPipelineId === selectedFlowId) {
                    // Check status
                    if (Object.values(filters.showStatus).every(item => !item) || filters.showStatus[instance.status]) {
                        // Check search term
                        if (!filters.searchTerm ||
                            instance.id.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
                            (instance.name?.toLowerCase().includes(filters.searchTerm.toLowerCase()))
                        ) {
                            return instance;
                        }
                    }
                }
            }
            return false;
        });
        sortInstances(filteredInstances);
        setVisibleInstances(filteredInstances);
    }

    function getFlowLabel(id: string|null): string {
        switch (id) {
          case "1": return "Ingest";
          case "2": return "Pre-process";
          default: return "";
        }
    }


    // Interaction Functions
    
    function handleFlowChange(value: string, label: string): void {
        setSelectedFlowId(value);
        if (props.onSelectedFlowChange) props.onSelectedFlowChange(value, label);
    }

    function handleInstanceClick(instance: AppInstanceObject): void {
        setSelectedInstance((currentInstance) => { return instance.id === currentInstance?.id ? undefined : instance; });
    }

    function handleInstanceUpdate(instance: AppInstanceObject): void {
        if (allInstances.some(item => item.id === instance.id)) {
            initializeInstances(allInstances.map(item => item.id === instance.id ? instance : item));
        } else {
            initializeInstances([...allInstances, instance]);
        }
    }

    function handleAddInstance(): void {
        props.onAddInstanceClick();
    }

    function handleConfigClone(config: AppInstanceConfigurationObject|undefined): void {
        if (props.onConfigClone) props.onConfigClone(config);
    }



    return (
        <div className="app-instances-container">

            {props.applicationId === "1" ? null : // Hide it if Ingest
            !flowOptions || flowOptions.length === 0 ? null :
                <div className="app-flow-header">                    
                    <div className="flow-title">{`${getFlowLabel(props.applicationId)} Flow:`}</div>
                    <CommonSelect
                        className="flow-type"
                        defaultValue={flowOptions[0].value}
                        onSelectedValueChange={handleFlowChange}
                        options={flowOptions}
                        anchor="right"
                    />
                </div>
            }
            
            <div className="app-instances-header">
                <div className="app-instances-title">APP INSTANCES</div>
                <CommonButton className="add-instance" title="Add a new instance" onClick={handleAddInstance}>
                    <span>Create New Instance</span>
                    <ElevaiteIcons.SVGCross circled />
                </CommonButton>
            </div>

            <AppInstanceFilters
                onFiltersChanged={setFilters}
            />

            <div className="app-instances-scroller">
                <div className="app-instances-list">
                    {isLoading ?
                        <div className="loading-container"><ElevaiteIcons.SVGSpinner/></div>
                        :
                        visibleInstances.length === 0 ? 
                            <div className="list-message">No instances to display.</div>
                        : visibleInstances.map((instance) => 
                        <AppInstance
                            key={instance.id}
                            applicationId={props.applicationId}
                            {...instance}
                            isSelected={selectedInstance?.id === instance.id}
                            onClick={handleInstanceClick}
                            onInstanceUpdate={handleInstanceUpdate}
                            onConfigClone={handleConfigClone}
                        />
                    )}
                </div>
            </div>

        </div>
    );
}







interface AppInstanceProps extends AppInstanceObject {
    applicationId: string | null,
    isHidden?: boolean,
    isSelected?: boolean,
    onClick: (instance: AppInstanceObject) => void;
    onInstanceUpdate?: (instance: AppInstanceObject) => void;
    onConfigClone?: (config: AppInstanceConfigurationObject|undefined) => void;
}

function AppInstance({isHidden, isSelected, onClick, ...props}: AppInstanceProps): JSX.Element {    
    const menuButtonRef = useRef<HTMLButtonElement|null>(null);
    const {elapsedTime} = useElapsedTime(props.startTime, props.endTime);
    const [icon, setIcon] = useState<JSX.Element>(<div/>)
    const [tooltips, setTooltips] = useState({ icon: "", time: "" });
    const [isMenuOpen, setIsMenuOpen] = useState(false);


    useEffect(() => {
        if (props.applicationId && props.id && props.onInstanceUpdate &&
            !props.id.toLowerCase().includes("test") && // Prevent test instances from attempting to refresh.
            (props.status === AppInstanceStatus.RUNNING || props.status === AppInstanceStatus.STARTING)) {
            const delay = props.status === AppInstanceStatus.STARTING ? 2000 : 5000;
            const interval = setInterval(() => {
                void fetchInstance(props.applicationId, props.id, props.status);
            }, delay);
            return () => {clearInterval(interval)};
        }
    }, [props.id]);

    useEffect(() => {
        setIcon(getIcon());
        setTooltips({
            icon: getIconTooltip(),
            time: getTimeTooltip(),
        })
    }, [props.status]);


    function handleConfigurationClone(): void {
        setIsMenuOpen(false);
        if (props.onConfigClone) props.onConfigClone(props.configuration);
    }


    async function fetchInstance(applicationId?: string | null, instanceId?: string, status?: AppInstanceStatus): Promise<void> {
        if (!applicationId || !instanceId || !status) return;
        
        try {            
            const data = await getApplicationInstanceById(applicationId, instanceId);
            if (data.status !== status && props.onInstanceUpdate) {
                props.onInstanceUpdate(data);
            }
        } catch (error) {
            // We ignore such errors silently.
        }
    }

    function getIcon(): JSX.Element {
        switch (props.status) {
            case AppInstanceStatus.STARTING: return <ElevaiteIcons.SVGTarget className="app-instance-icon starting" />
            case AppInstanceStatus.RUNNING: return <ElevaiteIcons.SVGInstanceProgress className="app-instance-icon ongoing" />
            case AppInstanceStatus.COMPLETED: return <ElevaiteIcons.SVGCheckmark className="app-instance-icon completed" />
            case AppInstanceStatus.FAILED: return <ElevaiteIcons.SVGWarning className="app-instance-icon failed" />
        }
    }
    function getIconTooltip(): string {
        switch (props.status) {
            case AppInstanceStatus.STARTING: return "The instance is initializing."
            case AppInstanceStatus.RUNNING: return "The instance is running. Thank you for your patience."
            case AppInstanceStatus.COMPLETED: return "The instance has been processed succesfully."
            case AppInstanceStatus.FAILED: return "The instance has encountered an error."
        }
    }    
    function getTimeTooltip(): string {
        const formatting = "DD MMM, hh:mm a";
        if (!props.startTime) return "";
        let tooltip = `Initialized on: ${dayjs(props.startTime).format(formatting)}`;
        if (props.endTime) {
            tooltip += `\n${props.status === AppInstanceStatus.FAILED ? "Failed on" : "Completed on"}: ${dayjs(props.endTime).format(formatting)}`;
        }
        return tooltip;
    }



    return (
        <div
            className={[
                "app-instance",
                isHidden ? "hidden" : undefined,
                isSelected ? "selected" : undefined,
            ].filter(Boolean).join(" ")}
        >
            <CommonButton
                className="app-instance-main-button"
                onClick={() => { onClick(props); }}
                overrideClass
                noBackground={!isSelected}
            >
                <div title={tooltips.icon}>{icon}</div>
                <div className="app-instance-label" title={props.name ? props.id : ""}>{props.name ? props.name : props.id}</div>
                <div className="app-instance-elapsed-time" title={tooltips.time}>{elapsedTime}</div>
            </CommonButton>
            <div className="app-instance-menu-button">
                <CommonButton
                    onClick={() => { setIsMenuOpen(true); }}
                    passedRef={menuButtonRef}
                    noBackground
                >
                    <ElevaiteIcons.SVGMenuDots/>
                </CommonButton>
            </div>

            
            <ClickOutsideDetector onOutsideClick={() => { setIsMenuOpen(false); }} ignoredRefs={[menuButtonRef]}>
                <div className={["app-instance-menu-container", isMenuOpen ? "open" : undefined].filter(Boolean).join(" ")}>
                    <CommonButton
                        onClick={handleConfigurationClone}
                        noBackground
                    >
                        Clone Configuration
                    </CommonButton>
                </div>
            </ClickOutsideDetector>

        </div>
    );
}