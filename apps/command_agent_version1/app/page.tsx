"use client";

import { ToastContainer } from "react-toastify";
import AgentConfigForm from "./components/AgentConfigForm";
import "./page.scss";
import { AgentsProvider } from "./ui/contexts/AgentsContext";
import { WorkflowsProvider } from "./ui/contexts/WorkflowsContext";

export default function CommandAgent(): JSX.Element {
  return (
    <AgentsProvider autoRefreshInterval={60000}>
      <WorkflowsProvider autoRefreshInterval={60000}>
        <main style={{
          height: '100vh !important',
          width: '100vw',
          overflow: 'auto',
          position: 'relative',
          paddingTop: '52px' // Adjust based on your navbar height
        }}>
          <ToastContainer
            position="bottom-right"
            autoClose={4000}
          />
          <AgentConfigForm />
        </main>
      </WorkflowsProvider>
    </AgentsProvider>
  );
}