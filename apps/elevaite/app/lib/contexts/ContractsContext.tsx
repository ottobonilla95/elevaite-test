"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { submitContract } from "../actions/contractActions";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractExtractionDictionary, type ContractObject } from "../interfaces";



const exampleExtractedData: ContractExtractionDictionary = {
    "page_0": {
        "Invoice Number": "119329",
        "Invoice Date": "28-06-2023",
        "Due Date": "27-08-2023",
        "Items": [
            {
            "Item": "High-speed internet router",
            "Quantity": "5",
            "Rate": "$500.00",
            "Total Value": "$2,500.00",
            },
            {
            "Item": "Data storage server",
            "Quantity": "5",
            "Rate": "$1,500.00",
            "Total Value": "$7,500.00",
            },
            {
            "Item": "High-performance laptops",
            "Quantity": "5",
            "Rate": "$1,000.00",
            "Total Value": "$5,000.00",
            }
        ],
        "Subtotal": "$15,000.00",
        "Others": "$0.00",
        "VAT": "10%",
        "Total": "$16,500.00"
    }
}


const testContracts: ContractObject[] = [
    {id: "01", name: "Test Invoice 01", status: CONTRACT_STATUS.READY, type: CONTRACT_TYPES.INVOICE, pdf: "/testPdf.pdf", extractedData: exampleExtractedData, fileSize: "24 MB", tags: ["Finance"], createdAt: new Date().toISOString()},
    {id: "02", name: "Test Contract 01", status: CONTRACT_STATUS.READY, type: CONTRACT_TYPES.CONTRACT, pdf: "/testPdf.pdf", extractedData: exampleExtractedData, fileSize: "24 MB", tags: ["Tech"], createdAt: new Date().toISOString()},
    {id: "03", name: "Test Purchase Order 01", status: CONTRACT_STATUS.PROGRESS, type: CONTRACT_TYPES.PURCHASE_ORDER, pdf: undefined, extractedData: undefined, fileSize: "24 MB", tags: [], createdAt: new Date().toISOString()},
    {id: "04", name: "Test Purchase Order 02", status: CONTRACT_STATUS.READY, type: CONTRACT_TYPES.PURCHASE_ORDER, pdf: "/testPdf.pdf", extractedData: exampleExtractedData, fileSize: "24 MB", tags: ["Finance"], createdAt: new Date().toISOString()},
    {id: "05", name: "Test Invoice 02", status: CONTRACT_STATUS.FAILED, type: CONTRACT_TYPES.INVOICE, pdf: undefined, extractedData: undefined, tags: ["Finance", "Tech"], createdAt: new Date().toISOString()},
    {id: "06", name: "Test Contract 02", status: CONTRACT_STATUS.READY, type: CONTRACT_TYPES.CONTRACT, pdf: "/testPdf.pdf", extractedData: exampleExtractedData, fileSize: "24 MB", tags: [], createdAt: new Date().toISOString()},
];



// STATIC OBJECTS

const defaultLoadingList: LoadingListObject = {
    contracts: undefined,
    submittingContract: false,
};



// INTERFACES

interface LoadingListObject {
    contracts: boolean|undefined;
    submittingContract: boolean;
}





// STRUCTURE 

export interface ContractsContextStructure {
    contracts: ContractObject[];
    selectedContract: ContractObject | undefined;
    setSelectedContract: (contract: ContractObject|undefined) => void;
    changeSelectedContractBit: (pageKey: `page_${number}`, itemKey: string, newValue: string) => void;
    changeSelectedContractTableBit: (pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]) => void;
    submitCurrentContractPdf: (pdf: File|undefined, type: CONTRACT_TYPES, name?: string) => void;
    loading: LoadingListObject;
}



export const ContractsContext = createContext<ContractsContextStructure>({
    contracts: [],
    selectedContract: undefined,
    setSelectedContract: () => {/**/},
    changeSelectedContractBit: () => {/**/},
    changeSelectedContractTableBit: () => {/**/},
    submitCurrentContractPdf: () => undefined,
    loading: defaultLoadingList,
});




// FUNCTIONS









// PROVIDER

interface ContractsContextProviderProps {
    children: React.ReactNode;
}


