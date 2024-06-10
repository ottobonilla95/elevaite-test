import { CommonButton, CommonDatePicker, CommonFormLabels, CommonSelect, ElevaiteIcons, type CommonSelectOption } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useCost } from "../../../lib/contexts/CostContext";
import { type FilterGroupStructure, type FilterUnitStructure } from "../../../lib/interfaces";
import "./CostSidebar.scss";


const DEFAULT_ACCOUNTS_VALUE = "All";



export function CostSidebar(): JSX.Element {
    const costContext = useCost();
    const [accountOptions, setAccountOptions] = useState<CommonSelectOption[]>([]);

    useEffect(() => {
        if (!costContext.costDetails.uniqueAccounts) return;

        const formattedAccounts = costContext.costDetails.uniqueAccounts.map(item => { return {
            value: item,
        }; });
        formattedAccounts.unshift({value: DEFAULT_ACCOUNTS_VALUE});
        setAccountOptions(formattedAccounts);
    }, [costContext.costDetails]);


    function handleAccountChange(value: string): void {
        costContext.filterByAccount(value);
    }

    function handleDateChange(date: string): void {
        costContext.setSelectedDate(dayjs(date).toISOString());
    }

    function handleGroupClick(group: string): void {
        costContext.toggleFilterGroup(group);
    }

    function handleGroupClear(group: string): void {
        costContext.clearFiltersOfGroup(group);
    }

    function handleAllClear(): void {
        costContext.clearAllFilters();
    }

    function handleFilterClick(filter: string, group: string): void {
        costContext.toggleFilterOfGroup(filter, group);        
    }



    return (
        <div className="cost-sidebar-container">
            <div className="parameters-container">
                <span>Parameters</span>
                <CommonFormLabels
                    className="parameter-item"
                    label="Account"
                >
                    <CommonSelect
                        options={accountOptions}
                        onSelectedValueChange={handleAccountChange}
                        defaultValue={DEFAULT_ACCOUNTS_VALUE}
                        callbackOnDefaultValue
                    />
                </CommonFormLabels>
                <CommonFormLabels
                    className="parameter-item"
                    label="Month"
                >                    
                    <CommonDatePicker
                        selectedDate={costContext.selectedDate}
                        onDateChange={handleDateChange}
                        monthOnly
                        customInput={
                            <div className="month-picker-wrapper">
                                <CommonButton
                                    className="month-picker-button"
                                >
                                    {dayjs(costContext.selectedDate).format("MMMM YYYY")}
                                    <ElevaiteIcons.SVGDatePicker/>
                                </CommonButton>
                            </div>
                        }
                    />
                </CommonFormLabels>
            </div>
            <div className="filters-container">
                <div className="header-bar">
                    <span>Additional Filters</span>
                    {costContext.activeFiltersCount <= 0 ? 
                        <span className="clear-all-info">No active filters</span>
                    :
                        <CommonButton
                            className="clear-all-button"
                            onClick={handleAllClear}
                            noBackground
                        >
                            <span>{`Clear All (${costContext.activeFiltersCount.toString()}) Filters`}</span>
                        </CommonButton>
                    }
                </div>
                <div className="filters-scroller">
                    <div className="filters-content">
                        {costContext.filtering.filters.map(filter => 
                            <SidebarFilterGroup
                                key={filter.label}
                                filter={filter}
                                onGroupClick={handleGroupClick}
                                onGroupClear={handleGroupClear}
                                onFilterClick={handleFilterClick}
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}





interface SidebarFilterGroupProps {
    filter: FilterUnitStructure | FilterGroupStructure;
    onGroupClick: (group: string) => void;
    onGroupClear: (group: string) => void;
    onFilterClick: (filter: string, group: string) => void;
}

function SidebarFilterGroup(props: SidebarFilterGroupProps): React.ReactNode {
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);

    useEffect(() => {
        if (!("filters" in props.filter)) return;
        setActiveFiltersCount(props.filter.filters.filter(item => item.isActive).length)
    }, [props.filter]);

    function handleGroupClick(): void {
        props.onGroupClick(props.filter.label);
    }

    function handleGroupClear(): void {
        props.onGroupClear(props.filter.label);
    }

    function handleClick(filterLabel: string): void {
        props.onFilterClick(filterLabel, props.filter.label);
    }


    if (!("filters" in props.filter)) return undefined;
    return (
        <div className={["sidebar-filter-group-container", !props.filter.isClosed ? "open" : undefined].filter(Boolean).join(" ")}>
            <div className="sidebar-filter-group-header">
                <CommonButton
                    className="sidebar-filter-group-chevron"
                    onClick={handleGroupClick}
                    noBackground
                >
                    <ElevaiteIcons.SVGChevron/>
                </CommonButton>
                <CommonButton
                    className="sidebar-filter-header-title"
                    onClick={handleGroupClick}
                >
                    <span>{props.filter.label}</span>
                </CommonButton>
                {activeFiltersCount <= 0 ? undefined :
                    <CommonButton
                        className="sidebar-filter-clear"
                        onClick={handleGroupClear}
                        title={`Clear all filters of "${props.filter.label}"`}
                    >
                        {`Clear ${activeFiltersCount.toString()}`}
                    </CommonButton>
                }
            </div>
                <div className="sidebar-filter-list-accordion-container">
                    <div className="sidebar-filter-list-accordion">
                        <div className="sidebar-filter-list">
                            {props.filter.filters.map(filter =>
                                <CommonButton
                                    key={filter.label}
                                    className={[
                                        "sidebar-filter-button",
                                        filter.isSelected ? "selected" : undefined,
                                        filter.isActive ? "active" : undefined].filter(Boolean).join(" ")}
                                    onClick={() => { handleClick(filter.label); }}
                                >
                                    {filter.label}
                                </CommonButton>
                            )}
                        </div>
                    </div>
                </div>
        </div>
    );
}
