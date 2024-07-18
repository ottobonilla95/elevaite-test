import type { CommonMenuItem } from "@repo/ui/components";
import { CommonButton, CommonMenu, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { type SortingObject } from "../../../../lib/interfaces";
import "./ListRow.scss";



export enum specialHandlingListRowFields {
    TAGS = "tags",
    ROLES = "roles",
    PERMISSIONS_LABEL = "permissionsLabel",
    PERMISSIONS = "permissions",
    EMAIL = "email",
    COUNT = "count",
    DATE = "date",
}


export interface RowStructure<RowObjectType> {
    header: string;
    field: string;
    isSortable?: boolean;
    onClick?: (rowItem: RowObjectType) => void;
    specialHandling?: specialHandlingListRowFields;
    align?: "left" | "right" | "center";
    style?: "block";
    leftBorder?: "all" | "header";
    capitalize?: boolean;
}


export interface ListNormalRow<RowObjectType> {
    rowItem: RowObjectType;
    structure: RowStructure<RowObjectType>[];
    menu?: CommonMenuItem<RowObjectType>[];
    menuToTop?: boolean;
    onSort?: never;
    sorting?: never;
}

interface ListHeaderRow<RowObjectType> {
    isHeader: true;
    rowItem?: never;
    structure: RowStructure<RowObjectType>[];
    menu?: CommonMenuItem<RowObjectType>[];
    onSort?: (field: string, specialHandling?: string) => void;
    sorting?: SortingObject<RowObjectType>;
}

type ListRowProps<RowObjectType> = ListNormalRow<RowObjectType> | ListHeaderRow<RowObjectType>;

export function ListRow<RowObjectType>(props: ListRowProps<RowObjectType>): JSX.Element {


    function getSpecialItem(item: RowStructure<RowObjectType>): React.ReactNode {
        switch (item.specialHandling) {
            case specialHandlingListRowFields.ROLES: {
                const roles = props.rowItem?.[item.field] as unknown;
                if (Array.isArray(roles)) {
                    let verifiedRoles: {roleLabel: string, roleParent?: string}[];
                    if (roles.length >= 1 && "roleLabel" in roles[0]) {
                        verifiedRoles = roles as {roleLabel: string, roleParent?: string}[];

                        if (verifiedRoles.length === 1 && verifiedRoles[0].roleLabel === "loading") return (
                            <div className="roles-loading">
                                <ElevaiteIcons.SVGSpinner/>
                                <span>Loading roles...</span>
                            </div>
                        );
                        return (
                            <div className="roles-container">
                                {verifiedRoles.map(role => 
                                    <div className="role" key={role.roleLabel + (role.roleParent ?? "")}>
                                        <span className="label">{role.roleLabel}</span>
                                        {!role.roleParent ? undefined :
                                        <><span>|</span><span className="parent">{role.roleParent}</span></>
                                        }
                                    </div>
                                )}
                            </div>
                        )
                    }
                } 
                return undefined;
            }
            case specialHandlingListRowFields.PERMISSIONS_LABEL: {                
                const permissions = props.rowItem?.[item.field] as unknown;
                return permissions && Array.isArray(permissions) ? permissions.join(" / ") : "";
            }
            case specialHandlingListRowFields.PERMISSIONS: {                
                const permission = props.rowItem?.[item.field] as unknown;
                return (<div className={["permission-field", permission ? "green" : "red"].filter(Boolean).join(" ")}>
                    {permission ? "YES" : "NO"}
                </div>);
            }
            case specialHandlingListRowFields.TAGS: return (props.rowItem?.[item.field] ? <>{(props.rowItem[item.field] as string[]).map((tag: string) => 
                    <div className="tag" key={tag}>{tag}</div>
                )}</> : "");
            case specialHandlingListRowFields.COUNT: return (props.rowItem?.[item.field] !== undefined ? <div className="count">{props.rowItem[item.field]}</div> : "");
            case specialHandlingListRowFields.EMAIL: return (props.rowItem?.[item.field] ? <a className="email" href={`mailto:${props.rowItem[item.field] as string}`}>{props.rowItem[item.field]}</a> : "");
            case specialHandlingListRowFields.DATE: return (props.rowItem?.[item.field] ? dayjs(props.rowItem[item.field] as string).format("DD-MMM-YYYY hh:mm a") : "");
            default: return "";
        }
    }


    function handleSortClick(item: RowStructure<RowObjectType>): void {
        if (!item.isSortable || !props.onSort) return;
        props.onSort(item.field, item.specialHandling);
    }


    return (
        <div className={["access-management-list-row-container", "isHeader" in props ? "header" : undefined].filter(Boolean).join(" ")}>

            {!props.menu ? undefined : 
                "isHeader" in props || props.menu.length === 0 ? <div className="access-management-list-row-cell menu"/> :
                <div className="access-management-list-row-cell menu">
                    <CommonMenu
                        item={props.rowItem}
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
                        "access-management-list-row-cell header",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                        structureItem.leftBorder ? "left-border" : undefined,
                        structureItem.capitalize ? "capitalize" : undefined,
                    ].filter(Boolean).join(" ")}
                    onClick={() => { handleSortClick(structureItem); }}
                    disabled={!structureItem.isSortable}
                    overrideClass
                >
                    {structureItem.header}
                    
                    {structureItem.isSortable ? 
                        <div className={[
                            "sort-container",
                            props.sorting && "field" in props.sorting && typeof (props.sorting.field) === "string" && props.sorting.field === structureItem.field && props.sorting.isDesc ? "desc" : undefined,
                            props.sorting && "field" in props.sorting && typeof (props.sorting.field) === "string" && props.sorting.field === structureItem.field && !props.sorting.isDesc ? "asc" : undefined,
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
                            "access-management-list-row-cell",
                            structureItem.field,
                            structureItem.align,
                            structureItem.style,
                            structureItem.leftBorder === "all" ? "left-border" : undefined,
                            structureItem.capitalize ? "capitalize" : undefined,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { if (structureItem.onClick) structureItem.onClick(props.rowItem); }}
                        disabled={!structureItem.isSortable}
                        overrideClass
                    >                    
                        {structureItem.specialHandling ? getSpecialItem(structureItem) :
                            props.rowItem[structureItem.field] ? props.rowItem[structureItem.field] : ""
                        }
                    </CommonButton>

                :

                <div key={structureItem.field}
                    className={[
                        "access-management-list-row-cell",
                        structureItem.field,
                        structureItem.align,
                        structureItem.style,
                        structureItem.leftBorder === "all" ? "left-border" : undefined,
                        structureItem.capitalize ? "capitalize" : undefined,
                    ].filter(Boolean).join(" ")}
                >
                    {structureItem.specialHandling ? getSpecialItem(structureItem) :
                        props.rowItem[structureItem.field] ? props.rowItem[structureItem.field] : ""
                    }
                </div>
        
                
            )}


        </div>
    );
}

