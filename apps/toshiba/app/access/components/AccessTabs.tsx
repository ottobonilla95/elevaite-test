"use client";
import { CommonButton } from "@repo/ui/components";
import { useSession } from "next-auth/react";
// Try direct enum definition to avoid import issues
enum ACCESS_MANAGEMENT_TABS {
  ACCOUNTS = "Accounts",
  PROJECTS = "Projects",
  USERS = "Users",
  ROLES = "Roles",
}
import "./AccessTabs.scss";
import { AccountsList } from "./AccountsList";
import { ProjectsList } from "./ProjectsList";
import { RolesList } from "./RolesList";
import { UsersList } from "./UsersList";

const AccessManagementTabsArray: {
  label: ACCESS_MANAGEMENT_TABS;
  isDisabled?: boolean;
}[] = [
  { label: ACCESS_MANAGEMENT_TABS.ACCOUNTS },
  { label: ACCESS_MANAGEMENT_TABS.PROJECTS },
  { label: ACCESS_MANAGEMENT_TABS.USERS },
  { label: ACCESS_MANAGEMENT_TABS.ROLES },
];

interface AccessTabsProps {
  selectedTab: ACCESS_MANAGEMENT_TABS;
  setSelectedTab: (tab: ACCESS_MANAGEMENT_TABS) => void;
  isSuperAdmin?: boolean;
}

export function AccessTabs({
  selectedTab,
  setSelectedTab,
  isSuperAdmin,
}: AccessTabsProps): JSX.Element {
  const { data: session } = useSession();

  const isAppAdminSession = (session?.user as any)?.application_admin === true;
  const effectiveIsSuper =
    isSuperAdmin ?? (session?.user as any)?.is_superuser === true;

  function handleTabSelection(tab: ACCESS_MANAGEMENT_TABS): void {
    setSelectedTab(tab);
  }

  const visibleTabs = AccessManagementTabsArray.filter((item) => {
    // Server-enforced: only superusers see all tabs; app-admins see Users only
    if (effectiveIsSuper) return true;
    return item.label === ACCESS_MANAGEMENT_TABS.USERS;
  });

  return (
    <div className="access-tabs-container">
      <div className="tabs-container">
        {visibleTabs.map(
          (item: { label: ACCESS_MANAGEMENT_TABS; isDisabled?: boolean }) => (
            <CommonButton
              key={item.label}
              className={[
                "tab-button",
                selectedTab === item.label ? "active" : undefined,
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => {
                handleTabSelection(item.label);
              }}
              disabled={item.isDisabled}
            >
              {item.label}
            </CommonButton>
          )
        )}
      </div>

      {effectiveIsSuper && (
        <div
          className={[
            "payload-container",
            selectedTab === ACCESS_MANAGEMENT_TABS.ACCOUNTS
              ? "is-visible"
              : undefined,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <AccountsList
            isVisible={selectedTab === ACCESS_MANAGEMENT_TABS.ACCOUNTS}
          />
        </div>
      )}
      {effectiveIsSuper && (
        <div
          className={[
            "payload-container",
            selectedTab === ACCESS_MANAGEMENT_TABS.PROJECTS
              ? "is-visible"
              : undefined,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <ProjectsList
            isVisible={selectedTab === ACCESS_MANAGEMENT_TABS.PROJECTS}
          />
        </div>
      )}
      <div
        className={[
          "payload-container",
          selectedTab === ACCESS_MANAGEMENT_TABS.USERS
            ? "is-visible"
            : undefined,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <UsersList
          isVisible={selectedTab === ACCESS_MANAGEMENT_TABS.USERS}
          isSuperAdmin={effectiveIsSuper}
        />
      </div>
      {effectiveIsSuper && (
        <div
          className={[
            "payload-container",
            selectedTab === ACCESS_MANAGEMENT_TABS.ROLES
              ? "is-visible"
              : undefined,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <RolesList isVisible={selectedTab === ACCESS_MANAGEMENT_TABS.ROLES} />
        </div>
      )}
    </div>
  );
}
