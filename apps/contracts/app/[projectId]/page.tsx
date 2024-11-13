import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import "./page.scss";

export default async function ProjectPage({
  params,
}: Readonly<{ params: Promise<{ projectId: string }> }>) {
  const { projectId } = await params;

  return (
    <div className="contracts-main-container">
      <ProjectsAndContracts projectId={projectId} />
    </div>
  );
}
