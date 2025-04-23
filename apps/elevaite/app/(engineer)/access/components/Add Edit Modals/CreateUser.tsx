import { CommonInput } from "@repo/ui/components";
import { useState } from "react";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUser.scss";

interface CreateUserProps {
  onClose: () => void;
  onSuccess: (email: string) => void;
}

export function CreateUser(props: CreateUserProps): JSX.Element {
  const [userFirstName, setUserFirstName] = useState("");
  const [userLastName, setUserLastName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleClick(): void {
    if (!userFirstName || !userLastName || !userEmail) return;

    setIsSubmitting(true);
    try {
      // TODO: API call to create a user
      setTimeout(() => {
        props.onSuccess(userEmail);
        setIsSubmitting(false);
      }, 1000);
    } catch (error) {
      // eslint-disable-next-line no-console -- Needed
      console.error("Error creating user:", error);
      setIsSubmitting(false);
    }
  }

  return (
    <div className="add-edit-user-container">
      <AddEditBaseDialog
        header="Create User"
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel="Create"
        disabled={!userFirstName || !userLastName || !userEmail}
        loading={isSubmitting}
      >
        <CommonInput
          label="First Name"
          field={userFirstName}
          onChange={setUserFirstName}
          required
        />
        <CommonInput
          label="Last Name"
          field={userLastName}
          onChange={setUserLastName}
          required
        />
        <CommonInput
          label="Email"
          field={userEmail}
          onChange={setUserEmail}
          required
          info="An invitation email will be sent to this address"
        />
      </AddEditBaseDialog>
    </div>
  );
}
