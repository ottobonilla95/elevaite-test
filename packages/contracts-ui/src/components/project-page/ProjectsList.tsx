import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { type ContractProjectObject } from "@/interfaces";
import "./ProjectsList.scss";
import { AddProject } from "./AddProject";




export function ProjectsList(): JSX.Element {
    const contractsContext = useContracts();
    const [isProjectCreationOpen, setIsProjectCreationOpen] = useState(false);

    function handleAddProject(): void {
        setIsProjectCreationOpen(true);
    }


    return (
        <div className="projects-list-container">
            <div className="projects-list-header">
                <span>Projects</span>
                <div className="projects-list-controls">
                    <CommonButton
                        onClick={handleAddProject}
                        title="Add Project"
                    >
                        <ElevaiteIcons.SVGCross />
                        {/* <span>Add Project</span> */}
                    </CommonButton>
                </div>
            </div>

            <div className="projects-list-scroller">

                <div className="projects-list-contents">
                    {
                        contractsContext.loading.projects ?
                            <div className="loading-projects">
                                <ElevaiteIcons.SVGSpinner />
                            </div>
                            :
                            contractsContext.projects.length === 0 ?
                                <div className="no-projects">No Projects found</div>
                                :
                                contractsContext.projects.map(project =>
                                    <ProjectCard
                                        key={project.id}
                                        project={project}
                                    />
                                )}
                </div>

            </div>


            {!isProjectCreationOpen ? undefined :
                <CommonModal
                    onClose={() => { setIsProjectCreationOpen(false); }}
                >
                    <AddProject
                        onClose={() => { setIsProjectCreationOpen(false); }}
                    />
                </CommonModal>
            }

        </div>
    );
}





interface ProjectCardProps {
    project: ContractProjectObject;
}

function ProjectCard(props: ProjectCardProps): JSX.Element {
    const contractsContext = useContracts();

    function handleClick(): void {
        if (contractsContext.selectedProject?.id === props.project.id) contractsContext.setSelectedProjectById(undefined);
        else contractsContext.setSelectedProjectById(props.project.id);
    }

    function onKeyDown(): void {
        // No need for this
    }

    return (
        // eslint-disable-next-line jsx-a11y/no-static-element-interactions -- Fix that later
        <div
            className={["project-card-container", contractsContext.selectedProject?.id === props.project.id ? "selected" : undefined].filter(Boolean).join(" ")}
            onClick={handleClick}
            onKeyDown={onKeyDown}
        >
            <div className="line">
                <span title={props.project.create_date ? `Created on:\n${dayjs(props.project.create_date).format("YYYY-MM-DD")}\n${dayjs(props.project.create_date).format("hh:mm a")}` : ""}>
                    {props.project.name}
                </span>
                <span className="selection-arrow">
                    <ElevaiteIcons.SVGSelectionArrow />
                </span>
            </div>
            {!props.project.description ? undefined :
                <div className="line">
                    <span>{props.project.description}</span>
                </div>
            }
        </div>
    )
}



