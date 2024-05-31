"use client"
import { useState } from "react";
import { CostContextProvider } from "../../lib/contexts/CostContext";
import { CostBarChart } from "./components/CostBarChart";
import { CostHeader } from "./components/CostHeader";
import { CostSidebar } from "./components/CostSidebar";
import { CostList } from "./components/CostList";
import "./page.scss";



export default function Page(): JSX.Element {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  function handleSidebarToggle(): void {
    setIsSidebarOpen(current => !current);
  }

  return (
    <CostContextProvider>
      <div className={["cost-main-container", isSidebarOpen ? undefined : "closed"].filter(Boolean).join(" ")}>
        <CostHeader isSidebarOpen={isSidebarOpen} onSidebarToggle={handleSidebarToggle} />
        <CostSidebar/>
        <div className="cost-details-container">
          <CostBarChart/>
          <CostList/>
        </div>
      </div>
    </CostContextProvider>
  );
}
