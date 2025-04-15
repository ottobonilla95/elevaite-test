"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { pipelineSteps } from "./lib/pipelineData";
import "./page.scss";

export default function Home(): JSX.Element {
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const router = useRouter();

  return (
    <div className="pipeline-container">
      <div className="pipeline-header">
        <h1>Document Processing Pipeline</h1>
        <p>Explore the 5 key steps in the document processing pipeline</p>
      </div>

      <div className="pipeline-steps">
        {pipelineSteps.map((step, index) => (
          <div
            key={step.id}
            className={`pipeline-step ${selectedStep === step.id ? "selected" : ""}`}
            onClick={() =>
              setSelectedStep(step.id === selectedStep ? null : step.id)
            }
          >
            <div className="step-number">{index + 1}</div>
            <div className="step-content">
              <h2>{step.title}</h2>
              <p>{step.description}</p>
              {selectedStep === step.id && (
                <div className="step-details">
                  <p>{step.details}</p>
                  <button
                    className="learn-more-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/${step.id}`);
                    }}
                  >
                    Learn More
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="pipeline-visualization">
        <div className="pipeline-flow">
          {pipelineSteps.map((step, index) => (
            <div key={step.id} className="flow-step">
              <div
                className={`flow-node ${selectedStep === step.id ? "selected" : ""}`}
                onClick={() => router.push(`/${step.id}`)}
              >
                {index + 1}
              </div>
              <div className="flow-title">{step.title}</div>
              {index < pipelineSteps.length - 1 && (
                <div className="flow-arrow">→</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
