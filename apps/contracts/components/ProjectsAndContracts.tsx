import {
  getContractProjectContracts,
  getContractProjectsList,
} from "../lib/actions/contractActions";
import { ContractsList } from "./ContractsList";
import "./ProjectsAndContracts.scss";
import { ProjectsList } from "./ProjectsList";

export async function ProjectsAndContracts({
  projectId,
}: {
  projectId?: string;
}) {
  const projectsListPromise = getContractProjectsList(false);
  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId, false)
    : Promise.resolve([]);

  const [projectsList, contractsList] = await Promise.all([
    projectsListPromise,
    contractsListPromise,
  ]);
  return (
    <div className="contracts-content active">
      <div className="projects-and-contracts-container">
        <ProjectsList projectsList={projectsList} projectId={projectId} />
        <ContractsList
          contractsList={contractsList}
          selectedProjectId={projectId}
        />
      </div>
    </div>
  );
}
