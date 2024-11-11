import { ProjectsAndContracts } from "@repo/contracts-ui/components";
import "./page.scss";

export default function Page(): JSX.Element {
  return (
    <div className="contracts-main-container">
      <ProjectsAndContracts />
    </div>
  );
}
