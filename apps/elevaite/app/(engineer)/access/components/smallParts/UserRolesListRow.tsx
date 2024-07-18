import { type CommonMenuItem } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { type ExtendedUserObject } from "../../../../lib/interfaces";
import { ListRow, type RowStructure } from "./ListRow";
import "./UserRolesListRow.scss";



interface UserRolesListRowProps {
    user: ExtendedUserObject;    
    structure: RowStructure<ExtendedUserObject>[];
    menu: CommonMenuItem<ExtendedUserObject>[];
    menuToTop: boolean;
}

export function UserRolesListRow(props: UserRolesListRowProps): JSX.Element {
    const rolesContext = useRoles();
    const [displayUser, setDisplayUser] = useState<ExtendedUserObject>(props.user);


    useEffect(() => {
        void updateUserProfile(props.user.id);
    }, [props.user.id]);


    async function updateUserProfile(userId: string): Promise<void> {
        setDisplayUser(current => { return {...current, displayRoles: [{roleLabel: "loading"}]}});
        const fetchedUser = await rolesContext.getUserProfile(userId);
        if (!fetchedUser) return;
        const roles: { roleLabel: string; roleParent?: string;}[] = [];
        if (fetchedUser.is_superadmin) roles.push({roleLabel: "Superadmin"});
        if (fetchedUser.account_memberships) {
            for (const i of fetchedUser.account_memberships) {
                if (i.is_admin) roles.push({roleLabel: "Admin", roleParent: i.account_name});
                for (const j of i.roles) {
                    roles.push({roleLabel: j.name, roleParent: i.account_name});
                }
            }
        }
        setDisplayUser(current => { return {...current, displayRoles: roles}});
    }



    return (
        <ListRow<ExtendedUserObject>
            rowItem={displayUser}
            structure={props.structure}
            menu={props.menu}
            menuToTop={props.menuToTop}
        />
    );
}