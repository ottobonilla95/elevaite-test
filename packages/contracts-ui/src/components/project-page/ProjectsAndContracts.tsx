"use client";
import { ProjectsList } from "./ProjectsList";
import { ContractsListV2 } from "./ContractsListV2";
import {
  type CONTRACT_TYPES,
  type ContractObject,
  type ContractProjectObject,
  type LoadingListObject,
} from "@/interfaces";
import "./ProjectsAndContracts.scss";

interface ProjectsAndContractsProps {
  projects: ContractProjectObject[];
  selectedProject?: ContractProjectObject;
  selectedContract?: ContractObject;
  setSelectedContract: (contract?: ContractObject) => void;
  setSecondarySelectedContract: (
    contract?: ContractObject | CONTRACT_TYPES
  ) => void;
  setSecondarySelectedContractById: (id?: string | number) => void;
  getContractById: (id: string | number) => ContractObject | undefined;
  submitCurrentContractPdf: (
    pdf: File | undefined,
    type: CONTRACT_TYPES,
    projectId: string | number,
    name?: string
  ) => void;
  deleteContract: (projectId: string, contractId: string) => Promise<boolean>;
  createProject: (name: string, description?: string) => Promise<boolean>;
  editProject: (
    projectId: string,
    name: string,
    description?: string
  ) => Promise<boolean>;
  deleteProject: (projectId: string) => Promise<boolean>;
  loading: LoadingListObject;
}

export function ProjectsAndContracts(
  props: ProjectsAndContractsProps
): JSX.Element {
  return (
    <div
      className={[
        "contracts-content",
        !props.selectedContract ? "active" : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="projects-and-contracts-container">
        <ProjectsList />
        <ContractsListV2
          createProject={props.createProject}
          deleteContract={props.deleteContract}
          deleteProject={props.deleteProject}
          editProject={props.editProject}
          getContractById={props.getContractById}
          loading={props.loading}
          projects={props.projects}
          setSecondarySelectedContract={props.setSecondarySelectedContract}
          setSecondarySelectedContractById={
            props.setSecondarySelectedContractById
          }
          setSelectedContract={props.setSelectedContract}
          submitCurrentContractPdf={props.submitCurrentContractPdf}
          selectedContract={props.selectedContract}
          selectedProject={props.selectedProject}
        />
      </div>
    </div>
  );
}
