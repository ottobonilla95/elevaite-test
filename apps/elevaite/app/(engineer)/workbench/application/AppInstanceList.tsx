"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import { useElapsedTime } from "@repo/ui/hooks";
import dayjs from "dayjs";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { getApplicationInstanceById, getApplicationInstanceList } from "../../../lib/actions";
import { AppInstanceObject, AppInstanceStatus, ApplicationType } from "../../../lib/interfaces";
import "./AppInstanceList.scss";



interface AppInstanceListProps {
    applicationId: string | null;
    applicationType?: ApplicationType;
    onSelectedInstanceChange: (instance: AppInstanceObject|undefined) => void;
    onSelectedFlowChange?: (flow: string) => void;
    onAddInstanceClick: () => void;
}

export default function AppInstanceList(props: AppInstanceListProps): JSX.Element {
    const session = useSession();
    const [isAllInstances, setIsAllInstances] = useState<boolean>(false);
    const [selectedInstance, setSelectedInstance] = useState<AppInstanceObject>();
    const [isLoading, setIsLoading] = useState(true);
    const [allInstances, setAllInstances] = useState<AppInstanceObject[]>([]);
    const [myInstances, setMyInstances] = useState<AppInstanceObject[]>([]);
    const [visibleInstances, setVisibleInstances] = useState<AppInstanceObject[]>([]);


    const instanceViewOptions: CommonSelectOption[] = [
        {label: "My Instances", value: "my"},
        {label: "All Instances", value: "all"}
    ];

    const flowOptions: CommonSelectOption[] = [
        {label: "Documents", value: "documents"},
        {label: "Threads", value: "threads"},
        {label: "Chat Channels", value: "chatChannels"},
        {label: "Forums", value: "forums"},
    ];


    useEffect(() => {
        void (async () => {
            try {
                if (!props.applicationId) return;
                const data = await getApplicationInstanceList(props.applicationId);
                initializeInstances(data);
                setIsLoading(false);
            } catch (error) {
                setIsLoading(false);
                console.error('Error fetching instances list:', error);
            }
        })();
    }, [props.applicationId]);

    useEffect(() => {
        assignVisibleInstances();
    }, [isAllInstances, allInstances, myInstances]);

    useEffect(() => {
        props.onSelectedInstanceChange(selectedInstance);
    }, [selectedInstance]);


    // Display Functions

    function initializeInstances(instances: AppInstanceObject[]): void {
        if (!instances) return;
        sortInstances(instances);
        const mine = instances.filter((instance) => { return instance.creator === (session?.data?.user?.name ?? "Unknown User"); });
        setAllInstances(instances);
        setMyInstances(mine);
    }

    function sortInstances(instances: AppInstanceObject[]): void {
        const sortingOrder = [AppInstanceStatus.STARTING, AppInstanceStatus.RUNNING, AppInstanceStatus.FAILED, AppInstanceStatus.COMPLETED];
        instances.sort((a, b) => dayjs(a.startTime).valueOf() - dayjs(b.startTime).valueOf() );
        instances.sort((a, b) => sortingOrder.indexOf(a.status) - sortingOrder.indexOf(b.status));
    }

    function assignVisibleInstances(): void {
        setVisibleInstances(isAllInstances ? allInstances : myInstances);
    }


    // Interaction Functions

    function handleAllInstanceViewChange(value: string): void {
        setIsAllInstances(value === "all");
        if (value === "all" && selectedInstance && selectedInstance.creator !== (session?.data?.user?.name ?? "Unknown User")) setSelectedInstance(undefined);
    }

    function handleFlowChange(value: string): void {
        if (props.onSelectedFlowChange) props.onSelectedFlowChange(value);
    }

    function handleInstanceClick(instance: AppInstanceObject): void {
        setSelectedInstance((currentInstance) => { return instance.id === currentInstance?.id ? undefined : instance; });
    }

    function handleInstanceUpdate(instance: AppInstanceObject): void {
        const index = allInstances.findIndex(item => item.id === instance.id);
        if (index >= 0) {
            allInstances[index] = instance;
            initializeInstances(allInstances);
        }
    }

    function handleAddInstance(): void {
        props.onAddInstanceClick();
    }



    return (
        <div className="app-instances-container">

            {!props.applicationType || props.applicationType !== ApplicationType.PREPROCESS ? null :
                <div className="app-flow-header">                    
                    <div className="flow-title">Pre-process Flow:</div>
                    <CommonSelect
                        className="flow-type"
                        defaultValue="documents"
                        onSelectedValueChange={handleFlowChange}
                        options={flowOptions}
                        anchor="right"
                    />
                </div>
            }
            
            <div className="app-instances-header">
                <div className="app-instances-title">APP INSTANCES</div>
                <CommonSelect
                    className="app-instances-type"
                    defaultValue="my"
                    onSelectedValueChange={handleAllInstanceViewChange}
                    options={instanceViewOptions}
                />
                <CommonButton className="add-instance" title="Add a new instance" onClick={handleAddInstance}>
                    <ElevaiteIcons.SVGCross/>
                </CommonButton>
            </div>

            <div className="app-instances-list">
                {isLoading ?
                    <div className="loading-container"><ElevaiteIcons.SVGSpinner/></div>
                    :
                    visibleInstances.length === 0 ? 
                        <div className="list-message">There are no active instances.</div>
                    : visibleInstances.map((instance) => 
                    <AppInstance
                        key={instance.id}
                        applicationId={props.applicationId}
                        {...instance}
                        isSelected={selectedInstance?.id === instance.id}
                        onClick={handleInstanceClick}
                        onInstanceUpdate={handleInstanceUpdate}
                    />
                )}
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
}

function AppInstance({isHidden, isSelected, onClick, ...props}: AppInstanceProps): JSX.Element {
    const {elapsedTime} = useElapsedTime(props.startTime, props.endTime);


    useEffect(() => {
        if (props.applicationId && props.id && props.onInstanceUpdate && props.status === AppInstanceStatus.RUNNING || props.status === AppInstanceStatus.STARTING) {
            const delay = props.status === AppInstanceStatus.STARTING ? 20000 : 5000;
            const interval = setInterval(() => {
                fetchInstance(props.applicationId, props.id, props.status);
            }, delay);
            return () => {clearInterval(interval)};
        }
    }, [props.id]);


    async function fetchInstance(applicationId?: string | null, instanceId?: string, status?: AppInstanceStatus): Promise<void> {
        if (!applicationId || !instanceId || !status) return;
        
        try {            
            const data = await getApplicationInstanceById(applicationId, instanceId);
            if (data && data.status && data.status !== status && props.onInstanceUpdate) {
                props.onInstanceUpdate(data);
            }
        } catch (error) {
            // We ignore such errors silently.
        }
    }




    function getRelevantIcon(): JSX.Element {
        switch (props.status) {
            case AppInstanceStatus.STARTING: return <ElevaiteIcons.SVGTarget className="app-instance-icon starting" />
            case AppInstanceStatus.RUNNING: return <ElevaiteIcons.SVGInstanceProgress className="app-instance-icon ongoing" />
            case AppInstanceStatus.COMPLETED: return <ElevaiteIcons.SVGCheckmark className="app-instance-icon completed" />
            case AppInstanceStatus.FAILED: return <ElevaiteIcons.SVGTarget className="app-instance-icon failed" />
        }
    }

    function getRelevantInfo(): string {
        switch (props.status) {
            case AppInstanceStatus.STARTING: return "The instance is initializing."
            case AppInstanceStatus.RUNNING: return "The instance is running. Thank you for your patience."
            case AppInstanceStatus.COMPLETED: return "The instance has been processed succesfully."
            case AppInstanceStatus.FAILED: return "The instance has encountered an error."
        }
    }


    return (
        <CommonButton
            className={[
                "app-instance",
                isHidden ? "hidden" : undefined,
                isSelected ? "selected" : undefined,
            ].filter(Boolean).join(" ")}
            onClick={() => { onClick(props); }}
            overrideClass
            noBackground={!isSelected}
        >
            <div title={getRelevantInfo()}>
                {getRelevantIcon()}
            </div>
            <div className="app-instance-label">{props.id}</div>
            <div className="app-instance-elapsed-time">{elapsedTime}</div>            
        </CommonButton>
    );
}