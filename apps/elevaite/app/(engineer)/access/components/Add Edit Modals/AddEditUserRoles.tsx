import { useEffect } from "react";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { type ExtendedUserObject } from "../../../../lib/interfaces";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUserRoles.scss";



interface AddEditUserRolesProps {
    user: ExtendedUserObject;
    onClose: () => void;
}

export function AddEditUserRoles(props: AddEditUserRolesProps): JSX.Element {
    const rolesContext = useRoles();

    useEffect(() => {
        console.log("Selected user:", props.user);
    }, [props.user]);


    // async function handleClick(): Promise<void> {
    function handleClick(): void {
        console.log("Applying");
        // if (!userFirstName || !userLastName) return;
        // let result: boolean;        
        // if (props.user) result = await rolesContext.editUser(props.user.id, userFirstName, userLastName);
        // else result = false; //await rolesContext.addUser();
        // if (result) props.onClose();
    }
    
    return (
        <div className="add-edit-user-roles-container">
            <AddEditBaseDialog
                header="Edit User roles"
                subHeader={[props.user.firstname, props.user.lastname].filter(Boolean).join(" ")}
                onClose={props.onClose}
                onClick={handleClick}
                buttonLabel="Apply"
                loading={rolesContext.loading.roles}
            >

                {/* <CommonInput
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
                    info={props.user ? "Email cannot be edited" : "Email will be filled by the auth token"}
                /> */}

                {/* User Roles adjustments */}

            </AddEditBaseDialog>
        </div>
    );
}