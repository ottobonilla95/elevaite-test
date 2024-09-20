"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { CreateProject, getContractProjectById, getContractProjectsList, submitContract } from "../actions/contractActions";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractExtractionDictionary, type ContractObject, type ContractProjectObject } from "../interfaces";



const exampleExtractedData: ContractExtractionDictionary = {
    "page_0": {
        "Invoice Number": "119329",
        "Invoice Date": "28-06-2023",
        "Due Date": "27-08-2023",
        // "Items": [
        //     {
        //     "Item": "High-speed internet router",
        //     "Quantity": "5",
        //     "Rate": "$500.00",
        //     "Total Value": "$2,500.00",
        //     },
        //     {
        //     "Item": "Data storage server",
        //     "Quantity": "5",
        //     "Rate": "$1,500.00",
        //     "Total Value": "$7,500.00",
        //     },
        //     {
        //     "Item": "High-performance laptops",
        //     "Quantity": "5",
        //     "Rate": "$1,000.00",
        //     "Total Value": "$5,000.00",
        //     }
        // ],
        "Subtotal": "$15,000.00",
        "Others": "$0.00",
        "VAT": "10%",
        "Total": "$16,500.00"
    }
}


const testContracts: ContractObject[] = [
    // {id: "01", label: "Test Invoice Label 01", filename: "Test Invoice 01", status: CONTRACT_STATUS.COMPLETED, content_type: CONTRACT_TYPES.INVOICE, file_ref: "/testPdf.pdf", response: exampleExtractedData, filesize: 24000, tags: ["Finance"], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "02", label: "Test Contract Label 01", filename: "Test Contract 01", status: CONTRACT_STATUS.COMPLETED, content_type: CONTRACT_TYPES.VSOW, file_ref: "/TC02.pdf", response: exampleExtractedData, filesize: 24000, tags: ["Tech"], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "03", label: "Test Purchase Order Label 01", filename: "Test Purchase Order 01", status: CONTRACT_STATUS.PROCESSING, content_type: CONTRACT_TYPES.PURCHASE_ORDER, file_ref: null, response: null, filesize: 24000, tags: [], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "04", label: "Test Purchase Order Label 02", filename: "Test Purchase Order 02", status: CONTRACT_STATUS.COMPLETED, content_type: CONTRACT_TYPES.PURCHASE_ORDER, file_ref: "/testPdf.pdf", response: exampleExtractedData, filesize: 24000, tags: ["Finance"], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "05", label: "Test Invoice Label 02", filename: "Test Invoice 02", status: CONTRACT_STATUS.FAILED, content_type: CONTRACT_TYPES.INVOICE, file_ref: null, response: null, filesize: 24000, tags: ["Finance", "Tech"], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "06", label: "", filename: "Test Contract 02", status: CONTRACT_STATUS.COMPLETED, content_type: CONTRACT_TYPES.VSOW, file_ref: "/testPdf.pdf", response: exampleExtractedData, filesize:24000, tags: [], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
    // {id: "07", label: "Test Contract Label 03", filename: "Test Contract 03", status: CONTRACT_STATUS.COMPLETED, content_type: CONTRACT_TYPES.VSOW, file_ref: "/TC03.pdf", response: exampleExtractedData, filesize: 24000, tags: [], creation_date: new Date().toISOString(), checksum: "", project_id: 0},
];


const testProjects: ContractProjectObject[] = [
    {
        id: 1,
        name: "Test Project",
        description: "This is a test project",
        creation_date: new Date().toISOString(),
        reports: testContracts,
    },
    {
        id: 2,
        name: "Empty Test Project",
        description: "This is an empty project",
        creation_date: new Date().toISOString(),
        reports: [],
    },
    {
        id: 4,
        name: "Second Empty Test Project",
        description: "This is an empty project with a much larger description, just to show how this is going to be handled",
        creation_date: new Date().toISOString(),
        reports: [],
    },
    {
        id: 5,
        name: "Another Empty Test Project",
        description: "This is an empty project",
        creation_date: new Date().toISOString(),
        reports: [],
    },
];



// STATIC OBJECTS

const defaultLoadingList: LoadingListObject = {
    projects: undefined,
    contracts: undefined,
    submittingContract: false,
};



// INTERFACES

