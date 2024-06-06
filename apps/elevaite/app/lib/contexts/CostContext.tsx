"use client";
import { localeSort } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { createContext, useContext, useEffect, useState } from "react";
import { countActiveFilters } from "../helpers";
import { type FiltersStructure, type SortingObject } from "../interfaces";
import { TEST_COST_DATA, type TestCostDataObject } from "./CostContextTestData";





// ENUMS

export enum specialHandlingCostFields {
    TAGS = "tags",
    DATE = "date",
    AMOUNT = "amount",
    FRACTION_AMOUNT = "amountFraction",
    PRICE = "price",
    MODEL = "model",
}

export enum costBarChartAxisValues {
    COST = "cost",
    TOKENS = "tokens",
    GPU = "gpu",
}


// STATIC OBJECTS


// const defaultLoadingList: LoadingListObject = {
//     test: false,
// };


// This should keep the rgba notation.
enum BarChartBaseColors {
    Red = "rgba(201, 66, 66, 1)",
    Purple = "rgba(111, 134, 255, 1)",
    Pink = "rgba(220, 24, 156, 1)",
    Yellow = "rgba(255, 212, 122, 1)",
    Green = "rgba(123, 246, 0, 1)",
    Cyan = "rgba(63, 209, 246, 1)",
};

const filterStructureFoundation: {label: string; field: string}[] = [
    { label: "Project", field: "project", },
    { label: "Billing Type", field: "billingType", },
    { label: "Model Provider", field: "modelProvider", },
    { label: "Model", field: "modelId", },
];



// INTERFACES

// interface LoadingListObject {
//     test: boolean;
// }

export interface CostDetails {
    totalCost?: number;
    totalGpu?: number;
    totalTokens?: number;
    uniqueAccounts?: string[];
    uniqueModels?: string[];
    uniqueProjects?: string[];
}






// FUNCTIONS

function getBarChartColor(index: number): string {
    const colors = Object.values(BarChartBaseColors);
    const maxColors = colors.length;
    const degreeOfOpacityShift = 0.25;

    if (index < 0) {
        return "rgba(0, 0, 0, 1)";
    } else if (index <= maxColors) {
        return colors[index - 1];
    } 
    const baseIndex = (index - 1) % maxColors;
    const opacityReductionFactor = Math.floor((index - 1) / maxColors) * degreeOfOpacityShift;
    return reduceOpacity(colors[baseIndex], opacityReductionFactor);

    function reduceOpacity(rgba: string, factor: number): string {
        const rgbaPattern = /rgba\((?<r>\d+), (?<g>\d+), (?<b>\d+), (?<a>[\d.]+)\)/;
        const rgbaParts = rgbaPattern.exec(rgba);
        if (rgbaParts) {
            const [_, r, g, b, a] = rgbaParts;
            const newOpacity = Math.max(0, parseFloat(a) - factor);
            return `rgba(${r}, ${g}, ${b}, ${newOpacity.toString()})`;
        }
        return rgba;
    }
}

function getCostOfItem(item: TestCostDataObject): number {
    // Just extrapolating to a month for now.
    return 30 * item.cost;
}

function sortDisplayCostData(costData: TestCostDataObject[], sorting: SortingObject<TestCostDataObject>, specialHandling?: specialHandlingCostFields): TestCostDataObject[] {

    switch (specialHandling) {
        case specialHandlingCostFields.DATE:
            costData.sort((a,b) => dayjs(a.inferenceDate).valueOf() - dayjs(b.inferenceDate).valueOf());
            break;
        default:
            if (sorting.field) {
                costData.sort((a,b) => {
                    if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field]))
                        return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
                    else if (sorting.field && a[sorting.field] && b[sorting.field] && typeof a[sorting.field] === "number" && typeof b[sorting.field] === "number") {
                        return (a[sorting.field] as number) - (b[sorting.field] as number);
                    }
                    return 0;
                })
            } else {
                costData.sort((a,b) => (a.project.toString()).localeCompare(b.project.toString()));
            }
    }

    if (sorting.isDesc) {
        costData.reverse();
    }
    return costData;
}




