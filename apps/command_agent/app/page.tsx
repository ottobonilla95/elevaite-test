"use client";

import React from "react";
import AgentConfigForm from "./components/AgentConfigForm";
import "./page.scss";

export default function CommandAgent(): JSX.Element {
  return (
    <main className="h-screen w-screen overflow-hidden">
      <AgentConfigForm />
    </main>
  );
}