import type { CommonMenuItem } from "@repo/ui/components";
import { CommonButton, CommonMenu, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { specialHandlingDatasetFields, useDatasets } from "../../../../lib/contexts/DatasetsContext";
import type { ModelDatasetObject } from "../../../../lib/interfaces";
import "./DatasetsListRow.scss";



export interface RowStructure {
    header: string;
    field: string;
    isSortable?: boolean;
    onClick?: (dataset: ModelDatasetObject) => void;
    specialHandling?: specialHandlingDatasetFields;
    align?: "left" | "right" | "center";
    style?: "block";
}


export interface DatasetListNormalRow {
    dataset: ModelDatasetObject;
    structure: RowStructure[];
    menu?: CommonMenuItem<ModelDatasetObject>[];
    menuToTop?: boolean;
}

interface DatasetListHeaderRow {
    isHeader: true;
    dataset?: never;
    structure: RowStructure[];
    menu?: CommonMenuItem<ModelDatasetObject>[];
}

type DatasetsListRowProps = DatasetListNormalRow | DatasetListHeaderRow;

export function DatasetsListRow(props: DatasetsListRowProps): JSX.Element {
    const datasetContext = useDatasets();


    function getSpecialItem(item: RowStructure): React.ReactNode {
        switch (item.specialHandling) {
            case specialHandlingDatasetFields.TASKS: return (props.dataset?.[item.field] ? 
                Array.isArray(props.dataset[item.field]) ? (props.dataset[item.field] as string[]).sort().join(", ") : props.dataset[item.field] as string : "");
            case specialHandlingDatasetFields.TAGS: return (props.dataset?.[item.field] ? <>{(props.dataset[item.field] as string[]).map((tag: string) => 
                    <div className="tag" key={tag}>{tag}</div>
                )}</> : "");
            case specialHandlingDatasetFields.DATE: return (props.dataset?.[item.field] ? dayjs(props.dataset[item.field] as string).format("DD-MMM-YYYY hh:mm a") : "");
            default: return "";
        }
    }


    function handleSortClick(item: RowStructure): void {
        if (!item.isSortable) return;
        datasetContext.sortDatasets(item.field, item.specialHandling);
    }


    return (
        <div className={["datasets-list-row-container", "isHeader" in props ? "header" : undefined].filter(Boolean).join(" ")}>

            {!props.menu ? undefined : 
                "isHeader" in props || props.menu.length === 0 ? <div className="datasets-list-row-cell menu"/> :
                <div className="datasets-list-row-cell menu">
                    <CommonMenu
                        item={props.dataset}
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
                        "datasets-list-row-cell header",
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
                            datasetContext.datasetSorting.field === structureItem.field && datasetContext.datasetSorting.isDesc ? "desc" : undefined,
                            datasetContext.datasetSorting.field === structureItem.field && !datasetContext.datasetSorting.isDesc ? "asc" : undefined,
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
                            "datasets-list-row-cell",
                            structureItem.field,
                            structureItem.align,
                            structureItem.style,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { if (structureItem.onClick) structureItem.onClick(props.dataset); }}
                        disabled={!structureItem.isSortable}
                        overrideClass
                    >                    
                        {structureItem.specialHandling ? getSpecialItem(structureItem) :
                            props.dataset[structureItem.field] ? props.dataset[structureItem.field] : ""
                        }
                    </CommonButton>

                :

                <div key={structureItem.field}
                    className={[
                        "datasets-list-row-cell",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                    ].filter(Boolean).join(" ")}
                >
                    {structureItem.specialHandling ? getSpecialItem(structureItem) :
                        props.dataset[structureItem.field] ? props.dataset[structureItem.field] : ""
                    }
                </div>
        
                
            )}


        </div>
    );
}