interface LoadingListObject {
    projects: boolean|undefined;
    contracts: boolean|undefined;
    submittingContract: boolean;
}





// STRUCTURE 

export interface ContractsContextStructure {
    projects: ContractProjectObject[];
    selectedProject: ContractProjectObject|undefined;
    setSelectedProjectById: (id: string|number|undefined) => void;
    selectedContract: ContractObject | undefined;
    setSelectedContract: (contract: ContractObject|undefined) => void;
    changeSelectedContractBit: (pageKey: `page_${number}`, itemKey: string, newValue: string) => void;
    changeSelectedContractTableBit: (pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]) => void;
    submitCurrentContractPdf: (pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string) => void;
    createProject: (name: string, description?: string) => Promise<boolean>;
    loading: LoadingListObject;
}



export const ContractsContext = createContext<ContractsContextStructure>({
    projects: [],
    selectedProject: undefined,
    setSelectedProjectById: () => {/**/},
    selectedContract: undefined,
    setSelectedContract: () => {/**/},
    changeSelectedContractBit: () => {/**/},
    changeSelectedContractTableBit: () => {/**/},
    submitCurrentContractPdf: () => undefined,
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    createProject: async () => { return false; },
    loading: defaultLoadingList,
});




// FUNCTIONS









// PROVIDER

interface ContractsContextProviderProps {
    children: React.ReactNode;
}


