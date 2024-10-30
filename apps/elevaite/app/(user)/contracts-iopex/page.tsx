import { ContractsContextProvider } from "../../lib/contexts/ContractsContext";
import { ContractVariations } from "../../lib/interfaces";
import { PdfAndExtraction } from "../contracts/components/PdfAndExtraction";
import { ProjectsAndContracts } from "../contracts/components/ProjectsAndContracts";
import "./page.scss";



export default function Page(): JSX.Element {


    return (
        <ContractsContextProvider
            variation={ContractVariations.Iopex}
        >
            <div className="contracts-main-container">

                <ProjectsAndContracts />

                <PdfAndExtraction />
                
            </div>
        </ContractsContextProvider>
    );
}