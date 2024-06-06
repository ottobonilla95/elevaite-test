import type { CommonMenuItem } from "@repo/ui/components";
import { CommonButton, CommonMenu, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { specialHandlingCostFields, useCost } from "../../../lib/contexts/CostContext";
import { type TestCostDataObject } from "../../../lib/contexts/CostContextTestData";
import "./CostListRow.scss";



export interface RowStructure {
    header: string;
    field: string;
    isSortable?: boolean;
    onClick?: (cost: TestCostDataObject) => void;
    specialHandling?: specialHandlingCostFields;
    ellipses?: boolean;
    subtitle?: string;
    align?: "left" | "right" | "center";
    style?: "block";
}


export interface CostListNormalRow {
    cost: TestCostDataObject;
    structure: RowStructure[];
    menu?: CommonMenuItem<TestCostDataObject>[];
    menuToTop?: boolean;
}

interface CostListHeaderRow {
    isHeader: true;
    cost?: never;
    structure: RowStructure[];
    menu?: CommonMenuItem<TestCostDataObject>[];
}

type CostListRowProps = CostListNormalRow | CostListHeaderRow;

export function CostListRow(props: CostListRowProps): JSX.Element {
    const costContext = useCost();


    function getSpecialItem(item: RowStructure): React.ReactNode {
        switch (item.specialHandling) {
            case specialHandlingCostFields.PRICE: return (!props.cost?.[item.field] ? "—" : `$ ${getFormattedNumber(props.cost[item.field] as string, 2)}`);
            case specialHandlingCostFields.AMOUNT: return (!props.cost?.[item.field] ? "—" : getFormattedNumber(props.cost[item.field] as string));
            case specialHandlingCostFields.FRACTION_AMOUNT: return (!props.cost?.[item.field] ? "—" : getFormattedNumber(props.cost[item.field] as string, 2));
            case specialHandlingCostFields.TAGS: return (!props.cost?.[item.field] ? "" : <div className="tag">{props.cost[item.field]}</div>);
            case specialHandlingCostFields.DATE: return (!props.cost?.[item.field] ? "" : 
                <span title={dayjs(props.cost[item.field] as string).format("dddd DD MMMM YYYY")}>
                    {dayjs(props.cost[item.field] as string).format("MM-DD-YYYY")}
                </span>
            );
            case specialHandlingCostFields.MODEL: return (!props.cost?.[item.field] ? "" : 
                <div className="model-content">
                    <div className="model-color-container" style={{backgroundColor: costContext.getBarColor(props.cost[item.field] as string) }} />
                    <span>{props.cost[item.field]}</span>
                </div>
            );
            default: return "";
        }
    }

    function getFormattedNumber(item: string|number, fractionDigits?: number): string {
        if (typeof item === "string" && !parseFloat(item)) return item;
        const numberItem = typeof item === "string" ? parseFloat(item) : item;
        return numberItem.toLocaleString(undefined, { minimumFractionDigits: fractionDigits ?? 0, maximumFractionDigits: fractionDigits ?? 0 })
    }


    function handleSortClick(item: RowStructure): void {
        if (!item.isSortable) return;
        costContext.sortCostData(item.field, item.specialHandling);
    }


    return (
        <div className={["cost-list-row-container", "isHeader" in props ? "header" : undefined].filter(Boolean).join(" ")}>

            {!props.menu ? undefined : 
                "isHeader" in props || props.menu.length === 0 ? <div className="cost-list-row-cell menu"/> :
                <div className="cost-list-row-cell menu">
                    <CommonMenu
                        item={props.cost}
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
                        "cost-list-row-cell header",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                    ].filter(Boolean).join(" ")}
                    onClick={() => { handleSortClick(structureItem); }}
                    disabled={!structureItem.isSortable}
                    overrideClass
                >
                    <div className="header-title">
                        <span>{structureItem.header}</span>
                        {!structureItem.subtitle ? undefined :
                            <span className="subtitle">{structureItem.subtitle}</span>
                        }
                    </div>
                    
                    {structureItem.isSortable ? 
                        <div className={[
                            "sort-container",
                            costContext.costSorting.field === structureItem.field && costContext.costSorting.isDesc ? "desc" : undefined,
                            costContext.costSorting.field === structureItem.field && !costContext.costSorting.isDesc ? "asc" : undefined,
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
                            "cost-list-row-cell",
                            structureItem.ellipses ? "ellipses" : undefined,
                            structureItem.field,
                            structureItem.align,
                            structureItem.style,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { if (structureItem.onClick) structureItem.onClick(props.cost); }}
                        disabled={!structureItem.isSortable}
                        overrideClass
                    >                    
                        {structureItem.specialHandling ? getSpecialItem(structureItem) :
                            props.cost[structureItem.field] ? props.cost[structureItem.field] : ""
                        }
                    </CommonButton>

                :

                <div key={structureItem.field}
                    className={[
                        "cost-list-row-cell",
                        structureItem.ellipses ? "ellipses" : undefined,
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                    ].filter(Boolean).join(" ")}
                >
                    {structureItem.ellipses ? 
                        <span title={props.cost[structureItem.field] as string}>
                            {structureItem.specialHandling ? getSpecialItem(structureItem) :
                                props.cost[structureItem.field] ? props.cost[structureItem.field] : ""
                            }
                        </span>
                        :
                        structureItem.specialHandling ? getSpecialItem(structureItem) :
                            props.cost[structureItem.field] ? props.cost[structureItem.field] : ""                        
                    }
                </div>
        
                
            )}


        </div>
    );
}

