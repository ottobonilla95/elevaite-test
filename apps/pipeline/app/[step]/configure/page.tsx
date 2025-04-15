"use client";
import { useParams, useRouter } from "next/navigation";
import React, { useState } from "react";
import { pipelineSteps } from "../../lib/pipelineData";
import "./page.scss";

export default function ConfigurePage(): JSX.Element {
  const params = useParams();
  const router = useRouter();
  const stepId = params.step as string;

  const step = pipelineSteps.find((s) => s.id === stepId);
  const [provider, setProvider] = useState<string>("sagemaker");
  const [config, setConfig] = useState<Record<string, any>>({});

  if (!step) {
    return (
      <div className="step-not-found">
        <h1>Step not found</h1>
        <p>The requested pipeline step does not exist.</p>
        <button onClick={() => router.push("/")}>
          Return to Pipeline Overview
        </button>
      </div>
    );
  }

  // Initialize config with default values
  useState(() => {
    const defaultConfig: Record<string, any> = {};
    step.configOptions.forEach((option) => {
      defaultConfig[option.id] = option.default;
    });
    setConfig(defaultConfig);
  });

  const handleConfigChange = (optionId: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [optionId]: value,
    }));
  };

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
  };

  const handleSaveConfig = () => {
    // In a real app, this would save the configuration to the backend
    alert(`Configuration for ${step.title} saved with provider ${provider}`);
    router.push("/");
  };

  return (
    <div className="configure-container">
      <div className="configure-header">
        <button className="back-button" onClick={() => router.push("/")}>
          ← Back to Pipeline
        </button>
        <h1>Configure {step.title} Step</h1>
        <p>{step.description}</p>
      </div>

      <div className="configure-content">
        <div className="provider-selection">
          <h2>Provider</h2>
          <div className="provider-options">
            {Object.entries(step.providers).map(
              ([providerName, providerInfo]) => (
                <div
                  key={providerName}
                  className={`provider-option ${provider === providerName ? "selected" : ""} ${!providerInfo.supported ? "disabled" : ""}`}
                  onClick={() =>
                    providerInfo.supported && handleProviderChange(providerName)
                  }
                >
                  <div className="provider-name">{providerName}</div>
                  <div className="provider-status">
                    {providerInfo.supported ? "Supported" : "Not Supported"}
                  </div>
                  {providerInfo.description && (
                    <div className="provider-description">
                      {providerInfo.description}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        </div>

        <div className="config-options">
          <h2>Configuration Options</h2>
          <div className="options-list">
            {step.configOptions.map((option) => (
              <div key={option.id} className="config-option">
                <label htmlFor={option.id}>{option.label}</label>

                {option.type === "select" && (
                  <select
                    id={option.id}
                    value={config[option.id] || option.default}
                    onChange={(e) =>
                      handleConfigChange(option.id, e.target.value)
                    }
                  >
                    {option.options?.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                )}

                {option.type === "text" && (
                  <input
                    type="text"
                    id={option.id}
                    value={config[option.id] || option.default}
                    onChange={(e) =>
                      handleConfigChange(option.id, e.target.value)
                    }
                  />
                )}

                {option.type === "number" && (
                  <input
                    type="number"
                    id={option.id}
                    value={config[option.id] || option.default}
                    onChange={(e) =>
                      handleConfigChange(option.id, parseFloat(e.target.value))
                    }
                  />
                )}

                {option.type === "checkbox" && (
                  <input
                    type="checkbox"
                    id={option.id}
                    checked={config[option.id] || (option.default as boolean)}
                    onChange={(e) =>
                      handleConfigChange(option.id, e.target.checked)
                    }
                  />
                )}

                {option.type === "radio" && option.options && (
                  <div className="radio-options">
                    {option.options.map((opt) => (
                      <div key={opt} className="radio-option">
                        <input
                          type="radio"
                          id={`${option.id}-${opt}`}
                          name={option.id}
                          value={opt}
                          checked={
                            (config[option.id] || option.default) === opt
                          }
                          onChange={() => handleConfigChange(option.id, opt)}
                        />
                        <label htmlFor={`${option.id}-${opt}`}>{opt}</label>
                      </div>
                    ))}
                  </div>
                )}

                {option.description && (
                  <div className="option-description">{option.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="config-actions">
          <button className="cancel-button" onClick={() => router.push("/")}>
            Cancel
          </button>
          <button className="save-button" onClick={handleSaveConfig}>
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
