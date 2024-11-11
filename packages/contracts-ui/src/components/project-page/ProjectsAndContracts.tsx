"use client";
import { useEffect, useState } from "react";
import {
  type CONTRACT_TYPES,
  type ContractObject,
  type ContractProjectObject,
  type LoadingListObject,
} from "../../interfaces";
import { ProjectsList } from "./ProjectsList";
import { ContractsListV2 } from "./ContractsListV2";
import "./ProjectsAndContracts.scss";
import {
  getContractProjectById,
  getContractProjectsList,
} from "@/actions/contractActions";

export function ProjectsAndContracts(): JSX.Element {
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  const [secondarySelectedContract, setSecondarySelectedContract] = useState<
    ContractObject | CONTRACT_TYPES | undefined
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
    const fetchProjects = async () => {
      const result = await getContractProjectsList(false);
      setProjects(result);
    };

    void fetchProjects();
  }, []);

  const getContractById = async (
    id: string | number
  ): Promise<ContractObject | undefined> => {
    const response = await fetch(`${CONTRACTS_URL}/1/files/${id}/file`);
    return response.ok ? await response.json() : undefined;
  };

  const submitCurrentContractPdf = async (
    pdf: File | undefined,
    type: CONTRACT_TYPES,
    projectId: string | number,
    name?: string
  ): Promise<void> => {
    const formData = new FormData();
    formData.append("pdf", pdf ?? "");
    formData.append("content_type", type);
    if (name) formData.append("name", name);

    await fetch(`${CONTRACTS_URL}/${projectId}/files/`, {
      method: "POST",
      body: formData,
    });
  };

  const createProject = async (
    name: string,
    description?: string
  ): Promise<boolean> => {
    const response = await fetch(`${CONTRACTS_URL}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (response.ok) {
      const newProject = await response.json();
      setProjects((prevProjects) => [...prevProjects, newProject]);
    }
    return response.ok;
  };

  const editProject = async (
    projectId: string,
    name: string,
    description?: string
  ): Promise<boolean> => {
    const response = await fetch(`${CONTRACTS_URL}/${projectId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    return response.ok;
  };

  const deleteProject = async (projectId: string): Promise<boolean> => {
    const response = await fetch(`${CONTRACTS_URL}/projects/${projectId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      setProjects((prevProjects) =>
        prevProjects.filter((project) => project.id !== projectId)
      );
    }
    return response.ok;
  };

  const deleteContract = async (
    projectId: string,
    contractId: string
  ): Promise<boolean> => {
    const response = await fetch(
      `${CONTRACTS_URL}/${projectId}/files/${contractId}`,
      { method: "DELETE" }
    );
    return response.ok;
  };

  function setSelectedProjectById(id?: string | number): void {
    if (projects.length === 0) return;
    window.location.href = `/${id}`;
  }

  function setSelectedContractById(
    secondaryId: string | number | undefined
  ): void {
    if (projects.length === 0) return;
    const primaryId =
      window.location.pathname.split("/")[1] || "primaryContract";
    const secondary = secondaryId
      ? secondaryId.toString()
      : "secondaryContract";
    window.location.href = `/${primaryId}/${secondary}`;
  }
  return (
    <div
      className={["contracts-content", selectedContract ? "active" : undefined]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="projects-and-contracts-container">
        <ProjectsList
          createProject={createProject}
          deleteProject={deleteProject}
          editProject={editProject}
          loading={loading}
          projects={projects}
          setSelectedProjectById={setSelectedProjectById}
        />
        <ContractsListV2
          createProject={createProject}
          deleteProject={deleteProject}
          editProject={editProject}
          loading={loading}
          projects={projects}
          deleteContract={deleteContract}
          submitCurrentContractPdf={() => submitCurrentContractPdf}
          setSelectedContract={setSelectedContract}
          setSecondarySelectedContractById={setSelectedContractById}
          setSecondarySelectedContract={setSecondarySelectedContract}
          getContractById={getContractById}
        />
      </div>
    </div>
  );
}
