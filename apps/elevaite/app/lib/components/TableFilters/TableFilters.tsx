"use client";
import { ClickOutsideDetector, CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useRef, useState } from "react";
import { useDatasets } from "../../contexts/DatasetsContext";
import { type FilterUnitStructure, type FilterGroupStructure, type FiltersStructure } from "../../interfaces";
import "./TableFilters.scss";






export function TableFilters(): JSX.Element {
    const datasetContext = useDatasets();
    const filterButtonRef = useRef<HTMLButtonElement|null>(null);
    const [isFiltersPanelOpen, setIsFiltersPanelOpen] = useState(false);
    const [activeFilters, setActiveFilters] = useState(0);




    function toggleFiltersPanel(): void {
        // setActiveFilters(current => current === 4 ? 0 : current+1);
        setIsFiltersPanelOpen(current => !current);
    }

    function closeFiltersPanel(): void {
        setIsFiltersPanelOpen(false);
    }

    function handleFilterClick(filter: string): void {
        console.log("Filter clicked:", filter);
    }

    function handleGroupClick(group: string): void {
        datasetContext.toggleFilterGroup(group);
    }



    return (
        <div className="table-filters-container">

            <div className="filters-button-anchor">

                <CommonButton
                    className="filters-button"                    
                    passedRef={filterButtonRef}
                    onClick={toggleFiltersPanel}
                >
                    <ElevaiteIcons.SVGFilter/>
                    <span>Filters</span>
                    <div className={["active-filters-count", activeFilters === 0 ? "hidden" : undefined].filter(Boolean).join(" ")}>
                        {activeFilters}
                    </div>
                </CommonButton>

                <ClickOutsideDetector 
                    onOutsideClick={closeFiltersPanel}
                    ignoredRefs={[filterButtonRef]}
                >
                    <FiltersPanel
                        isOpen={isFiltersPanelOpen}
                        onFilterClick={handleFilterClick}
                        onGroupClick={handleGroupClick}
                        structure={datasetContext.filtering}
                        isLoading={datasetContext.loading.filtersStructure}
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
                            />
                        )
                    }

                </div>

            </div>
        </div>
    );
}





type FilterUnitProps = FilterUnitStructure & {
    onClick: (filter: string) => void;
}

function FilterUnit(props: FilterUnitProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.label);
    }

    return (
        <div className="filter-unit-container">
            <CommonButton
                className="filter-unit-button"
                onClick={handleClick}
            >
                {props.label}
            </CommonButton>
        </div>
    );
}

