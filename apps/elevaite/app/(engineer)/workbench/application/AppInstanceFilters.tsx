"use client";
import type { CommonSelectOption} from "@repo/ui/components";
import { ClickOutsideDetector, CommonButton, CommonSelect, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useRef, useState } from "react";
import { AppInstanceStatus } from "../../../lib/interfaces";
import "./AppInstanceFilters.scss";


const SEARCH_DEBOUNCE_TIME = 500; // milliseconds

export enum ScopeInstances {
    MyInstances = "my",
    AllInstances = "all",
}

export enum SortingInstances {
    Ascending = "ascending",
    Descending = "descending",
}

interface StatusDisplay {
    [AppInstanceStatus.STARTING]: boolean;
    [AppInstanceStatus.RUNNING]: boolean;
    [AppInstanceStatus.FAILED]: boolean;
    [AppInstanceStatus.COMPLETED]: boolean;
}

export interface AppInstanceFiltersObject {
    scope: ScopeInstances;
    sorting: SortingInstances;
    searchTerm: string;
    showStatus: StatusDisplay;
}
export const initialFilters: AppInstanceFiltersObject = {
    scope: ScopeInstances.MyInstances,
    sorting: SortingInstances.Ascending,
    searchTerm: "",
    showStatus: {
        [AppInstanceStatus.STARTING]: false,
        [AppInstanceStatus.RUNNING]: false,
        [AppInstanceStatus.FAILED]: false,
        [AppInstanceStatus.COMPLETED]: false,
    }
}

const instanceViewOptions: CommonSelectOption[] = [
    {label: "My Instances", value: ScopeInstances.MyInstances},
    {label: "All Instances", value: ScopeInstances.AllInstances}
];





interface AppInstanceFiltersProps {
    onFiltersChanged: (filters: AppInstanceFiltersObject) => void;
}

export function AppInstanceFilters(props: AppInstanceFiltersProps): JSX.Element {
    const filterButtonRef = useRef<HTMLButtonElement|null>(null);
    const [filters, setFilters] = useState(initialFilters);
    const [searchTerm, setSearchTerm] = useState("");
    const [isFiltersOpen, setIsFiltersOpen] = useState(false);
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);


    useEffect(() => {
        props.onFiltersChanged(filters);
        setActiveFiltersCount(Object.keys(filters.showStatus).filter(key => { return filters.showStatus[key]; }).length);
    }, [filters]);

    useEffect(() => {
        const debounceTimeout = setTimeout(() => {
            setFilters(currentFilters => {
                const newFilters = {...currentFilters};
                newFilters.searchTerm = searchTerm;
                return newFilters;
            });
        }, SEARCH_DEBOUNCE_TIME);
        return () => { clearTimeout(debounceTimeout); };
    }, [searchTerm]);
      


    function handleScopeChange(scope: ScopeInstances): void {
        setFilters(currentFilters => {
            const newFilters = {...currentFilters};
            newFilters.scope = scope;
            return newFilters;
        });
    }

    function handleStatusFilterClick(status: AppInstanceStatus, currentStatus: boolean): void {
        setFilters(currentFilters => {
            const newFilters = {...currentFilters};
            newFilters.showStatus[status] = !currentStatus;
            return newFilters;
        });
    }

    function handleSortingFilterClick(sorting: SortingInstances): void {
        setFilters(currentFilters => {
            const newFilters = {...currentFilters};
            newFilters.sorting = sorting;
            return newFilters;
        });
    }

    function handleSearch(term: string): void {
        setSearchTerm(term);
    }


    return (
        <div className="app-instance-filters-container">
            <div className="top-bar">
                <span>Showing: </span>
                <CommonSelect
                    className="app-instances-type"
                    defaultValue={ScopeInstances.MyInstances}
                    onSelectedValueChange={handleScopeChange}
                    options={instanceViewOptions}
                />

                <div className="sorting-filters-container">
                    <CommonButton
                        className={[
                            "sorting-button",
                            SortingInstances.Ascending,
                            filters.sorting === SortingInstances.Ascending ? "active" : undefined,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { handleSortingFilterClick(SortingInstances.Ascending); }}
                        title="Sort instances from oldest to newest."
                    >
                        <ElevaiteIcons.SVGChevron type="down" />
                    </CommonButton>
                    <CommonButton
                        className={[
                            "sorting-button",
                            SortingInstances.Descending,
                            filters.sorting === SortingInstances.Descending ? "active" : undefined,
                        ].filter(Boolean).join(" ")}
                        onClick={() => { handleSortingFilterClick(SortingInstances.Descending); }}
                        title="Sort instances from newest to oldest."
                    >
                        <ElevaiteIcons.SVGChevron type="down" />
                    </CommonButton>
                </div>
            </div>



            <div className="middle-bar">
                
                <div className="filters-wrapper">
                    <CommonButton
                        className={[
                            "filters-button",
                            isFiltersOpen ? "open" : undefined,
                        ].filter(Boolean).join(" ")}
                        passedRef={filterButtonRef}
                        onClick={() => { setIsFiltersOpen(current => !current); }}
                    >
                        <ElevaiteIcons.SVGFilter/>
                        <span>Filters</span>
                        <div className={[
                            "filters-count",
                            activeFiltersCount ? "show" : undefined
                        ].filter(Boolean).join(" ")}>
                            {activeFiltersCount}
                        </div>
                    </CommonButton>
                    <ClickOutsideDetector onOutsideClick={() => { setIsFiltersOpen(false); }} ignoredRefs={[filterButtonRef]}>
                        <FiltersContainer
                            isOpen={isFiltersOpen}
                            onClose={() => { setIsFiltersOpen(false); }}
                            status={filters.showStatus}
                            onStatusClick={(item) => { handleStatusFilterClick(item, filters.showStatus[item]); }}
                        />
                    </ClickOutsideDetector>
                </div>

                <SimpleInput 
                    value={searchTerm}
                    onChange={handleSearch}
                    wrapperClassName={[
                        "search-input",
                        !searchTerm ? "inactive" : undefined,
                    ].filter(Boolean).join(" ")}
                    placeholder="Search Instance"
                    autoCorrect="off"
                    autoComplete="off"
                    spellCheck="false"
                    leftIcon={<ElevaiteIcons.SVGMagnifyingGlass/>}
                    rightIcon={
                        <CommonButton
                            onClick={() => { handleSearch(""); }}
                            noBackground
                            disabled={!searchTerm}
                        >
                            <ElevaiteIcons.SVGXmark/>
                        </CommonButton>
                    }
                />

            </div>


            <div className="bottom-bar">
                {Object.keys(filters.showStatus).map((objectKey: AppInstanceStatus) => {
                    if (filters.showStatus[objectKey]) return (
                        <div key={objectKey} className="filter-pill-container">
                            <div className={[
                                "icon",
                                objectKey,
                            ].filter(Boolean).join(" ")}>
                                {getIcon(objectKey)}
                            </div>
                            {getLabel(objectKey)}
                            <CommonButton
                                onClick={() => { handleStatusFilterClick(objectKey, filters.showStatus[objectKey]); }}
                                noBackground
                            >
                                <ElevaiteIcons.SVGXmark/>
                            </CommonButton>
                        </div>
                    );
                    return null;
                })}
            </div>

        </div>
    );
}









