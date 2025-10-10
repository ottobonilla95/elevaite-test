import {
  CommonCheckbox,
  CommonInput,
  ElevaiteIcons,
} from "@repo/ui/components";
import { useState, useEffect } from "react";
import { createUser, reactivateUser } from "../../../lib/services/userService";
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

interface CreateUserProps {
  onClose: () => void;
  onSuccess: (email: string, message?: string) => void;
}

export function CreateUser(props: CreateUserProps): JSX.Element {
  const [userFirstName, setUserFirstName] = useState("");
  const [userLastName, setUserLastName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [userPassword, setUserPassword] = useState(generateClientPassword());
  const [isOneTimePassword, setIsOneTimePassword] = useState(true);
  const [isApplicationAdmin, setIsApplicationAdmin] = useState(false);
  const [isManager, setIsManager] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");

  // Email validation regex
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // Password validation regex
  const passwordLowercase = /[a-z]/;
  const passwordUppercase = /[A-Z]/;
  const passwordNumber = /[0-9]/;
  const passwordSpecial = /[!@#$%^&*(),.?":{}|<>]/;

  // Validate email when it changes
  useEffect(() => {
    if (!userEmail) {
      setEmailError("");
    } else if (!userEmail.includes("@")) {
      setEmailError("Email must contain @ symbol");
    } else if (!emailRegex.test(userEmail)) {
      setEmailError("Please enter a valid email address");
    } else {
      setEmailError("");
    }
  }, [userEmail]);

  // Validate password when it changes
  useEffect(() => {
    if (userPassword === "") {
      setPasswordError("Password is required");
      return;
    }

    if (typeof userPassword === "string" && userPassword.length < 9) {
      setPasswordError("Password must be at least 9 characters");
      return;
    }

    if (typeof userPassword === "string") {
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
        setPasswordError(
          "Password must contain at least one special character"
        );
        return;
      }
    }

    setPasswordError("");
  }, [userPassword]);

  async function handleClick(): Promise<void> {
    if (!userFirstName || !userEmail || emailError || passwordError) return;

    setIsSubmitting(true);
    setApiError("");

    try {
      const result = await createUser({
        firstName: userFirstName,
        lastName: userLastName || "",
        email: userEmail,
        password: userPassword,
        isOneTimePassword,
        isApplicationAdmin,
        isManager,
      });

      if (result.success) {
        props.onSuccess(userEmail, result.message);
      } else {
        // Check if this is a deleted user error
        if (result.error?.type === 'user_deleted') {
          const shouldReactivate = window.confirm(
            `This user was previously deleted and cannot be recreated.\n\n` +
            `Would you like to reactivate this user account instead?`
          );

          if (shouldReactivate && result.error.user_id) {
            await handleReactivateUser(result.error.user_id);
          } else {
            setApiError(result.message);
          }
        } else {
          setApiError(result.message);
        }
      }
    } catch (error) {
      console.error("Exception while creating user:", error);
      setApiError("An unexpected error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReactivateUser(userId: number): Promise<void> {
    try {
      setIsSubmitting(true);
      setApiError("");

      const result = await reactivateUser(userId);

      if (result.success) {
        props.onSuccess(userEmail, "User reactivated successfully!");
      } else {
        setApiError(result.message);
      }
    } catch (error) {
      console.error("Error reactivating user:", error);
      setApiError("Failed to reactivate user. Please try again.");
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
        header="Create User"
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel="Create"
        disabled={
          !userFirstName ||
          !userEmail ||
          Boolean(emailError) ||
          Boolean(passwordError) ||
          isSubmitting
        }
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
        />
        <CommonInput
          label="Email"
          field={userEmail}
          onChange={setUserEmail}
          required
          placeholder="example@company.com"
          errorMessage={emailError}
          info={
            !emailError
              ? "An invitation email will be sent to this address"
              : undefined
          }
        />
        <div className="password-field-container">
          <div className="common-input-container">
            <div className="labels">
              <span className="title">
                Password
                <span className="required">*</span>
              </span>
              <div
                className="info"
                title="Must be at least 9 characters with uppercase, lowercase, numbers, and special characters"
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
        <CommonCheckbox
          label="Toshiba Admin"
          defaultTrue={isApplicationAdmin}
          onChange={setIsApplicationAdmin}
          info="Make the user an application admin?"
        />
        <CommonCheckbox
          label="Manager"
          defaultTrue={isManager}
          onChange={setIsManager}
          info="Make the user a manager (dashboard access only)?"
        />

        {apiError ? <div className="api-error-message">{apiError}</div> : null}
      </AddEditBaseDialog>
    </div>
  );
}