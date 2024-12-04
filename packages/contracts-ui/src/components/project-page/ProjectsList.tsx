"use client";
import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { type ContractProjectObject, } from "../../interfaces";
import { AddProject } from "./AddProject";
import "./ProjectsList.scss";


interface ProjectsListProps {
  projects: ContractProjectObject[];
  projectId?: string;
}

export function ProjectsList({ projects, projectId, }: ProjectsListProps ): JSX.Element {
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
          {projects.length === 0 ? (
            <div className="no-projects">No Projects found</div>
          ) : (
            projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                selectedProjectId={projectId}
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
            projects={projects}
            editingProjectId={projectId}
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
  selectedProjectId?: string;
}

function ProjectCard(props: ProjectCardProps): JSX.Element {
  const router = useRouter();

  function handleMouseOver(): void {
    router.prefetch(`/${props.project.id}`);
  }
  function handleClick(): void {
    if (props.selectedProjectId !== props.project.id.toString()) {
      // eslint-disable-next-line no-console -- .
      console.dir(props);
      router.push(`/${props.project.id}`);
    }
  }

  function onKeyDown(): void {
    // No need for this
  }

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions -- Fix that later
    <div
      className={[
        "project-card-container",
        props.selectedProjectId === props.project.id.toString()
          ? "selected"
          : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={handleClick}
      onMouseOver={handleMouseOver}
      onFocus={handleMouseOver}
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
