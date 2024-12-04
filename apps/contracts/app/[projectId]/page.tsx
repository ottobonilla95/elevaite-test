import { getContractProjectById, getContractProjectContracts, getContractProjectsList, } from "@repo/contracts-ui/actions";
import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import "./page.scss";


interface ProjectPageProps {
  readonly params: Promise<{ projectId: string }>;
}

export default async function ProjectPage({params}: ProjectPageProps): Promise<JSX.Element> {
  const { projectId } = await params;

  const projectsPromise = getContractProjectsList();
  const projectPromise = getContractProjectById(projectId);
  const contractsPromise = getContractProjectContracts(projectId);

  const [projects, project, contracts] = await Promise.all([projectsPromise, projectPromise, contractsPromise, ]);

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
