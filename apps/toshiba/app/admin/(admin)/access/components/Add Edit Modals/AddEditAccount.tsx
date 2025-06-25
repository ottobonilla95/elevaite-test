import {
  CommonFormLabels,
  CommonInput,
  SimpleTextarea,
} from "@repo/ui/components";
import { useState } from "react";
import { useRoles } from "../../../lib/contexts/RolesContext";
import { type AccountObject } from "../../../lib/interfaces";
import "./AddEditAccount.scss";
import { AddEditBaseDialog } from "./AddEditBaseDialog";

interface AddEditAccountProps {
  account: AccountObject | undefined;
  onClose: () => void;
}

export function AddEditAccount(props: AddEditAccountProps): JSX.Element {
  const rolesContext = useRoles();
  const [accountName, setAccountName] = useState("");
  const [accountDescription, setAccountDescription] = useState(
    props.account?.description ?? ""
  );

  async function handleClick(): Promise<void> {
    if (!accountName) return;
    let result: boolean;
    if (props.account)
      result = await rolesContext.editAccount(
        props.account.id,
        accountName,
        accountDescription
      );
    else
      result = await rolesContext.addAccount(accountName, accountDescription);
    if (result) props.onClose();
  }

  return (
    <div className="add-edit-account-container">
      <AddEditBaseDialog
        header={props.account ? "Edit Account" : "Add Account"}
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel={props.account ? "Apply" : "Add"}
        disabled={
          !accountName ||
          (props.account &&
            props.account.name === accountName &&
            props.account.description === accountDescription)
        }
        loading={rolesContext.loading.addEditAccount}
      >
        <CommonInput
          label="Account Name"
          field={accountName}
          onChange={setAccountName}
          initialValue={props.account?.name}
          required
        />

        <CommonFormLabels label="Account Description">
          <SimpleTextarea
            value={accountDescription}
            onChange={setAccountDescription}
            useCommonStyling
            rows={8}
          />
        </CommonFormLabels>
      </AddEditBaseDialog>
    </div>
  );
}
