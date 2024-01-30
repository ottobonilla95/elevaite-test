"use client";
import { useEffect, useState } from "react";
import "./AppInstanceList.scss";
import type { CommonSelectOption} from "@repo/ui/components";
import { CommonButton, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import { useElapsedTime } from "@repo/ui/hooks";
import { AppInstanceObject, AppInstanceStatus, ApplicationType } from "../../../lib/interfaces";
import { useSession } from "next-auth/react";
import { getApplicationInstanceList } from "../../../lib/actions";
import dayjs from "dayjs";



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
    const [allInstances, setAllInstances] = useState<AppInstanceObject[]>();
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
                setAllInstances(data);
                setIsLoading(false);
            } catch (error) {
                setIsLoading(false);
                console.error('Error fetching instances list:', error);
            }
        })();
    }, [props.applicationId]);

    useEffect(() => {
        if (!allInstances) return;
        sortInstances(allInstances);
        assignVisibleInstances();
    }, [allInstances]);


    useEffect(() => {
        props.onSelectedInstanceChange(selectedInstance);
    // This rule is starting to grate on my nerves.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- I don't want this to run when the props change, only when the selected instance changes.
    }, [selectedInstance]);


    function sortInstances(instances: AppInstanceObject[]): void {
        const sortingOrder = [AppInstanceStatus.STARTING, AppInstanceStatus.RUNNING, AppInstanceStatus.FAILED, AppInstanceStatus.COMPLETED];
        instances.sort((a, b) => dayjs(a.startTime).valueOf() - dayjs(b.startTime).valueOf() );
        instances.sort((a, b) => sortingOrder.indexOf(a.status) - sortingOrder.indexOf(b.status));
    }

    function assignVisibleInstances(): void {
        setVisibleInstances(allInstances ?? []);
    }


    function handleAllInstanceViewChange(value: string): void {
        setIsAllInstances(value === "all");
        if (value === "all" && selectedInstance?.creator !== "Test User") setSelectedInstance(undefined);
    }

    function handleFlowChange(value: string): void {
        if (props.onSelectedFlowChange) props.onSelectedFlowChange(value);
    }

    function handleInstanceClick(instance: AppInstanceObject): void {
        setSelectedInstance((currentInstance) => { return instance.id === currentInstance?.id ? undefined : instance; });
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
                        {...instance}
                        isSelected={selectedInstance?.id === instance.id}
                        isVisible={isAllInstances || instance.creator === (session?.data?.user?.name ?? "Test User")}
                        onClick={handleInstanceClick}
                    />
                )}
            </div>

        </div>
    );
}



interface AppInstanceProps extends AppInstanceObject {
    isVisible?: boolean,
    isSelected?: boolean,
    onClick: (instance: AppInstanceObject) => void;
}

function AppInstance({isVisible, isSelected, onClick, ...props}: AppInstanceProps): JSX.Element {
    const {elapsedTime} = useElapsedTime(props.startTime, props.endTime);


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
                !isVisible ? "hidden" : undefined,
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