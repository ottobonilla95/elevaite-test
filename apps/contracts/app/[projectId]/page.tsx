import { getContractProjectById, getContractProjectContracts, getContractProjectsList, } from "@repo/contracts-ui/actions";
import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import { type ContractObject, type ContractProjectObject } from "@repo/contracts-ui/interfaces";
import { redirect } from "next/navigation";
import "./page.scss";


interface ProjectPageProps {
  readonly params: Promise<{ projectId: string }>;
}

export default async function ProjectPage({params}: ProjectPageProps): Promise<JSX.Element> {
  const { projectId } = await params;
  let projects: ContractProjectObject[]|undefined;
  let project: ContractProjectObject|undefined;
  let contracts: ContractObject[]|undefined;

  const projectsPromise = getContractProjectsList();
  const projectPromise = getContractProjectById(projectId);
  const contractsPromise = getContractProjectContracts(projectId);

  try {
    [projects, project, contracts] = await Promise.all([projectsPromise, projectPromise, contractsPromise]);
  } catch(error) { redirect("/") }
  

  return (
    <div className="contracts-main-container">
      <ProjectsAndContracts
        projectId={projectId}
        contracts={contracts}
        projects={projects}
        project={project}
      />
    </div>
  );
}