export function ContractsContextProvider(props: ContractsContextProviderProps): JSX.Element {
    const [projects, setProjects] = useState<ContractProjectObject[]>([]);
    const [selectedProject, setSelectedProject] = useState<ContractProjectObject|undefined>();
    const [selectedContract, setSelectedContract] = useState<ContractObject|undefined>();
    const [processedContract, setProcessedContract] = useState<{id: string, data: ContractObject}|undefined>();
    const [hasCurrentContractFailed, setHasCurrentContractFailed] = useState("");
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);
    
    const selectedContractChangedByUser = useRef<boolean>();



    useEffect(() => {
        void actionFetchProjectsList();
    }, []);


    useEffect(() => {
        if (!selectedProject) return;
        const newSelection = projects.find(item => item.id === selectedProject.id);
        setSelectedProject(newSelection);
    }, [projects]);


    // useEffect(() => {
    //     console.log("Selected Project", selectedProject);
    // }, [selectedProject]);

    useEffect(() => {
        console.log("Selected Contract", selectedContract);
    }, [selectedContract]);


    useEffect(() => {       
        if (!processedContract) return;
        replaceTemporaryContractWithProcessed(processedContract.id, processedContract.data);
    }, [processedContract]);


    useEffect(() => {
        if (!hasCurrentContractFailed) return;
        changeStatusToContractInList(hasCurrentContractFailed, CONTRACT_STATUS.FAILED);
    }, [hasCurrentContractFailed]);




    function setSelectedProjectById(id: string|number|undefined): void {
        if (projects.length === 0) return;
        if (id === undefined) {
            setSelectedProject(undefined);
            return;
        }
        const foundProject = projects.find(item => item.id === id);
        if (foundProject) setSelectedProject(foundProject);
    }

    function changeSelectedContractBit(pageKey: `page_${number}`, itemKey: string, newValue: string): void {
        selectedContractChangedByUser.current = true;
        setSelectedContract(current => { 
            if (!current) return;
            const oldData = current.response;
            const newData: ContractExtractionDictionary|null = oldData === null ? null : {
                ...oldData,
                [pageKey]: {
                    ...oldData[pageKey],
                    [itemKey]: newValue
                }
            };
            return {...current, extractedData: newData};
        });
    }

    function changeSelectedContractTableBit(pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]): void {
        selectedContractChangedByUser.current = true;
        setSelectedContract(current => { 
            if (!current) return;
            const oldData = current.response;
            const newData: ContractExtractionDictionary|null = oldData === null ? null : {
                ...oldData,
                [pageKey]: {
                    ...oldData[pageKey],
                    [tableKey]: newTableData
                }
            };
            return {...current, extractedData: newData};
        });
    }




    function submitCurrentContractPdf(pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string): void {;
        if (pdf) {
            void actionSubmitContract(pdf, type, projectId, name);
        }
    }

    function appendContractToContractsList(project: ContractProjectObject, pdf: File, type: CONTRACT_TYPES, name?: string): string {
        const id = `NewContract_${project.id.toString()}_${(project.reports.length + 1).toString()}`;

        const newContract: ContractObject = {
            id,
            project_id: selectedProject?.id ?? "none",
            status: CONTRACT_STATUS.PROCESSING,
            content_type: type,
            label: name,
            filename: pdf.name,
            filesize: pdf.size,
            file_ref: pdf,
            response: null,
            tags: [],
            creation_date: new Date().toISOString(),
            checksum: "",
        }

        setProjects((prevProjects) =>
            prevProjects.map((currentProject) =>
                currentProject.id === project.id ?
                    { ...currentProject, reports: [...currentProject.reports, newContract] }
                    : currentProject
            )
        );
        return id;
    }

    function replaceProject(newProject: ContractProjectObject): void {
        setProjects((prevProjects) =>
            prevProjects.map((project) => project.id === newProject.id ? newProject : project)
        );
    }

    function replaceTemporaryContractWithProcessed(id: string, data: ContractObject): void {
        // If the returned data's id exists, replace it, then delete the previous id.
        const existingReport = findReportById(data.id);
        if (existingReport) {
            // Replace the data of the original report (data.id)
            setProjects((currentProjects) =>
                currentProjects.map((project) => ({
                    ...project,
                    reports: project.reports.map((report) =>
                        report.id === data.id ? data : report
                    ),
                }))
            );
            // Delete the temporary line item (id)
            setProjects((prevProjects) =>
                prevProjects.map((project) => ({
                    ...project,
                    reports: project.reports.filter((report) => report.id !== id),
                }))
            );
        }

        // Otherwise, replace the previous id with the new item
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports.map((report) =>
                    report.id === id ? data : report
                ),
            }))
        );

        function findReportById(itemId: string|number): ContractObject|undefined {
            for (const project of projects) {
                const foundItem = project.reports.find((report) => report.id === itemId);
                if (foundItem) { return foundItem; }
            } return undefined;
          };
    }

    function changeStatusToContractInList(id: string, status: CONTRACT_STATUS): void {
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports.map((report) =>
                    report.id === id ? { ...report, status } : report
                ),
            }))
        );
    }




    async function actionSubmitContract(submittedPdf: File, type: CONTRACT_TYPES, projectId: string|number, name?: string): Promise<void> {
        if (!selectedProject) return;
        setHasCurrentContractFailed("");
        const idOfNewEntry = appendContractToContractsList(selectedProject, submittedPdf, type, name);
        try {
            setLoading(current => { return {...current, submittingContract: true}} );
            const formData = new FormData();
            formData.append("file", submittedPdf);
            if (name) formData.append("label", name);
            const contractExtractionResults = await submitContract(projectId.toString(), formData, type);
            setProcessedContract({id: idOfNewEntry, data: contractExtractionResults});
            await actionFetchProjectById(projectId);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in submitting contract:", error);
            setHasCurrentContractFailed(idOfNewEntry);
        } finally {
            setLoading(current => { return {...current, submittingContract: false}} );
        }
    }

    async function actionCreateProject(name: string, description?: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const createProjectResult = await CreateProject(name, description);
            setProjects(current => [...current, createProjectResult]);
            return true;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in creating contract project:", error);
            return false;
        } finally {
            setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionFetchProjectsList(): Promise<void> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const projectsListResults = await getContractProjectsList();
            setProjects(projectsListResults);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract projects:", error);
        } finally {
            setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionFetchProjectById(id: string|number): Promise<void> {
        try {
            // setLoading(current => { return {...current, projects: true}} );
            // Stealth update            
            const projectResult = await getContractProjectById(id.toString());
            replaceProject(projectResult);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract projects:", error);
        } finally {
            // setLoading(current => { return {...current, projects: false}} );
        }
    }







  
    return (
        <ContractsContext.Provider
            value={ {
                projects,
                selectedProject,
                setSelectedProjectById,
                selectedContract,
                setSelectedContract,
                changeSelectedContractBit,
                changeSelectedContractTableBit,
                submitCurrentContractPdf,
                createProject: actionCreateProject,
                loading,
            } }
        >
            {props.children}
        </ContractsContext.Provider>
    );
}

  
export function useContracts(): ContractsContextStructure {
    return useContext(ContractsContext);
}