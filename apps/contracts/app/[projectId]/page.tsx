import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import "./page.scss";
import {
  getContractProjectById,
  getContractProjectContracts,
  getContractProjectsList,
} from "@repo/contracts-ui/actions";

export default async function ProjectPage({
  params,
}: Readonly<{ params: Promise<{ projectId: string }> }>) {
  const { projectId } = await params;

  const projectsPromise = getContractProjectsList();
  const projectPromise = getContractProjectById(projectId);
  const contractsPromise = getContractProjectContracts(projectId);

  const [projects, project, contracts] = await Promise.all([
    projectsPromise,
    projectPromise,
    contractsPromise,
  ]);

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
