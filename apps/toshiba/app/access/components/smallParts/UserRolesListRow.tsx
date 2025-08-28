import { type CommonMenuItem } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ExtendedUserObject } from "../../../lib/interfaces";
import { ListRow, type RowStructure } from "../../../lib/components/ListRow";
import "./UserRolesListRow.scss";

interface UserRolesListRowProps {
  user: ExtendedUserObject;
  structure: RowStructure<ExtendedUserObject>[];
  menu: CommonMenuItem<ExtendedUserObject>[];
  menuToTop: boolean;
}

export function UserRolesListRow(props: UserRolesListRowProps): JSX.Element {
  const [displayUser, setDisplayUser] = useState<ExtendedUserObject>(
    props.user
  );

  useEffect(() => {
    // Prefer roles coming from the user object
    const roles = getDisplayRolesFromUser(props.user);
    setDisplayUser({ ...props.user, displayRoles: roles });
  }, [props.user]);

  function getDisplayRolesFromUser(
    user: ExtendedUserObject
  ): { roleLabel: string; roleParent?: string }[] {
    if (user.displayRoles && user.displayRoles.length > 0) {
      return user.displayRoles;
    }
    if ((user as any).is_superadmin) {
      return [{ roleLabel: "iOpex Admin" }];
    }
    if ((user as any).application_admin) {
      return [{ roleLabel: "Application Admin" }];
    }
    return [{ roleLabel: "User" }];
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
