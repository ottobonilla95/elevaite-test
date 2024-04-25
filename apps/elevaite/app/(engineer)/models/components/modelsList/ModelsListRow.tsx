import type { CommonMenuItem } from "@repo/ui/components";
import { CommonButton, CommonMenu, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { specialHandlingModelFields, useModels } from "../../../../lib/contexts/ModelsContext";
import type { ModelObject } from "../../../../lib/interfaces";
import { ModelsStatus, REGISTERING_MODELS_REFRESH_PERIOD } from "../../../../lib/interfaces";
import "./ModelsListRow.scss";



export interface RowStructure {
    header: string;
    field: string;
    isSortable?: boolean;
    onClick?: (model: ModelObject) => void;
    specialHandling?: specialHandlingModelFields;
    align?: "left" | "right" | "center";
    style?: "block";
}


export interface ModelListNormalRow {
    model: ModelObject;
    structure: RowStructure[];
    menu?: CommonMenuItem<ModelObject>[];
    menuToTop?: boolean;
}

interface ModelListHeaderRow {
    isHeader: true;
    model?: never;
    structure: RowStructure[];
    menu?: CommonMenuItem<ModelObject>[];
}

type ModelsListRowProps = ModelListNormalRow | ModelListHeaderRow;

export function ModelsListRow(props: ModelsListRowProps): JSX.Element {
    const modelsContext = useModels();

    useEffect(() => {
        if (props.model && props.model.status === ModelsStatus.REGISTERING) {
            const refreshInterval = setInterval(() => {
                void modelsContext.refreshModelById(props.model.id);
            }, REGISTERING_MODELS_REFRESH_PERIOD);
            return () => { clearInterval(refreshInterval); };
        }
    }, [props.model]);


    function getSpecialItem(item: RowStructure): React.ReactNode {
        switch (item.specialHandling) {
            case specialHandlingModelFields.STATUS: return (!props.model?.status ? "" :
                <StatusCell status={props.model.status} url={props.model.endpointUrl} />);
            case specialHandlingModelFields.TAGS: return (props.model?.[item.field] ? <>{(props.model[item.field] as string[]).map((tag: string) => 
                    <div className="tag" key={tag}>{tag}</div>
                )}</> : "");
            case specialHandlingModelFields.RAM_TO_RUN: return (props.model?.memory_requirements?.total_size.value_str ?? "—");
            case specialHandlingModelFields.RAM_TO_TRAIN: return (props.model?.memory_requirements?.training_using_adam.value_str ?? "—");
            case specialHandlingModelFields.DATE: return (props.model?.[item.field] ? dayjs(props.model[item.field] as string).format("DD-MMM-YYYY hh:mm a") : "");
            default: return "";
        }
    }


    function handleSortClick(item: RowStructure): void {
        if (!item.isSortable) return;
        modelsContext.sortModels(item.field, item.specialHandling);
    }


    return (
        <div className={["models-list-row-container", "isHeader" in props ? "header" : undefined].filter(Boolean).join(" ")}>

            {!props.menu ? undefined : 
                "isHeader" in props || props.menu.length === 0 ? <div className="models-list-row-cell menu"/> :
                <div className="models-list-row-cell menu">
                    <CommonMenu
                        item={props.model}
                        menu={props.menu}
                        top={props.menuToTop}
                    />
                </div>
            }

            {props.structure.map(structureItem => 

                // Header
                "isHeader" in props ? 
            
                <CommonButton key={structureItem.field}
                    className={[
                        "models-list-row-cell header",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                    ].filter(Boolean).join(" ")}
                    onClick={() => { handleSortClick(structureItem); }}
                    disabled={!structureItem.isSortable}
                    overrideClass
                >
                    {structureItem.header}
                    
                    {structureItem.isSortable ? 
                        <div className={[
                            "sort-container",
                            modelsContext.modelsSorting.field === structureItem.field && modelsContext.modelsSorting.isDesc ? "desc" : undefined,
                            modelsContext.modelsSorting.field === structureItem.field && !modelsContext.modelsSorting.isDesc ? "asc" : undefined,
                        ].filter(Boolean).join(" ")}>
                            <ElevaiteIcons.SVGChevron type="sort"/>
                            <ElevaiteIcons.SVGChevron type="sort"/>
                        </div>
                    : undefined }
                </CommonButton>

                // Non-Header
                : structureItem.onClick ? 
                    
                    <CommonButton key={structureItem.field}
                        className={[
                            "models-list-row-cell",
                            structureItem.field,
                            structureItem.align,
                            structureItem.style,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { if (structureItem.onClick) structureItem.onClick(props.model); }}
                        disabled={!structureItem.isSortable}
                        overrideClass
                    >                    
                        {structureItem.specialHandling ? getSpecialItem(structureItem) :
                            props.model[structureItem.field] ? props.model[structureItem.field] : ""
                        }
                    </CommonButton>

                :

                <div key={structureItem.field}
                    className={[
                        "models-list-row-cell",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                    ].filter(Boolean).join(" ")}
                >
                    {structureItem.specialHandling ? getSpecialItem(structureItem) :
                        props.model[structureItem.field] ? props.model[structureItem.field] : ""
                    }
                </div>
        
                
            )}


        </div>
    );
}



export function StatusCell({status, url, toastLeft}: {status: ModelsStatus, url?: string; toastLeft?: boolean}): JSX.Element {
    const [toastCounter, setToastCounter] = useState(0);

    function onEndpointClick(): void {
        if (!url) return;
        setToastCounter(current => current < 2 ? 2 : 1);
        void navigator.clipboard.writeText(url);
    }

    return (
        <div
            className={[
                "status-cell",
                status,
            ].join(" ")}
            title={url ? "Click to copy the endpoing url to clipboard" : ""}
        >
            {status === ModelsStatus.ACTIVE ? <ElevaiteIcons.SVGCheckmark/> : 
            status === ModelsStatus.REGISTERING ? <ElevaiteIcons.SVGInstanceProgress/> :
            status === ModelsStatus.DEPLOYED ? <ElevaiteIcons.SVGDeployed/> :
            <ElevaiteIcons.SVGXmark/>
            }

            {status === ModelsStatus.ACTIVE ? "Active" : 
            status === ModelsStatus.REGISTERING ? "Registering" :
            status === ModelsStatus.DEPLOYED ? "Deployed" :
            "Failed"
            }

            {status !== ModelsStatus.DEPLOYED || !url ? undefined :
                <CommonButton title={url} onClick={onEndpointClick}><ElevaiteIcons.SVGCopy/></CommonButton>
            }

            {!url || toastCounter === 0 ? undefined :
                <div key={toastCounter} className={["toast-container", toastLeft ? "left" : undefined].filter(Boolean).join(" ")}>
                    <span>Endpoint URL copied to clipboard.</span>
                </div>
            }
        </div>
    );
}