// STRUCTURE 

export interface CostContextStructure {
    costData: TestCostDataObject[];
    costDetails: CostDetails;
    getBarColor: (modelId: string) => string;
    costBarChartAxis: costBarChartAxisValues;
    setCostBarChartAxis: (axis: costBarChartAxisValues) => void;
    getValueOfModelPerProject: (modelId: string, axis?: costBarChartAxisValues) => number[];
    costSorting: SortingObject<TestCostDataObject>;
    sortCostData: (field: string, specialHandling?: string) => void;
    filterByAccount: (account: string) => void;
    filtering: FiltersStructure;
    activeFiltersCount: number;
    toggleFilterGroup: (group: string) => void;
    toggleFilterOfGroup: (filter: string, group: string) => void;
    clearFiltersOfGroup: (group: string) => void;
    clearAllFilters: () => void;
}


export const CostContext = createContext<CostContextStructure>({
    costData: [],
    costDetails: {},
    getBarColor: () => "",
    costBarChartAxis: costBarChartAxisValues.COST,
    setCostBarChartAxis: () => {/**/},
    getValueOfModelPerProject: () => [],
    costSorting: {field: undefined},
    sortCostData: () => {/**/},
    filterByAccount: () => {/**/},
    filtering: {filters:[]},
    activeFiltersCount: 0,
    toggleFilterGroup: () => {/**/},
    toggleFilterOfGroup: () => {/**/},
    clearFiltersOfGroup: () => {/**/},
    clearAllFilters: () => {/**/},
});




// PROVIDER

interface CostContextProviderProps {
    children: React.ReactNode;
}