interface FiltersContainerProps {
    isOpen: boolean;
    onClose?: () => void;
    status: StatusDisplay;
    onStatusClick: (item: AppInstanceStatus) => void;
}


function FiltersContainer(props: FiltersContainerProps): JSX.Element {
    const [isStatusOpen, setIsStatusOpen] = useState(true);


    return (
        <div className={[
            "filters-container-accordion",
            props.isOpen ? "open" : undefined
        ].filter(Boolean).join(" ")}>
            <div className="filters-container">
                <div className="filters-content">
                    <span className="filters-title">Filters</span>

                    <div className={[
                        "filters-section-header",
                        isStatusOpen ? "open" : undefined,
                    ].filter(Boolean).join(" ")}>
                        <CommonButton onClick={() => { setIsStatusOpen(current => !current); }}>
                            <ElevaiteIcons.SVGChevron/>
                            <span>Status</span>
                        </CommonButton>
                    </div>

                    <div className={[
                        "filters-section-accordion",
                        isStatusOpen ? "open" : undefined,
                    ].filter(Boolean).join(" ")}>
                        <div className="filters-section-container">
                            {Object.keys(props.status).map((objectKey: AppInstanceStatus) => 
                                <CommonButton
                                    key={objectKey}
                                    className={[
                                        "filter-button",
                                        objectKey,
                                        props.status[objectKey] ? "active" : undefined,
                                    ].filter(Boolean).join(" ")}
                                    onClick={() => { props.onStatusClick(objectKey); }}
                                    title={`Toggle the visibility of ${getLabel(objectKey)} instances.`}
                                >
                                    {getIcon(objectKey)}
                                    <span>{getLabel(objectKey)}</span>
                                </CommonButton>
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}




function getIcon(item: AppInstanceStatus): React.ReactNode {
    switch(item) {
        case AppInstanceStatus.COMPLETED: return <ElevaiteIcons.SVGCheckmark/>;
        case AppInstanceStatus.RUNNING: return <ElevaiteIcons.SVGInstanceProgress/>;
        case AppInstanceStatus.FAILED: return <ElevaiteIcons.SVGWarning/>;
        case AppInstanceStatus.STARTING: return <ElevaiteIcons.SVGTarget/>;
    }
}

function getLabel(item: AppInstanceStatus): string {    
    switch(item) {
        case AppInstanceStatus.COMPLETED: return "Completed";
        case AppInstanceStatus.RUNNING: return "Running";
        case AppInstanceStatus.FAILED: return "Interrupted";
        case AppInstanceStatus.STARTING: return "Initializing";
    }
}
