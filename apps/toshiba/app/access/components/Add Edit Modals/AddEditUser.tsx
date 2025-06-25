import { CommonInput } from "@repo/ui/components";
import { useState } from "react";
import { useRoles } from "../../../lib/contexts/RolesContext";
import { type ExtendedUserObject } from "../../../lib/interfaces";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUser.scss";

interface AddEditUserProps {
  user: ExtendedUserObject | undefined;
  onClose: () => void;
}

export function AddEditUser(props: AddEditUserProps): JSX.Element {
  const rolesContext = useRoles();
  const [userFirstName, setUserFirstName] = useState(
    props.user?.firstname ?? ""
  );
  const [userLastName, setUserLastName] = useState(props.user?.lastname ?? "");
  const [userEmail, setUserEmail] = useState(props.user?.email ?? "");

  async function handleClick(): Promise<void> {
    if (!userFirstName || !userLastName) return;
    let result: boolean;
    if (props.user)
      result = await rolesContext.editUser(
        props.user.id,
        userFirstName,
        userLastName
      );
    else result = false; //await rolesContext.addUser();
    if (result) props.onClose();
  }

  return (
    <div className="add-edit-user-container">
      <AddEditBaseDialog
        header={props.user ? "Edit User" : "Add User"}
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel={props.user ? "Apply" : "Add"}
        disabled={
          !userFirstName ||
          !userLastName ||
          !userEmail ||
          (Boolean(props.user) &&
            props.user?.firstname === userFirstName &&
            props.user.lastname === userLastName)
        }
        loading={rolesContext.loading.addEditUser}
      >
        <CommonInput
          label="First Name"
          field={userFirstName}
          onChange={setUserFirstName}
          initialValue={props.user?.firstname}
          required
        />
        <CommonInput
          label="Last Name"
          field={userLastName}
          onChange={setUserLastName}
          initialValue={props.user?.lastname}
          required
        />
        <CommonInput
          label="Email"
          field={userEmail}
          onChange={setUserEmail}
          initialValue={props.user?.email}
          required
          disabled
          info={
            props.user
              ? "Email cannot be edited"
              : "Email will be filled by the auth token"
          }
        />

        {/* User Roles adjustments */}
      </AddEditBaseDialog>
    </div>
  );
}
