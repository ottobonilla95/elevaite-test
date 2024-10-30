"use client";
import { ClickOutsideDetector, CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useRef, useState } from "react";
import { getUniqueActiveFiltersFromGroup } from "../../helpers";
import { type FilterGroupStructure, type FilterUnitStructure, type FiltersStructure } from "../../interfaces";
import "./TableFilters.scss";




interface TableFiltersProps {
    filtering: FiltersStructure;
    onToggleFilter?: (filter: string) => void;
    onToggleGroup?: (group: string) => void;
    activeFiltersCount?: number;
    isLoading?: boolean;
    showPills?: boolean;
}

export function TableFilters(props: TableFiltersProps): JSX.Element {
    const filterButtonRef = useRef<HTMLButtonElement|null>(null);
    const [isFiltersPanelOpen, setIsFiltersPanelOpen] = useState(false);
    const [activeFilters, setActiveFilters] = useState<string[]>([]);


    useEffect(() => {
        setActiveFilters(getUniqueActiveFiltersFromGroup(props.filtering));
    }, [props.filtering]);


    function toggleFiltersPanel(): void {
        setIsFiltersPanelOpen(current => !current);
    }

    function closeFiltersPanel(): void {
        setIsFiltersPanelOpen(false);
    }

    function handleFilterClick(filter: string): void {
        if (props.onToggleFilter) props.onToggleFilter(filter);
    }

    function handleClosePill(filter: string): void {
        if (props.onToggleFilter) props.onToggleFilter(filter);
    }

    function handleGroupClick(group: string): void {
        if (props.onToggleGroup) props.onToggleGroup(group);
    }



    return (
        <div className="table-filters-container">

            {!props.showPills ? undefined :
                <div className="active-filters-list">
                    {activeFilters.map(filter => 
                        <FilterPill key={filter} label={filter} onClick={handleClosePill} />
                    )}
                </div>
            }

            <div className="filters-button-anchor">

                <CommonButton
                    className="filters-button"                    
                    passedRef={filterButtonRef}
                    onClick={toggleFiltersPanel}
                >
                    <ElevaiteIcons.SVGFilter/>
                    <span>Filters</span>
                    {props.activeFiltersCount === undefined ? undefined :
                        <div className={["active-filters-count", props.activeFiltersCount === 0 ? "hidden" : undefined].filter(Boolean).join(" ")}>
                            {props.activeFiltersCount}
                        </div>
                    }
                </CommonButton>

                <ClickOutsideDetector 
                    onOutsideClick={closeFiltersPanel}
                    ignoredRefs={[filterButtonRef]}
                >
                    <FiltersPanel
                        isOpen={isFiltersPanelOpen}
                        onFilterClick={handleFilterClick}
                        onGroupClick={handleGroupClick}
                        structure={props.filtering}
                        isLoading={props.isLoading}
                    />
                </ClickOutsideDetector>
                
            </div>
        </div>
    );
}




interface FiltersPanelProps {
    isLoading?: boolean;
    isOpen: boolean;
    onFilterClick: (filter: string) => void;
    onGroupClick: (group: string) => void;
    structure: FiltersStructure;
}

function FiltersPanel(props: FiltersPanelProps): JSX.Element {
    return (
        <div className={["filter-panel-container", props.isOpen ? "open" : undefined].filter(Boolean).join(" ")}>
            <div className="filter-panel-accordion">
                <div className="filter-panel-contents">

                    {!props.structure.label ? undefined :
                        <div className="filter-panel-header">{props.structure.label}</div>
                    }

                    {props.isLoading ? 
                        <div className="filters-loading">
                            <ElevaiteIcons.SVGSpinner/>
                            <span>Loading filters</span>
                        </div>
                    :
                    props.structure.filters.length === 0 ? 
                        <div className="no-filters">No available filters</div>
                    :
                    props.structure.filters.map(filterGroup => {
                        if ("filters" in filterGroup) return (
                            <FiltersGroupBox
                                key={filterGroup.label}
                                group={filterGroup}
                                onFilterGroupClick={props.onGroupClick}
                                onFilterClick={props.onFilterClick}
                            />
                        );
                        return <div key={filterGroup.label}>{filterGroup.label}</div>
                    })
                    }

                </div>
            </div>
        </div>
    );
}



interface FiltersGroupBoxProps {
    onFilterClick: (filter: string) => void;
    onFilterGroupClick: (group: string) => void;
    group: FilterGroupStructure;
}

function FiltersGroupBox(props: FiltersGroupBoxProps): JSX.Element {

    function handleGroupClick(): void {
        props.onFilterGroupClick(props.group.label);
    }

    return (
        <div className={["filter-group-box-container", props.group.isClosed ? "closed" : undefined].filter(Boolean).join(" ")}>
            <CommonButton
                onClick={handleGroupClick}
            >
                <div className="chevron-container">
                    <ElevaiteIcons.SVGChevron/>
                </div>
                <span className="filter-group-box-label">{props.group.label}</span>
            </CommonButton>

            <div className="filter-group-box-accordion">

                <div className="filter-group-box-contents">

                    {props.group.filters.length === 0 ? 
                        <div className="no-group-filters">No filters in this group</div>
                        :
                        props.group.filters.map(filter => 
                            <FilterUnit
                                key={filter.label}
                                {...filter}
                                onClick={props.onFilterClick}
                                prettifyText={props.group.label === "Tasks"}
                            />
                        )
                    }

                </div>

            </div>
        </div>
    );
}




interface FilterPillProps {
    label: string;
    onClick: (filter: string) => void;
    prettifyText?: boolean;
}

function FilterPill(props: FilterPillProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.label);
    }

    return (
        <div className={["filter-pill-container", props.prettifyText ? "capitalize" : undefined].filter(Boolean).join(" ")}>
            <span>
                {props.prettifyText ? props.label.split("-").join(" ") : props.label}
            </span>
            <CommonButton
                className="filter-pill-button"
                onClick={handleClick}
            >
                <ElevaiteIcons.SVGXmark/>
            </CommonButton>
        </div>
    );
}




type FilterUnitProps = FilterUnitStructure & {
    onClick: (filter: string) => void;
    isActive?: boolean;
    prettifyText?: boolean;
}

function FilterUnit(props: FilterUnitProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.label);
    }

    return (
        <div className={["filter-unit-container", props.prettifyText ? "capitalize" : undefined].filter(Boolean).join(" ")}>
            <CommonButton
                className={["filter-unit-button", props.isActive ? "active" : undefined].filter(Boolean).join(" ")}
                onClick={handleClick}
            >
                {props.prettifyText ? props.label.split("-").join(" ") : props.label}
            </CommonButton>
        </div>
    );
}

