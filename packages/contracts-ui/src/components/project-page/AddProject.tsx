import {
  CommonButton,
  CommonDialog,
  CommonInput,
  ElevaiteIcons,
} from "@repo/ui/components";
import { useEffect, useState } from "react";
import "./AddProject.scss";
import { type ContractProjectObject } from "@/interfaces";

interface AddProjectProps {
  onClose: () => void;
  editingProjectId?: string;
  projects: ContractProjectObject[];
  deleteProject: (projectId: string) => Promise<boolean>;
  createProject: (name: string, description?: string) => Promise<boolean>;
  editProject: (
    projectId: string,
    name: string,
    description?: string
  ) => Promise<boolean>;
}

export function AddProject(props: AddProjectProps): JSX.Element {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [editingProject, setEditingProject] = useState<
    ContractProjectObject | undefined
  >();

  const [isDeletionConfirmationOpen, setIsDeletionConfirmationOpen] =
    useState(false);

  useEffect(() => {
    if (!props.editingProjectId) {
      setEditingProject(undefined);
      return;
    }
    setEditingProject(
      props.projects.find(
        (project) => project.id.toString() === props.editingProjectId
      )
    );
  }, [props.editingProjectId]);

  useEffect(() => {
    setName(editingProject?.name ?? "");
    setDescription(editingProject?.description ?? "");
  }, [editingProject]);

  function handleCloseModal(): void {
    props.onClose();
  }

  function handleDelete(): void {
    setIsDeletionConfirmationOpen(true);
  }

  async function handleConfirmedDelete(): Promise<void> {
    setIsDeletionConfirmationOpen(false);
    if (!editingProject?.id) return;

    setIsLoading(true);
    await props.deleteProject(editingProject.id.toString());
    setIsLoading(false);
    props.onClose();
  }

  async function handleSubmit(): Promise<void> {
    if (!name) return;
    setIsLoading(true);
    if (editingProject) {
      await props.editProject(editingProject.id.toString(), name, description);
    } else {
      await props.createProject(name, description);
    }
    setIsLoading(false);
    props.onClose();
  }

  return (
    <div className="add-project-container">
      {!isLoading ? undefined : (
        <div className="loading-overlay">
          <ElevaiteIcons.SVGSpinner />
        </div>
      )}

      <div className="add-project-header">
        <div className="add-project-title">
          <span>{props.editingProjectId ? "Edit Project" : "Add Project"}</span>
        </div>
        <div className="close-button">
          <CommonButton onClick={handleCloseModal} noBackground>
            <ElevaiteIcons.SVGXmark />
          </CommonButton>
        </div>
      </div>

      <CommonInput
        label="Name"
        controlledValue={name}
        onChange={setName}
        required
      />

      <CommonInput
        label="Description"
        controlledValue={description}
        onChange={setDescription}
      />

      <div
        className={[
          "submit-controls",
          !props.editingProjectId ? undefined : "editing",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {!props.editingProjectId ? undefined : (
          <CommonButton className="delete-button" onClick={handleDelete}>
            Delete Project
          </CommonButton>
        )}

        <div className="pair">
          <CommonButton className="cancel-button" onClick={handleCloseModal}>
            Cancel
          </CommonButton>
          <CommonButton
            className="submit-button"
            onClick={() => void handleSubmit()}
            disabled={!name}
          >
            {props.editingProjectId ? "Submit Changes" : "Submit"}
          </CommonButton>
        </div>
      </div>

      {!isDeletionConfirmationOpen ? undefined : (
        <CommonDialog
          title="Delete Project?"
          confirmLabel="Delete"
          onConfirm={() => void handleConfirmedDelete()}
          onCancel={() => {
            setIsDeletionConfirmationOpen(false);
          }}
          dangerSubmit
        >
          <div className="delete-dialog-contents">
            <span>{`Are you sure you want to delete the project named "${editingProject?.name}"?`}</span>
            <span>
              This action will delete the project and all its files and cannot
              be reverted.
            </span>
          </div>
        </CommonDialog>
      )}
    </div>
  );
}
