import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUser.scss";

interface UserCreatedConfirmationProps {
  email: string;
  onClose: () => void;
  message?: string;
}

export function UserCreatedConfirmation(
  props: UserCreatedConfirmationProps
): JSX.Element {
  const defaultMessage = `We've sent a user invitation to ${props.email}. Once they accept the invitation, they will be able to access the system.`;

  return (
    <div className="add-edit-user-container">
      <AddEditBaseDialog
        header="User Invitation Sent"
        onClose={props.onClose}
        onClick={props.onClose}
        buttonLabel="OK"
        singleButton={true}
      >
        <div className="confirmation-content">
          <p>{props.message ?? defaultMessage}</p>
        </div>
      </AddEditBaseDialog>
    </div>
  );
}
