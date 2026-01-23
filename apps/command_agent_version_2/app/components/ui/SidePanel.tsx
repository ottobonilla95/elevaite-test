import { cls, CommonButton, SimpleInput } from "@repo/ui";
import { useState, type JSX } from "react";
import { CategoryId } from "../../lib/enums";
import { type SidePanelOption } from "../../lib/interfaces";
import { getCategoryLabel } from "../../lib/utilities/nodes";
import { Icons } from "../icons";
import "./SidePanel.scss";
import Actions from "./sidePanelSubgroups/Actions";
import Agents from "./sidePanelSubgroups/Agents";
import Api from "./sidePanelSubgroups/Api";
import ExternalAgents from "./sidePanelSubgroups/ExternalAgents";
import Inputs from "./sidePanelSubgroups/Inputs";
import Logic from "./sidePanelSubgroups/Logic";
import Outputs from "./sidePanelSubgroups/Outputs";
import SidePanelItem from "./sidePanelSubgroups/SidePanelItem";
import Triggers from "./sidePanelSubgroups/Triggers";

const sidePanelLayout: SidePanelOption[] = [
  {
    id: CategoryId.INPUTS,
    label: getCategoryLabel(CategoryId.INPUTS),
    icon: CategoryId.INPUTS,
    isCategory: true,
    children: <Inputs />,
  },
  {
    id: CategoryId.AGENTS,
    label: getCategoryLabel(CategoryId.AGENTS),
    icon: CategoryId.AGENTS,
    isCategory: true,
    children: <Agents />,
  },
  {
    id: CategoryId.EXTERNAL_AGENTS,
    label: getCategoryLabel(CategoryId.EXTERNAL_AGENTS),
    icon: CategoryId.EXTERNAL_AGENTS,
    isCategory: true,
    children: <ExternalAgents />,
  },
  {
    id: CategoryId.TRIGGERS,
    label: getCategoryLabel(CategoryId.TRIGGERS),
    icon: CategoryId.TRIGGERS,
    isCategory: true,
    children: <Triggers />,
  },
  {
    id: CategoryId.OUTPUTS,
    label: getCategoryLabel(CategoryId.OUTPUTS),
    icon: CategoryId.OUTPUTS,
    isCategory: true,
    children: <Outputs />,
  },
  // { id: CategoryId.API, label: getCategoryLabel(CategoryId.API), icon: CategoryId.API, isCategory: true, children: <Api /> },
  {
    id: CategoryId.ACTIONS,
    label: getCategoryLabel(CategoryId.ACTIONS),
    icon: CategoryId.ACTIONS,
    isCategory: true,
    children: <Actions />,
  },
  {
    id: CategoryId.LOGIC,
    label: getCategoryLabel(CategoryId.LOGIC),
    icon: CategoryId.LOGIC,
    isCategory: true,
    children: <Logic />,
  },
  // { id: CategoryId.PROMPTS, label: getCategoryLabel(CategoryId.PROMPTS), icon: CategoryId.PROMPTS, isCategory: true, nodeDetails: { categoryId: CategoryId.PROMPTS, isNewItem: true } },
  {
    id: CategoryId.KNOWLEDGE,
    label: getCategoryLabel(CategoryId.KNOWLEDGE),
    icon: CategoryId.KNOWLEDGE,
    isCategory: true,
    nodeDetails: { categoryId: CategoryId.KNOWLEDGE, isNewItem: true },
  },
  // { id: CategoryId.MEMORY, label: getCategoryLabel(CategoryId.MEMORY), icon: CategoryId.MEMORY, isCategory: true, nodeDetails: { categoryId: CategoryId.MEMORY, isNewItem: true } },
  {
    id: CategoryId.GUARDAILS,
    label: getCategoryLabel(CategoryId.GUARDAILS),
    icon: CategoryId.GUARDAILS,
    isCategory: true,
    nodeDetails: { categoryId: CategoryId.GUARDAILS, isNewItem: true },
  },
];

export function SidePanel(): JSX.Element {
  const [isPinnedOpen, setIsPinnedOpen] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function handleOptionClick(option: SidePanelOption): void {
    if (!option.children) return;
    toggleExpanded(option.id);
  }

  function handlePanelClick(): void {
    console.log("Panel clicked");
  }

  function handlePinClick(): void {
    setIsPinnedOpen(!isPinnedOpen);
  }

  function handleTransitionEnd(
    event: React.TransitionEvent<HTMLElement>,
  ): void {
    const element = event.currentTarget;
    if (event.propertyName !== "max-width") return;
    // const forcedOpen = element.classList.contains("open");
    // const hovered = element.matches(":hover");
    // const focused = element.matches(":focus-within");
    const width = element.getBoundingClientRect().width;

    if (width <= 40) {
      closeAllExpanded();
    }
  }

  function toggleExpanded(id: string): void {
    setExpanded((currentOption) => {
      const newOption = new Set(currentOption);
      newOption.has(id) ? newOption.delete(id) : newOption.add(id);
      return newOption;
    });
  }

  function isExpanded(id: string): boolean {
    return expanded.has(id);
  }

  function closeAllExpanded(): void {
    setExpanded(new Set());
  }

  return (
    <div className="side-panel-container">
      <div
        className={cls("side-panel-contents", isPinnedOpen && "open")}
        onTransitionEnd={handleTransitionEnd}
      >
        <div className="side-panel-header">
          <div className="side-panel-search-bar-container">
            <SimpleInput
              value={searchTerm}
              onChange={setSearchTerm}
              leftIcon={<Icons.SVGSearch />}
              placeholder="Search"
            />
          </div>
          <CommonButton onClick={handlePanelClick}>
            <Icons.SVGPanel />
          </CommonButton>
          <CommonButton
            onClick={handlePinClick}
            className={isPinnedOpen ? "active" : undefined}
            title="Pin / unpin the sidebar open"
          >
            <Icons.SVGPin />
          </CommonButton>
        </div>

        <div className="side-panel-scroller">
          <div className="side-panel-scroller-contents">
            {sidePanelLayout.map((option) => (
              <SidePanelItem
                key={option.id}
                option={option}
                onClick={handleOptionClick}
                isExpanded={isExpanded(option.id)}
                classname="main"
                preventDrag={Boolean(option.children)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