export function ContractsContextProvider(props: ContractsContextProviderProps): JSX.Element {
    const [displayContracts, setDisplayContracts] = useState<ContractObject[]>([]);
    const [selectedContract, setSelectedContract] = useState<ContractObject|undefined>();
    const [currentContractExtractionData, setCurrentContractExtractionData] = useState<{id: string, data: ContractExtractionDictionary}|undefined>();
    const [hasCurrentContractFailed, setHasCurrentContractFailed] = useState("");
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);
    
    const selectedContractChangedByUser = useRef<boolean>();



    useEffect(() => {
        fetchContracts();
    }, []);


    useEffect(() => {
        // console.log("display contracts", displayContracts);
        if (selectedContract) {
            if (selectedContractChangedByUser.current) {
                selectedContractChangedByUser.current = false;
                return;
            }
            const updatedContract = displayContracts.find(item => item.id === selectedContract.id);
            if (updatedContract) setSelectedContract(updatedContract);
        }
    }, [displayContracts]);

    useEffect(() => {
        // console.log("Selected Contract changed:", selectedContract);
        setDisplayContracts(current => 
            current.map(contract => contract.id === selectedContract?.id ? selectedContract : contract )
        )
    }, [selectedContract]);

    useEffect(() => {
        if (!currentContractExtractionData) return;
        addExtractionDataToContractInList(currentContractExtractionData.id, currentContractExtractionData.data);
    }, [currentContractExtractionData]);

    useEffect(() => {
        if (!hasCurrentContractFailed) return;
        changeStatusToContractInList(hasCurrentContractFailed, CONTRACT_STATUS.FAILED);
    }, [hasCurrentContractFailed]);



    function fetchContracts(): void {
        setLoading(current => {return {...current, contracts: true}} );
        setDisplayContracts(testContracts);
        setLoading(current => {return {...current, contracts: false}} );
    }

    function changeSelectedContractBit(pageKey: `page_${number}`, itemKey: string, newValue: string): void {
        selectedContractChangedByUser.current = true;
        setSelectedContract(current => { 
            if (!current) return;
            const oldData = current.extractedData;
            const newData: ContractExtractionDictionary|undefined = oldData === undefined ? undefined : {
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
            const oldData = current.extractedData;
            const newData: ContractExtractionDictionary|undefined = oldData === undefined ? undefined : {
                ...oldData,
                [pageKey]: {
                    ...oldData[pageKey],
                    [tableKey]: newTableData
                }
            };
            return {...current, extractedData: newData};
        });
    }




    function submitCurrentContractPdf(pdf: File|undefined, type: CONTRACT_TYPES, name?: string): void {;
        if (pdf) {
            void actionSubmitContract(pdf, type, name);
        }
    }

    function appendContractToContractsList(pdf: File, type: CONTRACT_TYPES, name?: string): string {
        const id = (displayContracts.length + 1).toString();
        setDisplayContracts(current => {
            return [...current, {
                id,
                status: CONTRACT_STATUS.PROGRESS,
                type,
                name: name ? name : (type === CONTRACT_TYPES.PURCHASE_ORDER ? "New Purchase Order" : type === CONTRACT_TYPES.INVOICE ? "New Invoice" : "New Contract"),
                pdf,
                extractedData: undefined,
                fileSize: `${Math.floor(pdf.size / 1000).toString() } MB`,
                tags: [],
                createdAt: new Date().toISOString(),
            }]}
        );
        return id;
    }

    function addExtractionDataToContractInList(id: string, data: ContractExtractionDictionary): void {
        setDisplayContracts(current =>
            current.map(contract => 
                contract.id === id ? 
                    {...contract, status: CONTRACT_STATUS.READY, extractedData: data }
                : contract
            )
        )
    }

    function changeStatusToContractInList(id: string, status: CONTRACT_STATUS): void {
        setDisplayContracts(current =>
            current.map(contract => 
                contract.id === id ? 
                    {...contract, status }
                : contract
            )
        )
    }




    async function actionSubmitContract(submittedPdf: File, type: CONTRACT_TYPES, name?: string): Promise<void> {
        setHasCurrentContractFailed("");
        const id = appendContractToContractsList(submittedPdf, type, name);
        try {
            setLoading(current => { return {...current, submittingContract: true}} );
            const formData = new FormData();
            formData.append("file", submittedPdf);
            const contractExtractionResults = await submitContract(formData, type);
            setCurrentContractExtractionData({id, data: contractExtractionResults});
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in submitting contract:", error);
            setHasCurrentContractFailed(id);
        } finally {
            setLoading(current => { return {...current, submittingContract: false}} );
        }
    }


  
    return (
        <ContractsContext.Provider
            value={ {
                contracts: displayContracts,
                selectedContract,
                setSelectedContract,
                changeSelectedContractBit,
                changeSelectedContractTableBit,
                submitCurrentContractPdf,
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