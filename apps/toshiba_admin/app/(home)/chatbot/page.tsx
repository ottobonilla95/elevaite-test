"use client";

import { useState } from "react";
import { MainAreaSwitcher } from "../../components/advanced/MainAreaSwitcher";
import { ProjectSidebar } from "../../components/advanced/ProjectSidebar";
import "./page.scss";




export default function Chatbot(): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false)


  return (
    <main className={`chatbot-advanced-container ${isExpanded ? "sidebar-expanded" : "sidebar-collapsed"}`}>
      {/* <Sidebar/> */}
      <ProjectSidebar
        isExpanded={isExpanded}
        setIsExpanded={setIsExpanded}
      />
      <MainAreaSwitcher
        isSidebarCollapsed={isExpanded}
      />
    </main>
  );
}
