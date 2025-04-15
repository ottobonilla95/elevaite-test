"use client";
import { useParams, useRouter } from "next/navigation";
import { pipelineSteps } from "../lib/pipelineData";
import "./page.scss";

export default function StepPage(): JSX.Element {
  const params = useParams();
  const router = useRouter();
  const stepId = params.step as string;
  
  const step = pipelineSteps.find(s => s.id === stepId);
  
  if (!step) {
    return (
      <div className="step-not-found">
        <h1>Step not found</h1>
        <p>The requested pipeline step does not exist.</p>
        <button onClick={() => router.push('/')}>Return to Pipeline Overview</button>
      </div>
    );
  }
  
  return (
    <div className="step-detail-container">
      <div className="step-detail-header">
        <button className="back-button" onClick={() => router.push('/')}>
          ← Back to Pipeline
        </button>
        <h1>{step.title}</h1>
        <p className="step-description">{step.description}</p>
      </div>
      
      <div className="step-detail-content">
        <div className="detail-section">
          <h2>Overview</h2>
          <p>{step.details}</p>
        </div>
        
        <div className="detail-section">
          <h2>Key Features</h2>
          <ul className="features-list">
            {step.features.map((feature, index) => (
              <li key={index}>{feature}</li>
            ))}
          </ul>
        </div>
        
        <div className="detail-section">
          <h2>Examples</h2>
          <div className="examples-container">
            {step.examples.map((example, index) => (
              <div key={index} className="example-card">
                <div className="example-input">
                  <h3>Input</h3>
                  <p>{example.input}</p>
                </div>
                <div className="example-arrow">→</div>
                <div className="example-output">
                  <h3>Output</h3>
                  <p>{example.output}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="detail-section">
          <h2>Pipeline Position</h2>
          <div className="pipeline-position">
            {pipelineSteps.map((s, index) => (
              <div key={s.id} className="position-step">
                <div 
                  className={`position-node ${s.id === stepId ? 'current' : ''}`}
                  onClick={() => router.push(`/${s.id}`)}
                >
                  {index + 1}
                </div>
                <div className="position-title">{s.title}</div>
                {index < pipelineSteps.length - 1 && <div className="position-arrow">→</div>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