export function CostContextProvider(props: CostContextProviderProps): JSX.Element {
    const [costData, setCostData] = useState<TestCostDataObject[]>([]);
    const [displayCostData, setDisplayCostData] = useState<TestCostDataObject[]>([]);
    const [costDetails, setCostDetails] = useState<CostDetails>({});
    const [costBarChartAxis, setCostBarChartAxis] = useState(costBarChartAxisValues.COST)
    const [sorting, setSorting] = useState<SortingObject<TestCostDataObject>>({field: undefined});
    const [filtering, setFiltering] = useState<FiltersStructure>({filters: []});
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);
    const [selectedAccount, setSelectedAccount] = useState("");


    useEffect(() => {
        setCostData(TEST_COST_DATA);
    }, []);

    useEffect(() => {
        calculateCostCounts(costData);
        setDisplayCostData(formatDisplayData());
    }, [costData]);

    useEffect(() => {
        constructFilters(costData);
    }, [costData]); // Add loading === false when loading is implemented.

    useEffect(() => {        
        setDisplayCostData(formatDisplayData());
    }, [selectedAccount]);

    useEffect(() => {
        setActiveFiltersCount(countActiveFilters(filtering));
        filterCostData();
        // console.log("Filtering:", filtering);
        // filterDatasets();
    }, [filtering]);

    

    // useEffect(() => {
    //     console.log("Display Data:", displayCostData);        
    // }, [displayCostData]);



    function formatDisplayData(): TestCostDataObject[] {   
        const costDataClone = JSON.parse(JSON.stringify(costData)) as TestCostDataObject[];
        const adjustedCostData = costDataClone.filter(item => !selectedAccount || selectedAccount === "All" || item.account === selectedAccount);
        // setDisplayCostData();
        return sortDisplayCostData(adjustedCostData, sorting);
    }


    function filterCostData(): void {
        const allCostData = formatDisplayData();
        const filteredCostData: TestCostDataObject[] = [];

        // If there are no active filters, reset the list
        if (countActiveFilters(filtering) === 0) {
            setDisplayCostData(allCostData);
            return;
        }

        // For each item decide if to add it or not.
        for (const costItem of allCostData) {            
            const show: boolean[] = [];

            // For each field covered by filtering
            for (const filterGroup of filtering.filters) {
                if ("field" in filterGroup && filterGroup.field) {
                    if (filterGroup.filters.filter(item => item.isActive).length === 0) continue;
                    const label = costItem[filterGroup.field] as string;
                    if (label) {
                        const specificFilter = filterGroup.filters.find(filterItem => filterItem.label === label);
                        if (specificFilter?.isActive) show.push(true);
                        else show.push(false);
                    }
                }                
            }
            if (!(show.some(item => !item))) filteredCostData.push(costItem);
        }
        setDisplayCostData(filteredCostData);
    }



    function constructFilters(data: TestCostDataObject[]): void {
        const constructedFilters: FiltersStructure = {
            label: "Filters",
            filters: filterStructureFoundation.map(item => { return {
                label: item.label,
                field: item.field,
                isClosed: true,
                filters: getUniqueValues(data, item.field).sort((a, b) => a.localeCompare(b)).map(unique => { return {
                    label: unique,
                    isSelected: false,
                    isActive: false,
                }; }),
            }; })
        };
        setFiltering(constructedFilters);
    }

    function getUniqueValues(data: TestCostDataObject[], field: string): string[] {
        const itemsSet = new Set<string>();
        data.map(dataItem => {
            if (dataItem[field] && typeof dataItem[field] === "string") return itemsSet.add(dataItem[field] as string);
            return undefined;
        })
        return Array.from(itemsSet).sort();
    }

    function toggleFilterGroup(group: string): void {
        setFiltering(prevSorting => ({
            ...prevSorting,
            filters: prevSorting.filters.map(foundGroup => {
              if ("filters" in foundGroup && foundGroup.label === group) {
                return {
                  ...foundGroup,
                  isClosed: !foundGroup.isClosed
                };
              }
              return foundGroup;
            })
        }));
    }

    function toggleFilterOfGroup(filter: string, group: string): void {
        setFiltering(prevSorting => ({
            ...prevSorting,
            filters: prevSorting.filters.map(foundFilter => {
              if ('filters' in foundFilter && foundFilter.label === group) {
                return {
                  ...foundFilter,
                  filters: foundFilter.filters.map(subFilter => {
                    if (subFilter.label === filter) {
                      return {
                        ...subFilter,
                        isActive: !subFilter.isActive
                      };
                    }
                    return subFilter;
                  })
                };
              }
              return foundFilter;
            })
        }));
    }

    function clearGroup(group: string): void {
        setFiltering(prevFiltering => ({
            ...prevFiltering,
            filters: prevFiltering.filters.map(filter => {
              if ('filters' in filter && filter.label === group) {
                return {
                  ...filter,
                  filters: filter.filters.map(subFilter => ({
                    ...subFilter,
                    isActive: false
                  }))
                };
              }
              return filter;
            })
        }));
    }

    function clearAll(): void {
        setFiltering(prevFiltering => ({
            ...prevFiltering,
            filters: prevFiltering.filters.map(filter => {
                if ('filters' in filter) {
                    return {
                        ...filter,
                        filters: filter.filters.map(subFilter => ({
                            ...subFilter,
                            isActive: false
                        }))
                    };
                } 
                return {
                    ...filter,
                    isActive: false
                };
            })
        }));
    }


    function calculateCostCounts(table: TestCostDataObject[]): void {
        let totalCost = 0;
        let totalGpu = 0;
        let totalTokens = 0;
        for (const i of table) { 
            totalCost += getCostOfItem(i);
            totalGpu += i.gpu ?? 0;
            totalTokens += i.tokensIn + (i.tokensOut ?? 0);
        }
        const uniqueAccounts = Array.from(new Set(table.map((item) => item.account)));
        localeSort(uniqueAccounts);
        const uniqueModels = Array.from(new Set(table.map((item) => item.modelId)));
        localeSort(uniqueModels);
        const uniqueProjects = Array.from(new Set(table.map((item) => item.project)));
        localeSort(uniqueProjects);

        setCostDetails({
            totalCost,
            totalGpu,
            totalTokens,
            uniqueAccounts,
            uniqueModels,
            uniqueProjects,
        })
    }

    function getBarColor(modelId: string): string {
        const index = costDetails.uniqueModels?.findIndex(item => item === modelId);
        return getBarChartColor(index !== undefined ? (index + 1) : 0);
    }


    function getValueOfModelPerProject(modelId: string, axis?: costBarChartAxisValues): number[] {
        switch (axis) {
            case costBarChartAxisValues.TOKENS: return getTokensOfModelPerProject(modelId);
            case costBarChartAxisValues.GPU: return getGPUUsageOfModelPerProject(modelId);
            default: return getCostsOfModelPerProject(modelId);
        }
    }
    
    function getTokensOfModelPerProject(modelId: string): number[] {
        if (!costDetails.uniqueModels || !costDetails.uniqueProjects) return [];
        const tokensArray = costDetails.uniqueProjects.map(project => {
            let totalTokensIn = 0;
            let totalTokensOut = 0;
            for (const i of displayCostData) {
                if (i.project === project && i.modelId === modelId) {
                    totalTokensIn += i.tokensIn;
                    totalTokensOut += (i.tokensOut ?? 0);
                }
            }
            return [totalTokensIn, totalTokensOut];
        });
        return tokensArray.flat();
    }

    function getGPUUsageOfModelPerProject(modelId: string): number[] {
        if (!costDetails.uniqueModels || !costDetails.uniqueProjects) return [];
        const gpuArray = costDetails.uniqueProjects.map(project => {
            let totalGPUCost = 0;
            for (const i of displayCostData) {
                if (i.project === project && i.modelId === modelId)
                totalGPUCost += i.gpu ?? 0;
            }
            return totalGPUCost;
        });
        return gpuArray;
    }

    function getCostsOfModelPerProject(modelId: string): number[] {
        if (!costDetails.uniqueModels || !costDetails.uniqueProjects) return [];
        const costArray = costDetails.uniqueProjects.map(project => {
            let totalOfModelCost = 0;
            for (const i of displayCostData) {
                if (i.project === project && i.modelId === modelId)
                totalOfModelCost += getCostOfItem(i);
            }
            return totalOfModelCost;
        });
        return costArray;
    }




    
    function sortCostData(field: keyof TestCostDataObject, specialHandling?: specialHandlingCostFields): void {
        let sortingResult: SortingObject<TestCostDataObject> = {};
        if (sorting.field !== field) sortingResult = {field};
        if (sorting.field === field) {
            if (sorting.isDesc) sortingResult = {field: undefined};
            else sortingResult = {field, isDesc: true};
        }
        setSorting(sortingResult);
        
        if (displayCostData.length === 0) return;
        setDisplayCostData(sortDisplayCostData(displayCostData, sortingResult, specialHandling));
    }

    function filterByAccount(account: string): void {
        setSelectedAccount(account);
    }





    return(
        <CostContext.Provider
            value={ {
                costData: displayCostData,
                costDetails,
                getBarColor,
                costBarChartAxis,
                setCostBarChartAxis,
                getValueOfModelPerProject,
                costSorting: sorting,
                sortCostData,
                filterByAccount,
                filtering,
                activeFiltersCount,
                toggleFilterGroup,
                toggleFilterOfGroup,
                clearFiltersOfGroup: clearGroup,
                clearAllFilters: clearAll,
            } }
        >
            {props.children}
        </CostContext.Provider>
    )
}


export function useCost(): CostContextStructure {
    return useContext(CostContext);
}

