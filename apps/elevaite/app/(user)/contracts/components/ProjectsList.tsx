import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import "./ProjectsList.scss";




export function ProjectsList(): JSX.Element {

    function handleAddProject() {
        console.log("Adding Project");
    }


    return (
        <div className="projects-list-container">
            <div className="projects-list-header">
                <span>Project List</span>
                <div className="projects-list-controls">
                    <CommonButton
                        onClick={handleAddProject}
                    >
                        <ElevaiteIcons.SVGCross/>
                        <span>Add Project</span>
                    </CommonButton>
                </div>
            </div>

            <div className="projects-list-scroller">

                <div className="projects-list-contents">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(number => 
                        <ProjectCard key={number}/>
                    )}
                </div>

            </div>
        </div>
    );
}





interface ProjectCardProps {

}

function ProjectCard(props: ProjectCardProps): JSX.Element {
    return (
        <div className="project-card-container">
            <div className="line">
                <span>Project Name</span>
                <span>{dayjs().format("YYYY-MM-DD")}</span>
            </div>
            <div className="line">
                <span>Longer Description</span>
            </div>
        </div>
    )
}



