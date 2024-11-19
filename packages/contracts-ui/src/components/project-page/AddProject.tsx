import {
  CommonButton,
  CommonDialog,
  CommonInput,
  ElevaiteIcons,
} from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractProjectObject } from "@/interfaces";
import "./AddProject.scss";
import {
  CreateProject,
  DeleteProject,
  EditProject,
} from "@/actions/contractActions";

interface AddProjectProps {
  onClose: () => void;
  editingProjectId?: string;
  projects: ContractProjectObject[];
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
  const [deleteConfirmationField, setDeleteConfirmationField] = useState("");

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
  }, [props.editingProjectId, props.projects]);

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
    await DeleteProject(editingProject.id.toString());
    setIsLoading(false);
    props.onClose();
  }

  async function handleSubmit(): Promise<void> {
    if (!name) return;
    setIsLoading(true);
    if (editingProject) {
      await EditProject(editingProject.id.toString(), name, description);
    } else {
      await CreateProject(name, description);
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
            onClick={() => {
              void handleSubmit();
            }}
            disabled={!name}
          >
            {props.editingProjectId ? "Submit Changes" : "Submit"}
          </CommonButton>
        </div>
      </div>

      {!isDeletionConfirmationOpen || !editingProject ? undefined : (
        <CommonDialog
          title="Delete Project?"
          confirmLabel="Delete"
          disableConfirm={
            deleteConfirmationField.trim().toLowerCase() !== "delete"
          }
          onConfirm={() => {
            void handleConfirmedDelete();
          }}
          onCancel={() => {
            setIsDeletionConfirmationOpen(false);
          }}
          dangerSubmit
        >
          <div className="delete-dialog-contents">
            <span>{`Are you sure you want to delete the project named "${editingProject.name}"?`}</span>
            <span>
              This action will delete the project and all its files and cannot
              be reverted.
            </span>
            <div className="super-confirm">
              <CommonInput
                label='Please type the word "Delete" in the field below.'
                onChange={setDeleteConfirmationField}
                placeholder="Write 'Delete' to confirm."
              />
            </div>
          </div>
        </CommonDialog>
      )}
    </div>
  );
}
