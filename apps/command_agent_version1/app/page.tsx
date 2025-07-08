"use client";

import React from "react";
import AgentConfigForm from "./components/AgentConfigForm";
import { WorkflowsProvider } from "./ui/contexts/WorkflowsContext";
import { AgentsProvider } from "./ui/contexts/AgentsContext";
import "./page.scss";

export default function CommandAgent(): JSX.Element {
  return (
    <AgentsProvider autoRefreshInterval={60000}>
      <WorkflowsProvider autoRefreshInterval={60000}>
        <main style={{
          height: '100vh',
          width: '100vw',
          overflow: 'auto',
          position: 'relative',
          paddingTop: '52px' // Adjust based on your navbar height
        }}>
          <AgentConfigForm />
        </main>
      </WorkflowsProvider>
    </AgentsProvider>
  );
}