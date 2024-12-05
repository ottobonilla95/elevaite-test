"use client";
import { type ContractObject, type ContractProjectObject, } from "../../interfaces";
import { ContractsListV2 } from "./ContractsListV2";
import "./ProjectsAndContracts.scss";
import { ProjectsList } from "./ProjectsList";

interface ProjectsAndContractsProps {
  projectId?: string;
  project?: ContractProjectObject;
  projects?: ContractProjectObject[];
  contracts?: ContractObject[];
}

export function ProjectsAndContracts({ projects, project, contracts, ...props }: ProjectsAndContractsProps): JSX.Element {

  return (
    <div
      className={["contracts-content active"]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="projects-and-contracts-container">
        <ProjectsList
          projectId={props.projectId}
          projects={projects}
        />
        <ContractsListV2
          projectId={props.projectId}
          project={project}
          contracts={contracts}
          projects={projects}
        />
      </div>
    </div>
  );
}
