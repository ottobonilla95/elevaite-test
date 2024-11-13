"use client";
import { useEffect, useState } from "react";
import { ContractsListV2 } from "./ContractsListV2";
import { ProjectsList } from "./ProjectsList";
import {
  type ContractProjectObject,
  type ContractObject,
  type LoadingListObject,
} from "@/interfaces";
import "./ProjectsAndContracts.scss";
import { getContractProjectsList } from "@/actions/contractActions";

interface ProjectsAndContractsProps {
  projectId?: string;
}

export function ProjectsAndContracts(
  props: ProjectsAndContractsProps
): JSX.Element {
  const [selectedContract, setSelectedContract] = useState<
    ContractObject | undefined
  >();
  const [projects, setProjects] = useState<ContractProjectObject[]>([]);
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
  useEffect(() => {
    getContractProjectsList(false).then((projectList) => {
      setProjects(projectList);
      setLoading((current) => {
        return { ...current, projects: false };
      });
    });
  }, []);

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
          selectedContract={selectedContract}
          setSelectedContract={setSelectedContract}
          projects={projects}
        />
      </div>
    </div>
  );
}
