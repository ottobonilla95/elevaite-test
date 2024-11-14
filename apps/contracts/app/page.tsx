import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import { getContractProjectsList } from "@repo/contracts-ui/actions";
import "./page.scss";

export default async function Page(): Promise<JSX.Element> {
  const projects = await getContractProjectsList(false);
  return (
    <div className="contracts-main-container">
      <ProjectsAndContracts projects={projects} contracts={[]} />
    </div>
  );
}
