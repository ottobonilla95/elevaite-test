"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { getAvailableDatasets, getDatasetTasks, getDatasets, registerDataset } from "../actions/datasetActions";
import { countActiveFilters, getUniqueActiveFiltersFromGroup, getUniqueTagsFromList } from "../helpers";
import { type FiltersStructure, type HuggingfaceDatasetObject, type ModelDatasetObject } from "../interfaces";



// ENUMS

export enum specialHandlingDatasetFields {
    TAGS = "tags",
    DATE = "date",
}

export enum FilterStructureLabels {
    TAGS = "Tags",
    TASKS = "Tasks",
}


// STATIC OBJECTS


const defaultLoadingList: LoadingListObject = {
    datasets: undefined,
    datasetTasks: undefined,
    availableDatasets: undefined,
    registerDataset: undefined,
    filtersStructure: undefined,
};


// INTERFACES

interface SortingObject {
    field?: keyof ModelDatasetObject;
    isDesc?: boolean;
}

interface LoadingListObject {
    datasets: boolean|undefined;
    datasetTasks: boolean|undefined;
    availableDatasets: boolean|undefined;
    registerDataset: boolean|undefined;
    filtersStructure: boolean|undefined;
}





// STRUCTURE 

export interface DatasetsContextStructure {
    datasets: ModelDatasetObject[];
    datasetTasks: string[],
    availableDatasets: HuggingfaceDatasetObject[];
    datasetSorting: SortingObject;
    sortDatasets: (field: string, specialHandling?: string) => void;
    getAvailableDatasetsByName: (name: string) => void;
    getAvailableDatasetsByTask: (task: string) => void;
    registerDataset: (datasetName: string, datasetRepo: string, tags?: string[]) => Promise<void>;
    filtering: FiltersStructure;
    activeFiltersCount: number;
    toggleFilter: (filterName: string) => void,
    toggleFilterGroup: (group: string) => void,
    loading: LoadingListObject;
}

export const DatasetsContext = createContext<DatasetsContextStructure>({
    datasets: [],
    datasetTasks: [],
    availableDatasets: [],
    datasetSorting: {field: undefined},
    sortDatasets: () => {/**/},
    getAvailableDatasetsByName: () => {/**/},
    getAvailableDatasetsByTask: () => {/**/},
    registerDataset: async () => {/**/},
    filtering: {filters:[]},
    activeFiltersCount: 0,
    toggleFilter: () => {/**/},
    toggleFilterGroup: () => {/**/},
    loading: defaultLoadingList,
});









// FUNCTIONS

function sortDisplayDatasets(datasets: ModelDatasetObject[], sorting: SortingObject, specialHandling?: specialHandlingDatasetFields): ModelDatasetObject[] {

    switch (specialHandling) {
        // case specialHandlingDatasetFields.DATE:
        //     datasets.sort((a,b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf());
        //     break;
        case specialHandlingDatasetFields.TAGS:
            datasets.sort((a,b) => a.tags.length > 0 === b.tags.length > 0 ? 0 : a.tags.length > 0 ? -1 : 1);
            break;
        default:
            if (sorting.field) {
                datasets.sort((a,b) => {
                    if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field]))
                    return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
                    return 0;
                })
            } else {
                datasets.sort((a,b) => (a.id.toString()).localeCompare(b.id.toString()));
            }
    }

    if (sorting.isDesc) {
        datasets.reverse();
    }
    return datasets;
}





// PROVIDER

interface DatasetsContextProviderProps {
    children: React.ReactNode;
}


