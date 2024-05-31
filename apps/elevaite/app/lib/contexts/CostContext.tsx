"use client";
import { localeSort } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { createContext, useContext, useEffect, useState } from "react";
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


// INTERFACES

// interface LoadingListObject {
//     test: boolean;
// }

interface SortingObject {
    field?: keyof TestCostDataObject;
    isDesc?: boolean;
}

export interface CostDetails {
    totalCost?: number;
    formattedCost?: string;
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



function sortDisplayCostData(costData: TestCostDataObject[], sorting: SortingObject, specialHandling?: specialHandlingCostFields): TestCostDataObject[] {

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
    getCostsOfModelPerProject: (modelId: string) => number[];
    costSorting: SortingObject;
    sortCostData: (field: string, specialHandling?: string) => void;
    filterByAccount: (account: string) => void;
}


export const CostContext = createContext<CostContextStructure>({
    costData: [],
    costDetails: {},
    getBarColor: () => "",
    getCostsOfModelPerProject: () => [],
    costSorting: {field: undefined},
    sortCostData: () => {/**/},
    filterByAccount: () => {/**/},
});




// PROVIDER

interface CostContextProviderProps {
    children: React.ReactNode;
}

export function CostContextProvider(props: CostContextProviderProps): JSX.Element {
    const [costData, setCostData] = useState<TestCostDataObject[]>([]);
    const [displayCostData, setDisplayCostData] = useState<TestCostDataObject[]>([]);
    const [costDetails, setCostDetails] = useState<CostDetails>({});
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});
    const [selectedAccount, setSelectedAccount] = useState("");


    useEffect(() => {
        setCostData(TEST_COST_DATA);
    }, []);

    useEffect(() => {
        calculateCostCounts(costData);
        formatDisplayData(costData);
    }, [costData]);


    useEffect(() => {
        formatDisplayData(costData.filter(item => !selectedAccount || selectedAccount === "All" || item.account === selectedAccount));
    }, [selectedAccount]);

    // useEffect(() => {
    //     console.log("Display Data:", displayCostData);        
    // }, [displayCostData]);



    function formatDisplayData(data: TestCostDataObject[]): void {        
        setDisplayCostData(JSON.parse(JSON.stringify(data)) as TestCostDataObject[]);
    }



    function calculateCostCounts(table: TestCostDataObject[]): void {
        let totalCost = 0;
        for (const i of table) { 
            totalCost += getCostOfItem(i);
        }
        // Formatting:
        const formattedCost = totalCost.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
        const uniqueAccounts = Array.from(new Set(table.map((item) => item.account)));
        localeSort(uniqueAccounts);
        const uniqueModels = Array.from(new Set(table.map((item) => item.modelId)));
        localeSort(uniqueModels);
        const uniqueProjects = Array.from(new Set(table.map((item) => item.project)));
        localeSort(uniqueProjects);

        setCostDetails({
            totalCost,
            formattedCost,
            uniqueAccounts,
            uniqueModels,
            uniqueProjects,
        })
    }

    function getBarColor(modelId: string): string {
        const index = costDetails.uniqueModels?.findIndex(item => item === modelId);
        return getBarChartColor(index !== undefined ? (index + 1) : 0);
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
        let sortingResult: SortingObject = {};
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
                getCostsOfModelPerProject,
                costSorting: sorting,
                sortCostData,
                filterByAccount,
            } }
        >
            {props.children}
        </CostContext.Provider>
    )
}


export function useCost(): CostContextStructure {
    return useContext(CostContext);
}

