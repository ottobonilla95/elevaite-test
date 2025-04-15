"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { pipelineSteps } from "./lib/pipelineData";
import "./page.scss";

export default function Home(): JSX.Element {
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [executionMode, setExecutionMode] = useState<
    "configure" | "execute" | "monitor"
  >("configure");
  const [selectedProvider, setSelectedProvider] = useState<string>("sagemaker");
  const router = useRouter();

  const handleStepSelect = (stepId: string) => {
    setSelectedStep(stepId === selectedStep ? null : stepId);
  };

  const handleModeChange = (mode: "configure" | "execute" | "monitor") => {
    setExecutionMode(mode);
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
  };

  return (
    <div className="pipeline-container">
      <div className="pipeline-header">
        <h1>Document Processing Pipeline</h1>
        <p>
          Configure and execute the 5 key steps in the document processing
          pipeline
        </p>

        <div className="pipeline-controls">
          <div className="mode-selector">
            <button
              className={executionMode === "configure" ? "active" : ""}
              onClick={() => handleModeChange("configure")}
            >
              Configure
            </button>
            <button
              className={executionMode === "execute" ? "active" : ""}
              onClick={() => handleModeChange("execute")}
            >
              Execute
            </button>
            <button
              className={executionMode === "monitor" ? "active" : ""}
              onClick={() => handleModeChange("monitor")}
            >
              Monitor
            </button>
          </div>

          <div className="provider-selector">
            <label>Provider:</label>
            <select
              value={selectedProvider}
              onChange={(e) => handleProviderChange(e.target.value)}
            >
              <option value="sagemaker">SageMaker</option>
              <option value="airflow">Airflow</option>
              <option value="bedrock">Bedrock</option>
            </select>
          </div>
        </div>
      </div>

      <div className="pipeline-content">
        <div className="pipeline-steps">
          {pipelineSteps.map((step, index) => (
            <div
              key={step.id}
              className={`pipeline-step ${selectedStep === step.id ? "selected" : ""}`}
              onClick={() => handleStepSelect(step.id)}
            >
              <div className="step-number">{index + 1}</div>
              <div className="step-content">
                <h2>{step.title}</h2>
                <p>{step.description}</p>
                {selectedStep === step.id && (
                  <div className="step-details">
                    <p>{step.details}</p>

                    <div className="step-actions">
                      <button
                        className="learn-more-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/${step.id}`);
                        }}
                      >
                        Learn More
                      </button>

                      {executionMode === "configure" && (
                        <button
                          className="configure-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/${step.id}/configure`);
                          }}
                        >
                          Configure
                        </button>
                      )}

                      {executionMode === "execute" && (
                        <button
                          className="execute-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Execute the step
                            alert(
                              `Executing ${step.title} step with ${selectedProvider} provider`
                            );
                          }}
                        >
                          Execute
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="pipeline-right-panel">
          <div className="pipeline-flow">
            <h3>Pipeline Flow</h3>
            <div className="flow-diagram">
              {pipelineSteps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div className="flow-step">
                    <div
                      className={`flow-node ${selectedStep === step.id ? "selected" : ""}`}
                      onClick={() => handleStepSelect(step.id)}
                    >
                      {index + 1}
                    </div>
                    <div className="flow-title">{step.title}</div>
                  </div>
                  {index < pipelineSteps.length - 1 && (
                    <div className="flow-arrow">→</div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="execution-panel">
            <h3>
              {executionMode === "configure"
                ? "Configuration"
                : executionMode === "execute"
                  ? "Execution"
                  : "Monitoring"}
            </h3>
            {selectedStep ? (
              <div className="panel-content">
                <h4>
                  {pipelineSteps.find((s) => s.id === selectedStep)?.title}
                </h4>
                {executionMode === "configure" && (
                  <div className="configuration-options">
                    <p>
                      Configure options for{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}
                    </p>
                    <button
                      onClick={() => router.push(`/${selectedStep}/configure`)}
                      className="view-config-btn"
                    >
                      View Configuration Options
                    </button>
                  </div>
                )}

                {executionMode === "execute" && (
                  <div className="execution-options">
                    <p>
                      Execute{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                      with {selectedProvider}
                    </p>
                    <button
                      onClick={() =>
                        alert(
                          `Executing ${pipelineSteps.find((s) => s.id === selectedStep)?.title} step with ${selectedProvider} provider`
                        )
                      }
                      className="execute-step-btn"
                    >
                      Execute Step
                    </button>
                  </div>
                )}

                {executionMode === "monitor" && (
                  <div className="monitoring-options">
                    <p>
                      Monitor{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                      executions
                    </p>
                    <div className="execution-list">
                      <p>No recent executions found.</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="panel-content empty">
                <p>
                  Select a pipeline step to{" "}
                  {executionMode === "configure"
                    ? "configure"
                    : executionMode === "execute"
                      ? "execute"
                      : "monitor"}
                  .
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
