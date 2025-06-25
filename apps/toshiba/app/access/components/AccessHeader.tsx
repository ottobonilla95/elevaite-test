"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useRoles } from "../../lib/contexts/RolesContext";
// Define the enum locally to avoid import issues
enum ACCESS_MANAGEMENT_TABS {
  ACCOUNTS = "Accounts",
  PROJECTS = "Projects",
  USERS = "Users",
  ROLES = "Roles",
}
import "./AccessHeader.scss";

interface AccessHeaderProps {
  onRefresh: () => void;
  selectedTab: ACCESS_MANAGEMENT_TABS;
}

export function AccessHeader(props: AccessHeaderProps): JSX.Element {
  const rolesContext = useRoles();

  function handleAccessRefresh(): void {
    props.onRefresh();
  }

  return (
    <div className="access-header-container">
      <div className="part-container left">
        <div className="title">ACCESS MANAGEMENT</div>
      </div>

      <div className="part-container right">
        <CommonButton
          className={[
            "refresh-button",
            props.selectedTab === ACCESS_MANAGEMENT_TABS.ACCOUNTS &&
            rolesContext.loading.accounts
              ? "loading"
              : undefined,
            props.selectedTab === ACCESS_MANAGEMENT_TABS.PROJECTS &&
            rolesContext.loading.projects
              ? "loading"
              : undefined,
            props.selectedTab === ACCESS_MANAGEMENT_TABS.USERS &&
            rolesContext.loading.users
              ? "loading"
              : undefined,
            props.selectedTab === ACCESS_MANAGEMENT_TABS.ROLES &&
            rolesContext.loading.roles
              ? "loading"
              : undefined,
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={handleAccessRefresh}
          noBackground
        >
          <ElevaiteIcons.SVGRefresh />
        </CommonButton>
      </div>
    </div>
  );
}
