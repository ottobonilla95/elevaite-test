import { CommonButton } from "@repo/ui/components";
import "./AddEditUser.scss";

interface UserCreatedConfirmationProps {
  email: string;
  onClose: () => void;
  message?: string;
}

export function UserCreatedConfirmation(
  props: UserCreatedConfirmationProps
): JSX.Element {
  const defaultMessage = `We've sent an email invitation to <strong>${props.email}</strong> with
    a temporary password. Once they log in, they'll be prompted to set a new
    password before accessing the system.`;

  return (
    <div className="add-edit-user-container">
      <div className="user-created-confirmation">
        <h2>User Created Successfully</h2>
        <p
          dangerouslySetInnerHTML={{ __html: props.message ?? defaultMessage }}
        />
        <p className="note">
          Note: If the user doesn&apos;t receive the email, they can use the
          &quot;Forgot Password&quot; option on the login page to get a new
          temporary password.
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
