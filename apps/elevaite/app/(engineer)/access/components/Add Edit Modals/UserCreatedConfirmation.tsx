import { CommonButton } from "@repo/ui/components";
import "./AddEditUser.scss";

interface UserCreatedConfirmationProps {
  email: string;
  onClose: () => void;
}

export function UserCreatedConfirmation(
  props: UserCreatedConfirmationProps
): JSX.Element {
  return (
    <div className="add-edit-user-container">
      <div className="user-created-confirmation">
        <h2>User Invitation Sent</h2>
        <p>
          We&apos;ve sent an email invitation to <strong>{props.email}</strong>.
          Once they accept the invitation, they&apos;ll be able to access the
          system.
        </p>
        <div className="button-container">
          <CommonButton onClick={props.onClose} className="go-back-button">
            OK
          </CommonButton>
        </div>
      </div>
    </div>
  );
}
