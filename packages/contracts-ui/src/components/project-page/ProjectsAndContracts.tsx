"use client";
import { useState } from "react";
import { ContractsListV2 } from "./ContractsListV2";
import { ProjectsList } from "./ProjectsList";
import {
  type ContractProjectObject,
  type ContractObject,
  type LoadingListObject,
} from "@/interfaces";
import "./ProjectsAndContracts.scss";

interface ProjectsAndContractsProps {
  projectId?: string;
  project?: ContractProjectObject;
  projects: ContractProjectObject[];
}

export function ProjectsAndContracts({
  projects,
  project,
  ...props
}: ProjectsAndContractsProps): JSX.Element {
  const [selectedContract, setSelectedContract] = useState<
    ContractObject | undefined
  >();
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
      className={["contracts-content", !selectedContract ? "active" : undefined]
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
          selectedContract={selectedContract}
          setSelectedContract={setSelectedContract}
          projects={projects}
        />
      </div>
    </div>
  );
}
