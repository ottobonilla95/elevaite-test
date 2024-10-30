import { CommonButton, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useState } from "react";
import { useContracts } from "../lib/contexts/ContractsContext";
import "./AddProject.scss";



interface AddProjectProps {
    onClose: () => void;
}

export function AddProject(props: AddProjectProps): JSX.Element {
    const contractsContext = useContracts();
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [isLoading, setIsLoading] = useState(false);


    function handleCloseModal(): void {
        props.onClose();
    }

    async function handleSubmit(): Promise<void> {
        if (!name) return;
        setIsLoading(true);
        await contractsContext.createProject(name, description);
        setIsLoading(false);
        props.onClose();
    }


    return (
        <div className="add-project-container">

            {!isLoading ? undefined :
                <div className="loading-overlay">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            }

            <div className="add-project-header">
                <div className="add-project-title">
                    <span>Add Project</span>
                </div>
                <div className="close-button">                    
                    <CommonButton onClick={handleCloseModal} noBackground>
                        <ElevaiteIcons.SVGXmark/>
                    </CommonButton>
                </div>
            </div>

            <CommonInput
                label="Name"
                onChange={setName}
                required
            />

            <CommonInput
                label="Description"
                onChange={setDescription}
            />
            
            <div className="submit-controls">

                <CommonButton
                    className="submit-button"
                    onClick={handleSubmit}
                    disabled={!name}
                >
                    Submit
                </CommonButton>

            </div>

        </div>
    );
}