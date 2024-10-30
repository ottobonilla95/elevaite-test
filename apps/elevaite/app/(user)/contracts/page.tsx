import { ContractsContextProvider } from "../../lib/contexts/ContractsContext";
import { ContractVariations } from "../../lib/interfaces";
import { PdfAndExtraction } from "./components/PdfAndExtraction";
import { ProjectsAndContracts } from "./components/ProjectsAndContracts";
import "./page.scss";



export default function Page(): JSX.Element {


    return (
        <ContractsContextProvider
            variation={ContractVariations.Default}
        >
            <div className="contracts-main-container">

                <ProjectsAndContracts />

                <PdfAndExtraction />
                
            </div>
        </ContractsContextProvider>
    );
}