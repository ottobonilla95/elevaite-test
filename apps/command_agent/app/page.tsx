"use client";

import React from "react";
import AgentConfigForm from "./components/AgentConfigForm";
import "./page.scss";

export default function Chatbot(): JSX.Element {
  return (
    <main className="chatbot-main-container overflow-y-auto">
      <div className="w-full bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 pb-32">
        <div className="w-full max-w-4xl mx-auto px-4 sm:px-6">
          <header className="text-center mb-8">
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">
              iOPEX Command Agents
            </h1>
            <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto mt-2">
              Configure your AI-powered business assistant
            </p>
          </header>

          <div className="text-center mb-12">
            <div className="inline-block p-2 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg text-white font-bold text-sm mb-4">
              AGENT CONFIGURATION
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              Command Agent Setup
            </h2>
            <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto mt-2">
              Configure your AI command agent to automate tasks, enhance decision-making, and optimize workflows across your business.
            </p>
          </div>

          <AgentConfigForm />

          <footer className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Powered by elevAIte</p>
          </footer>
        </div>
      </div>
    </main>
  );
}