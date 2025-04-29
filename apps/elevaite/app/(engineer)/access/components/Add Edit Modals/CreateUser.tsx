import { CommonInput } from "@repo/ui/components";
import { useState, useEffect } from "react";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import { createUser } from "../../../lib/services/userService";
import "./AddEditUser.scss";

interface CreateUserProps {
  onClose: () => void;
  onSuccess: (email: string, message?: string) => void;
}

export function CreateUser(props: CreateUserProps): JSX.Element {
  const [userFirstName, setUserFirstName] = useState("");
  const [userLastName, setUserLastName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");

  // Email validation regex
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

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

  async function handleClick(): Promise<void> {
    if (!userFirstName || !userLastName || !userEmail || emailError) return;

    setIsSubmitting(true);
    setApiError("");

    try {
      // Call the API to create a user
      const result = await createUser({
        firstName: userFirstName,
        lastName: userLastName,
        email: userEmail,
      });

      if (result.success) {
        // User created successfully
        props.onSuccess(userEmail, result.message);
      } else {
        // Error creating user
        setApiError(result.message);
      }
    } catch (error) {
      // eslint-disable-next-line no-console -- Needed
      console.error("Error creating user:", error);
      setApiError("An unexpected error occurred. Please try again.");
    } finally {
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
        disabled={
          !userFirstName ||
          !userLastName ||
          !userEmail ||
          Boolean(emailError) ||
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
          required
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

        {apiError && <div className="api-error-message">{apiError}</div>}
      </AddEditBaseDialog>
    </div>
  );
}