export function DatasetsContextProvider(props: DatasetsContextProviderProps): JSX.Element {
    const [datasets, setDatasets] = useState<ModelDatasetObject[]>([]);
    const [displayDatasets, setDisplayDatasets] = useState<ModelDatasetObject[]>([]);
    const [datasetTasks, setDatasetTasks] = useState<string[]>([]);
    const [availableDatasets, setAvailableDatasets] = useState<HuggingfaceDatasetObject[]>([]);
    const [filtering, setFiltering] = useState<FiltersStructure>({filters: []});
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);
    
    
    
    useEffect(() => {
        setLoading(current => {return {...current, filtersStructure: true}} );
        void fetchDatasets();
        void fetchDatasetTasks();
        void fetchAvailableDatasets();
    }, []);

    useEffect(() => {
        if (loading.datasets === false && loading.datasetTasks === false && loading.filtersStructure) constructFilters(displayDatasets, datasetTasks);
    }, [displayDatasets, datasetTasks, loading.datasets, loading.datasetTasks]);

    useEffect(() => {     
        setDisplayDatasets(formatDisplayDatasets());
    }, [datasets]);

    useEffect(() => {
        setActiveFiltersCount(countActiveFilters(filtering));
        filterDatasets();
    }, [filtering]);



    function formatDisplayDatasets(): ModelDatasetObject[] {
        const datasetsClone = JSON.parse(JSON.stringify(datasets)) as ModelDatasetObject[];
        const adjustedDatasets = datasetsClone.map(model => {
            // Use this to modify the display datasets as needed
            return model;
        });
        return sortDisplayDatasets(adjustedDatasets, sorting);
    }


    function filterDatasets(): void {
        const allDatasets = formatDisplayDatasets();
        const filteredDatasets: ModelDatasetObject[] = [];

        // If there are no active filters, reset the list
        if (countActiveFilters(filtering) === 0) {
            setDisplayDatasets(allDatasets);
            return;
        }

        // Get all active tasks
        const activeTasks = getUniqueActiveFiltersFromGroup(filtering, FilterStructureLabels.TASKS);
        // // Get all active tags
        const activeTags = getUniqueActiveFiltersFromGroup(filtering, FilterStructureLabels.TAGS);

        // // For each item decide if to add it or not.
        for (const dataset of allDatasets) {
            let show = false;
            // console.log("Has task matches?", activeTasks.includes(dataset.task))
            // if (activeTasks.includes(dataset.task)) show = true;
            if (/** !show && */ dataset.tags.some(item => activeTags.includes(item))) show = true;

            if (show) filteredDatasets.push(dataset);
        }
        setDisplayDatasets(filteredDatasets);
    }


    function sortDatasets(field: keyof ModelDatasetObject, specialHandling?: specialHandlingDatasetFields): void {
        let sortingResult: SortingObject = {};
        if (sorting.field !== field) sortingResult = {field};
        if (sorting.field === field) {
            if (sorting.isDesc) sortingResult = {field: undefined};
            else sortingResult = {field, isDesc: true};
        }
        setSorting(sortingResult);
        
        if (displayDatasets.length === 0) return;
        setDisplayDatasets(sortDisplayDatasets(displayDatasets, sortingResult, specialHandling));
    }


    function constructFilters(passedDatasets: ModelDatasetObject[], tasks: string[]): void {
        const constructedFilters: FiltersStructure = { label: "Filters", filters: []};
        // Tags
        const uniqueTags = getUniqueTagsFromList(passedDatasets);
        constructedFilters.filters.push({
            label: FilterStructureLabels.TAGS,
            filters: uniqueTags.map(tag => { return { label: tag }; })
        })
        // Tasks
        constructedFilters.filters.push({
            label: FilterStructureLabels.TASKS,
            filters: tasks.map(task => { return { label: task }; })
        })        
        setFiltering(constructedFilters);
        setLoading(current => {return {...current, filtersStructure: false}} );
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

    function toggleFilter(filterName: string): void {
        setFiltering(prevSorting => ({
            ...prevSorting,
            filters: prevSorting.filters.map(foundFilter => {
              if ('filters' in foundFilter) {  // Check if it's a group
                return {
                  ...foundFilter,
                  filters: foundFilter.filters.map(subFilter => {
                    if (subFilter.label === filterName) {
                      return {
                        ...subFilter,
                        isActive: !subFilter.isActive
                      };
                    }
                    return subFilter;
                  })
                };
              } else if (foundFilter.label === filterName) {  // If it's a single filter
                return {
                  ...foundFilter,
                  isActive: !foundFilter.isActive
                };
              }
              return foundFilter;
            })
        }));
    }



    async function fetchDatasets(): Promise<void> {
        try {
            setLoading(current => {return {...current, datasets: true}} );
            const fetchedDatasets = await getDatasets();
            setDatasets(fetchedDatasets);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching models:", error);
        } finally {                
            setLoading(current => {return {...current, datasets: false}} );
        }
    }

    async function fetchAvailableDatasets(name?: string, task?: string, author?: string): Promise<void> {
        if (!name && !task && !author) return;
        try {
            setLoading(current => {return {...current, availableDatasets: true}} );
            const input = { datasetName: "", task: "", author: "" };
            if (name) input.datasetName = name;
            if (task) input.task = task;
            if (author) input.author = author;
            const fetchedAvailableDatasets = await getAvailableDatasets(input);
            setAvailableDatasets(fetchedAvailableDatasets);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching models:", error);
        } finally {                
            setLoading(current => {return {...current, availableDatasets: false}} );
        }
    }

    function fetchAvailableDatasetsByName(name: string): void {
        void fetchAvailableDatasets(name, undefined, undefined);
    }

    function fetchAvailableDatasetsByTask(task: string): void {
        void fetchAvailableDatasets(undefined, task, undefined);
    }

    async function fetchDatasetTasks(): Promise<void> {
        try {
            setLoading(current => {return {...current, datasetTasks: true}} );
            const fetchedDatasetTasks = await getDatasetTasks();
            fetchedDatasetTasks.sort();
            setDatasetTasks(fetchedDatasetTasks);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching dataset tasks:", error);
        } finally {                
            setLoading(current => {return {...current, datasetTasks: false}} );
        }
    }


    async function actionRegisterDataset(datasetName: string, datasetRepo: string, tags?: string[]): Promise<void> {
        try {
            setLoading(current => {return {...current, registerDataset: true}} );
            const result = await registerDataset(datasetName, datasetRepo, tags);
            setDatasets(current => [...current, result]);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected dataset parameters:", error);
        } finally {
            setLoading(current => {return {...current, registerDataset: false}} );
        }
    }




  
    return (
        <DatasetsContext.Provider
            value={ {
                datasets: displayDatasets,
                datasetTasks,
                availableDatasets,
                datasetSorting: sorting,
                sortDatasets,
                getAvailableDatasetsByName: fetchAvailableDatasetsByName,
                getAvailableDatasetsByTask: fetchAvailableDatasetsByTask,
                registerDataset: actionRegisterDataset,
                filtering,
                activeFiltersCount,
                toggleFilter,
                toggleFilterGroup,
                loading,
            } }
        >
            {props.children}
        </DatasetsContext.Provider>
    );
}
  
export function useDatasets(): DatasetsContextStructure {
    return useContext(DatasetsContext);
}

