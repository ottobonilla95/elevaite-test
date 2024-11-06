import { ContractsContextProvider } from "../lib/contexts/ContractsContext";
import { ContractVariations } from "../lib/interfaces";
import { ProjectsAndContracts } from "../components/ProjectsAndContracts";
import "./page.scss";

export default function Page(): JSX.Element {
  return (
    <ContractsContextProvider variation={ContractVariations.Default}>
      <div className="contracts-main-container">
        <ProjectsAndContracts />
      </div>
    </ContractsContextProvider>
  );
}
