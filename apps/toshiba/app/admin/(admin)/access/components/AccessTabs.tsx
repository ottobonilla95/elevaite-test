"use client";
import { CommonButton } from "@repo/ui/components";
import { ACCESS_MANAGEMENT_TABS } from "../../lib/interfaces";
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
}

export function AccessTabs({
  selectedTab,
  setSelectedTab,
}: AccessTabsProps): JSX.Element {
  function handleTabSelection(tab: ACCESS_MANAGEMENT_TABS): void {
    setSelectedTab(tab);
  }

  return (
    <div className="access-tabs-container">
      <div className="tabs-container">
        {AccessManagementTabsArray.map(
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
        <UsersList isVisible={selectedTab === ACCESS_MANAGEMENT_TABS.USERS} />
      </div>
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
    </div>
  );
}
