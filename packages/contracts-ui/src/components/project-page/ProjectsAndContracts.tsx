"use client";
import { useState } from "react";
import { ContractsListV2 } from "./ContractsListV2";
import { ProjectsList } from "./ProjectsList";
import {
  type ContractProjectObject,
  type ContractObject,
  type LoadingListObject,
} from "../../interfaces";
import "./ProjectsAndContracts.scss";

interface ProjectsAndContractsProps {
  projectId?: string;
  project?: ContractProjectObject;
  projects: ContractProjectObject[];
  contracts: ContractObject[];
}

export function ProjectsAndContracts({
  projects,
  project,
  contracts,
  ...props
}: ProjectsAndContractsProps): JSX.Element {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- testing
  const [loading, setLoading] = useState<LoadingListObject>({
    projects: undefined,
    contracts: undefined,
    submittingContract: false,
    projectReports: {},
    projectSettings: {},
    contractEmphasis: {},
    contractLineItems: {},
    contractVerification: {},
    deletingContract: false,
  });

  return (
    <div
      className={["contracts-content active"]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="projects-and-contracts-container">
        <ProjectsList
          loading={loading}
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
