import { CommonCheckbox, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import { resetUserPassword } from "../../lib/services/authUserService";
import { type ExtendedUserObject } from "../../../../lib/interfaces";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUser.scss";

// Client-side function to generate a secure password
function generateClientPassword(): string {
  const length = 16;
  const lowercase = "abcdefghijklmnopqrstuvwxyz";
  const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const numbers = "0123456789";
  const special = '!@#$%^&*(),.?":{}|<>';

  const allChars = lowercase + uppercase + numbers + special;

  // Ensure at least one of each character type
  let password =
    lowercase.charAt(Math.floor(Math.random() * lowercase.length)) +
    uppercase.charAt(Math.floor(Math.random() * uppercase.length)) +
    numbers.charAt(Math.floor(Math.random() * numbers.length)) +
    special.charAt(Math.floor(Math.random() * special.length));

  // Fill the rest with random characters
  for (let i = 4; i < length; i++) {
    password += allChars.charAt(Math.floor(Math.random() * allChars.length));
  }

  // Shuffle the password
  return password
    .split("")
    .sort(() => 0.5 - Math.random())
    .join("");
}

interface ResetUserPasswordProps {
  user: ExtendedUserObject;
  onClose: () => void;
  onSuccess: (email: string, message?: string) => void;
}

export function ResetUserPassword(props: ResetUserPasswordProps): JSX.Element {
  const [userPassword, setUserPassword] = useState(generateClientPassword());
  const [isOneTimePassword, setIsOneTimePassword] = useState(true);
  const [showPassword, setShowPassword] = useState(true); // Show password by default for admin
  const [passwordError, setPasswordError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");

  // Password validation regex
  const passwordLowercase = /[a-z]/;
  const passwordUppercase = /[A-Z]/;
  const passwordNumber = /[0-9]/;
  const passwordSpecial = /[!@#$%^&*(),.?":{}|<>]/;

  // Validate password when it changes
  useEffect(() => {
    if (!userPassword) {
      setPasswordError("Password is required");
      return;
    }

    if (userPassword.length < 12) {
      setPasswordError("Password must be at least 12 characters");
      return;
    }

    if (!passwordLowercase.test(userPassword)) {
      setPasswordError("Password must contain at least one lowercase letter");
      return;
    }

    if (!passwordUppercase.test(userPassword)) {
      setPasswordError("Password must contain at least one uppercase letter");
      return;
    }

    if (!passwordNumber.test(userPassword)) {
      setPasswordError("Password must contain at least one number");
      return;
    }

    if (!passwordSpecial.test(userPassword)) {
      setPasswordError("Password must contain at least one special character");
      return;
    }

    setPasswordError("");
  }, [userPassword]);

  async function handleClick(): Promise<void> {
    if (passwordError) return;

    setIsSubmitting(true);
    setApiError("");

    try {
      // Call the API to reset the user's password
      const result = await resetUserPassword({
        userId: props.user.id,
        email: props.user.email,
        password: userPassword,
        isOneTimePassword,
      });

      if (result.success) {
        // Password reset successfully
        props.onSuccess(props.user.email, result.message);
      } else {
        // Error resetting password
        setApiError(result.message);
      }
    } catch (error) {
      // eslint-disable-next-line no-console -- Needed
      console.error("Error resetting password:", error);
      setApiError("An unexpected error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function regeneratePassword(): void {
    setUserPassword(generateClientPassword());
  }

  return (
    <div className="add-edit-user-container">
      <AddEditBaseDialog
        header="Reset User Password"
        subHeader={`${props.user.firstname ?? ""} ${props.user.lastname ?? ""} (${props.user.email})`}
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel="Reset Password"
        disabled={Boolean(passwordError) || isSubmitting}
        loading={isSubmitting}
      >
        <div className="password-field-container">
          <div className="common-input-container">
            <div className="labels">
              <span className="title">
                New Password
                <span className="required">*</span>
              </span>
              <div
                className="info"
                title="Must be at least 12 characters with uppercase, lowercase, numbers, and special characters"
              >
                <ElevaiteIcons.SVGInfo />
              </div>
              <div className="error-message">{passwordError}</div>
            </div>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                value={userPassword}
                onChange={(e) => {
                  setUserPassword(e.target.value);
                }}
                required
              />
              <div className="password-controls">
                <button
                  type="button"
                  className="regenerate-password-btn"
                  onClick={regeneratePassword}
                  title="Generate new password"
                >
                  <ElevaiteIcons.SVGRefresh size={14} />
                </button>
                <button
                  type="button"
                  className="toggle-password-visibility"
                  onClick={() => {
                    setShowPassword(!showPassword);
                  }}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          </div>
        </div>
        <CommonCheckbox
          label="One time password?"
          defaultTrue={isOneTimePassword}
          onChange={setIsOneTimePassword}
          info="If checked, user will be required to change password on first login"
        />

        {apiError ? <div className="api-error-message">{apiError}</div> : null}
      </AddEditBaseDialog>
    </div>
  );
}
