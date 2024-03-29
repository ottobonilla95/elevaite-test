import type { CommonMenuItem } from "@repo/ui/components";
import { CommonButton, CommonMenu, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { specialHandlingModelFields, useModels } from "../../../../lib/contexts/ModelsContext";
import type { ModelObject } from "../../../../lib/interfaces";
import { ModelsStatus } from "../../../../lib/interfaces";
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


    function getSpecialItem(item: RowStructure): React.ReactNode {
        switch (item.specialHandling) {
            case specialHandlingModelFields.STATUS: return (!props.model?.status ? "" :
                <StatusCell status={props.model.status} url={props.model.endpointUrl} />);
            case specialHandlingModelFields.TAGS: return (props.model?.[item.field] ? <>{(props.model[item.field] as string[]).map((tag: string) => 
                    <div className="tag" key={tag}>{tag}</div>
                )}</> : "");
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
                "isHeader" in props ? <div className="models-list-row-cell menu"/> :
                <div className="models-list-row-cell menu">
                    <CommonMenu
                        item={props.model}
                        menu={props.menu}
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



export function StatusCell({status, url}: {status: ModelsStatus, url?: string;}): JSX.Element {

    function onEndpointClick(): void {
        if (!url) return;
        void navigator.clipboard.writeText(url);
    }

    return (
        <div
            className={[
                "status-cell",
                status === ModelsStatus.DEPLOYED ? "deployed" : undefined,
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
        </div>
    );
}