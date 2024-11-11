import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useState } from "react";
import { AddProject } from "./AddProject";
import {
  type LoadingListObject,
  type ContractProjectObject,
} from "@/interfaces";
import "./ProjectsList.scss";

interface ProjectsListProps {
  projects: ContractProjectObject[];
  loading: LoadingListObject;
  selectedProject?: ContractProjectObject;
  setSelectedProjectById: (id?: string | number) => void;
  createProject: (name: string, description?: string) => Promise<boolean>;
  editProject: (
    projectId: string,
    name: string,
    description?: string
  ) => Promise<boolean>;
  deleteProject: (projectId: string) => Promise<boolean>;
}

export function ProjectsList(props: ProjectsListProps): JSX.Element {
  const [isProjectCreationOpen, setIsProjectCreationOpen] = useState(false);

  function handleAddProject(): void {
    setIsProjectCreationOpen(true);
  }

  return (
    <div className="projects-list-container">
      <div className="projects-list-header">
        <span>Projects</span>
        <div className="projects-list-controls">
          <CommonButton onClick={handleAddProject} title="Add Project">
            <ElevaiteIcons.SVGCross />
            {/* <span>Add Project</span> */}
          </CommonButton>
        </div>
      </div>

      <div className="projects-list-scroller">
        <div className="projects-list-contents">
          {props.loading?.projects ? (
            <div className="loading-projects">
              <ElevaiteIcons.SVGSpinner />
            </div>
          ) : props.projects.length === 0 ? (
            <div className="no-projects">No Projects found</div>
          ) : (
            props.projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                setSelectedProjectById={props.setSelectedProjectById}
                selectedProject={props.selectedProject}
              />
            ))
          )}
        </div>
      </div>

      {!isProjectCreationOpen ? undefined : (
        <CommonModal
          onClose={() => {
            setIsProjectCreationOpen(false);
          }}
        >
          <AddProject
            createProject={props.createProject}
            deleteProject={props.deleteProject}
            editProject={props.editProject}
            projects={props.projects}
            onClose={() => {
              setIsProjectCreationOpen(false);
            }}
          />
        </CommonModal>
      )}
    </div>
  );
}

interface ProjectCardProps {
  project: ContractProjectObject;
  selectedProject?: ContractProjectObject;
  setSelectedProjectById: (id?: string | number) => void;
}

function ProjectCard(props: ProjectCardProps): JSX.Element {
  function handleClick(): void {
    if (props.selectedProject?.id === props.project.id)
      props.setSelectedProjectById(undefined);
    else props.setSelectedProjectById(props.project.id);
  }

  function onKeyDown(): void {
    // No need for this
  }

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions -- Fix that later
    <div
      className={[
        "project-card-container",
        props.selectedProject?.id === props.project.id ? "selected" : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={handleClick}
      onKeyDown={onKeyDown}
    >
      <div className="line">
        <span
          title={
            props.project.create_date
              ? `Created on:\n${dayjs(props.project.create_date).format("YYYY-MM-DD")}\n${dayjs(props.project.create_date).format("hh:mm a")}`
              : ""
          }
        >
          {props.project.name}
        </span>
        <span className="selection-arrow">
          <ElevaiteIcons.SVGSelectionArrow />
        </span>
      </div>
      {!props.project.description ? undefined : (
        <div className="line">
          <span>{props.project.description}</span>
        </div>
      )}
    </div>
  );
}
