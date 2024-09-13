import { ContractsContextProvider } from "../../lib/contexts/ContractsContext";
import { PdfAndExtraction } from "./components/PdfAndExtraction";
import { ProjectsAndContracts } from "./components/ProjectsAndContracts";
import "./page.scss";



export default function Page(): JSX.Element {


    return (
        <ContractsContextProvider>
            <div className="contracts-main-container">

                <ProjectsAndContracts />

                <PdfAndExtraction />
                
            </div>
        </ContractsContextProvider>
    );
}