"use client";

import React from "react";
import AgentConfigForm from "./components/AgentConfigForm";
import "./page.scss";

export default function CommandAgent(): JSX.Element {
  return (
    <main style={{
      height: '100vh',
      width: '100vw',
      overflow: 'auto',
      position: 'relative',
      paddingTop: '52px' // Adjust based on your navbar height
    }}>
      <AgentConfigForm />
    </main>
  );
}