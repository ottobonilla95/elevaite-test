import { CommonFormLabels, CommonInput, CommonSelect, type CommonSelectOption, SimpleTextarea } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { type ProjectObject } from "../../../../lib/interfaces";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditProject.scss";



interface AddEditProjectProps {
    project: ProjectObject | undefined;
    onClose: () => void;
}

export function AddEditProject(props: AddEditProjectProps): JSX.Element {
    const rolesContext = useRoles();
    const [projectName, setProjectName] = useState("");
    const [projectDescription, setProjectDescription] = useState(props.project?.description ?? "");
    const [accountOptions, setAccountOptions] = useState<CommonSelectOption[]>([]);
    const [parentProjectOptions, setParentProjectOptions] = useState<CommonSelectOption[]>([{value: "", label: "None"}]);
    const [selectedAccountId, setSelectedAccountId] = useState(props.project?.account_id ?? undefined);
    const [selectedParentProjectId, setSelectedParentProjectId] = useState(props.project?.parent_project_id ?? "");


    useEffect(() => {
        if (!rolesContext.accounts) return;
        setAccountOptions(
            rolesContext.accounts.map(item => { return {
                value: item.id, label: item.name
            }})
        );
    }, [rolesContext.accounts]);

    useEffect(() => {
        if (!selectedAccountId) setParentProjectOptions([]);
        else {
            const projectOptions = [{value: "", label: "None"}];
            setParentProjectOptions(
                [...projectOptions, ...rolesContext.projects.filter(item => item.account_id === selectedAccountId).map(item => { return {
                    value: item.id, label: item.name
                }})]
            );
        }
    }, [selectedAccountId]);

    useEffect(() => {    
        setSelectedParentProjectId(selectedAccountId === props.project?.account_id && props.project?.parent_project_id ? props.project.parent_project_id : "");
    }, [parentProjectOptions]);



    function handleAccountChange(accountId: string): void {
        setSelectedAccountId(accountId);
    }

    function handleParentProjectChange(parentId: string): void {
        setSelectedParentProjectId(parentId);
    }


    async function handleClick(): Promise<void> {
        if (!projectName || !selectedAccountId) return;
        let result: boolean;        
        if (props.project) result = await rolesContext.editProject(props.project.id, projectName, projectDescription);
        else result = await rolesContext.addProject(selectedAccountId, projectName, projectDescription, selectedParentProjectId);
        if (result) props.onClose();
    }


    return (
        <div className="add-edit-project-container">
            
            <AddEditBaseDialog
                header={props.project ? "Edit Project" : "Add Project"}
                onClose={props.onClose}
                onClick={handleClick}
                buttonLabel={props.project ? "Apply" : "Add"}
                disabled={!projectName || (props.project && props.project.name === projectName && props.project.description === projectDescription)}
                loading={rolesContext.loading.addEditProject}
            >
                <CommonInput
                    label="Project Name"
                    field={projectName}
                    onChange={setProjectName}
                    initialValue={props.project?.name}
                    required
                />

                <CommonFormLabels
                    label="Account"
                    required
                    info={props.project ? "Parent Project cannot be edited" : undefined}
                >
                    <CommonSelect
                        options={accountOptions}
                        controlledValue={selectedAccountId}
                        onSelectedValueChange={handleAccountChange}
                        isLoading={rolesContext.loading.accounts}
                        disabled={Boolean(props.project)}
                        useCommonStyling
                    />
                </CommonFormLabels>

                <CommonFormLabels
                    label="Parent Project"
                    info={props.project ? "Parent Project cannot be edited" : "Select an account to see available parent projects"}
                >
                    <CommonSelect
                        options={parentProjectOptions}
                        controlledValue={selectedParentProjectId}
                        onSelectedValueChange={handleParentProjectChange}
                        isLoading={rolesContext.loading.projects}
                        disabled={!selectedAccountId || Boolean(props.project)}
                        useCommonStyling
                    />
                </CommonFormLabels>

                <CommonFormLabels
                    label="Project Description"
                >
                    <SimpleTextarea
                        value={projectDescription}
                        onChange={setProjectDescription}
                        useCommonStyling
                        rows={8}
                    />
                </CommonFormLabels>

            </AddEditBaseDialog>
        </div>
    );
}