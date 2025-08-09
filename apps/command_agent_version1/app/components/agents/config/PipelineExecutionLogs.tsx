"use client";

import React, { useState, useEffect } from 'react';
import { ProgressBar } from './ProgressBar';
import { LogsTabs } from './LogsTabs';
import "./PipelineExecutionLogs.scss";

interface PipelineStep {
  id: string;
  type: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress?: number;
  logs?: string[];
  output?: object;
  startTime?: string;
  endTime?: string;
}

interface PipelineExecutionLogsProps {
  steps: any[];
  isRunning: boolean;
  onComplete: () => void;
}

export function PipelineExecutionLogs({ 
  steps, 
  isRunning, 
  onComplete 
}: PipelineExecutionLogsProps): JSX.Element {
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);
  const [activeTab, setActiveTab] = useState<"logs" | "output">("logs");
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  // Initialize pipeline steps from props and sync with their status
  useEffect(() => {
    const syncedSteps: PipelineStep[] = steps.map((step, index) => {
      // Check if this step already exists in our state
      const existingStep = pipelineSteps.find(s => s.id === step.id);
      
      return {
        id: step.id || `step-${index}`,
        type: step.step_type || step.type,
        name: step.name || getStepDisplayName(step.step_type || step.type),
        status: step.status || 'pending',
        progress: step.status === 'completed' ? 100 : step.status === 'running' ? 50 : 0,
        logs: existingStep?.logs || [],
        output: existingStep?.output,
        startTime: existingStep?.startTime,
        endTime: existingStep?.endTime,
      };
    });
    
    setPipelineSteps(syncedSteps);
    
    // Select first step by default if none selected
    if (!selectedStep && syncedSteps.length > 0) {
      setSelectedStep(syncedSteps[0].id);
    }
  }, [steps]); // Only depend on steps prop changes

  // Watch for status changes and generate appropriate logs
  useEffect(() => {
    steps.forEach((step, index) => {
      const currentStepState = pipelineSteps.find(s => s.id === step.id);
      
      // If step just started running, generate initial logs
      if (step.status === 'running' && currentStepState?.status !== 'running') {
        const initialLogs = generateInitialLogs(step.name || getStepDisplayName(step.type));
        
        setPipelineSteps(prev => prev.map(s => 
          s.id === step.id ? {
            ...s,
            status: 'running',
            startTime: new Date().toISOString(),
            logs: [...(s.logs || []), ...initialLogs],
            progress: 20
          } : s
        ));

        // Add some progress logs over time for running step
        setTimeout(() => {
          const midProgressLogs = generateProgressLogs(step.name || getStepDisplayName(step.type), 50);
          setPipelineSteps(prev => prev.map(s => 
            s.id === step.id && s.status === 'running' ? {
              ...s,
              logs: [...(s.logs || []), ...midProgressLogs],
              progress: 70
            } : s
          ));
        }, 2000);
      }
      
      // If step just completed, generate completion logs
      if (step.status === 'completed' && currentStepState?.status !== 'completed') {
        const completionLogs = generateCompletionLogs(step.name || getStepDisplayName(step.type));
        
        setPipelineSteps(prev => prev.map(s => 
          s.id === step.id ? {
            ...s,
            status: 'completed',
            endTime: new Date().toISOString(),
            logs: [...(s.logs || []), ...completionLogs],
            output: getMockStepOutput(s.type),
            progress: 100
          } : s
        ));
      }

      // If step failed, generate error logs
      if (step.status === 'error' && currentStepState?.status !== 'error') {
        const errorLogs = generateErrorLogs(step.name || getStepDisplayName(step.type));
        
        setPipelineSteps(prev => prev.map(s => 
          s.id === step.id ? {
            ...s,
            status: 'error',
            endTime: new Date().toISOString(),
            logs: [...(s.logs || []), ...errorLogs],
            progress: 0
          } : s
        ));
      }
    });
  }, [steps, pipelineSteps]);

  const generateInitialLogs = (stepName: string): string[] => {
    return [
      `[${new Date().toLocaleTimeString()}] ======================================`,
      `[${new Date().toLocaleTimeString()}] Starting ${stepName}`,
      `[${new Date().toLocaleTimeString()}] ======================================`,
      `[${new Date().toLocaleTimeString()}] INFO: Pipeline execution initiated`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Environment: Production`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Node version: v18.17.0`,
      `[${new Date().toLocaleTimeString()}] INFO: Initializing step environment`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Creating temporary workspace`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Workspace created: /tmp/pipeline-${Date.now()}`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Setting environment variables`,
      `[${new Date().toLocaleTimeString()}] INFO: Checking system requirements`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Available memory: ${Math.floor(Math.random() * 2048 + 1024)}MB`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Available disk space: ${Math.floor(Math.random() * 50 + 10)}GB`,
      `[${new Date().toLocaleTimeString()}] DEBUG: CPU cores: ${Math.floor(Math.random() * 8 + 4)}`,
      `[${new Date().toLocaleTimeString()}] INFO: System requirements satisfied`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Loading configuration file`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Configuration validation passed`,
      `[${new Date().toLocaleTimeString()}] INFO: Configuration loaded successfully`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Validating input parameters`,
      `[${new Date().toLocaleTimeString()}] INFO: All input parameters valid`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Initializing logging framework`,
      `[${new Date().toLocaleTimeString()}] INFO: Step initialization complete`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Beginning main processing loop`,
    ];
  };

  const generateProgressLogs = (stepName: string, progress: number): string[] => {
    const logs = [
      `[${new Date().toLocaleTimeString()}] INFO: Processing ${stepName} - ${progress}% complete`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Current throughput: ${Math.floor(Math.random() * 1000 + 500)} items/sec`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Memory usage: ${Math.floor(Math.random() * 512 + 256)}MB`,
      `[${new Date().toLocaleTimeString()}] DEBUG: CPU usage: ${Math.floor(Math.random() * 40 + 20)}%`,
      `[${new Date().toLocaleTimeString()}] INFO: Network I/O: ${Math.floor(Math.random() * 10 + 1)}MB/s`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Active threads: ${Math.floor(Math.random() * 20 + 5)}`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Queue depth: ${Math.floor(Math.random() * 100 + 10)}`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Error rate: ${(Math.random() * 0.1).toFixed(3)}%`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Cache hit rate: ${(Math.random() * 30 + 70).toFixed(1)}%`,
    ];

    if (progress >= 50) {
      logs.push(
        `[${new Date().toLocaleTimeString()}] INFO: Reached ${progress}% completion milestone`,
        `[${new Date().toLocaleTimeString()}] DEBUG: Intermediate validation checkpoint`,
        `[${new Date().toLocaleTimeString()}] DEBUG: Data consistency check: PASSED`,
        `[${new Date().toLocaleTimeString()}] INFO: Checkpoint validation successful`,
      );
    }

    return logs;
  };

  const generateCompletionLogs = (stepName: string): string[] => {
    return [
      `[${new Date().toLocaleTimeString()}] INFO: Finalizing ${stepName} processing`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Flushing all buffers to disk`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Buffer flush complete: ${Math.floor(Math.random() * 1000 + 500)}KB written`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Syncing file system changes`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Writing output data to buffer`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Calculating data checksums`,
      `[${new Date().toLocaleTimeString()}] DEBUG: MD5 checksum: ${Math.random().toString(16).substr(2, 32)}`,
      `[${new Date().toLocaleTimeString()}] INFO: Performing comprehensive data validation`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Schema validation: PASSED`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Data integrity check: PASSED`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Validation checks passed: 15/15`,
      `[${new Date().toLocaleTimeString()}] INFO: All validation checks successful`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Generating audit trail`,
      `[${new Date().toLocaleTimeString()}] INFO: Cleaning up temporary resources`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Closing database connections: ${Math.floor(Math.random() * 5 + 2)}`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Memory freed: ${Math.floor(Math.random() * 256 + 128)}MB`,
      `[${new Date().toLocaleTimeString()}] INFO: Resource cleanup complete`,
      `[${new Date().toLocaleTimeString()}] INFO: Generating performance metrics`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Total items processed: ${Math.floor(Math.random() * 10000 + 5000)}`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Average processing time: ${(Math.random() * 50 + 10).toFixed(2)}ms/item`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Peak memory usage: ${Math.floor(Math.random() * 512 + 256)}MB`,
      `[${new Date().toLocaleTimeString()}] SUCCESS: ${stepName} completed successfully!`,
      `[${new Date().toLocaleTimeString()}] INFO: Execution time: ${(Math.random() * 30 + 10).toFixed(2)} seconds`,
      `[${new Date().toLocaleTimeString()}] INFO: Step output ready for next stage`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Output validation: PASSED`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Output format: JSON`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Output size: ${(Math.random() * 10 + 5).toFixed(1)}MB`,
      `[${new Date().toLocaleTimeString()}] INFO: Ready for pipeline continuation`,
      `[${new Date().toLocaleTimeString()}] ======================================`,
    ];
  };

  const generateErrorLogs = (stepName: string): string[] => {
    return [
      `[${new Date().toLocaleTimeString()}] ERROR: ${stepName} execution failed`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Exception caught in main processing loop`,
      `[${new Date().toLocaleTimeString()}] ERROR: Stack trace:`,
      `[${new Date().toLocaleTimeString()}] ERROR:   at processStep (pipeline.js:${Math.floor(Math.random() * 500 + 100)})`,
      `[${new Date().toLocaleTimeString()}] ERROR:   at Pipeline.execute (pipeline.js:${Math.floor(Math.random() * 100 + 50)})`,
      `[${new Date().toLocaleTimeString()}] DEBUG: Attempting error recovery`,
      `[${new Date().toLocaleTimeString()}] ERROR: Recovery failed - step execution terminated`,
      `[${new Date().toLocaleTimeString()}] INFO: Cleaning up partial results`,
      `[${new Date().toLocaleTimeString()}] ======================================`,
    ];
  };

  const getStepDisplayName = (stepType: string): string => {
    const names: Record<string, string> = {
      'load': 'Load Data',
      'parse': 'Parse Documents', 
      'chunk': 'Chunk Text',
      'embed': 'Generate Embeddings',
      'store': 'Store Vectors'
    };
    return names[stepType] || stepType;
  };

  const getMockStepOutput = (stepType: string): object => {
    // Return appropriate mock output based on step type
    const outputs: Record<string, object> = {
      'load': {
        "status": "completed",
        "files_processed": 3,
        "total_size_mb": 7.2,
        "file_types": ["pdf", "docx", "txt"],
        "processing_time": "2.34s",
        "metadata": {
          "encoding": "utf-8",
          "language_detected": "en",
          "total_characters": 45678
        },
        "performance_metrics": {
          "throughput": "3.2MB/s",
          "memory_peak": "128MB",
          "cpu_avg": "23%"
        }
      },
      'parse': {
        "status": "completed",
        "documents_processed": 3,
        "total_elements": 428,
        "element_types": {
          "paragraphs": 245,
          "headers": 23,
          "tables": 12,
          "images": 8,
          "lists": 140
        },
        "processing_time": "4.67s",
        "extraction_quality": {
          "text_confidence": 0.98,
          "structure_confidence": 0.95
        },
        "performance_metrics": {
          "throughput": "91.6 elements/s",
          "memory_peak": "256MB",
          "cpu_avg": "45%"
        }
      },
      'chunk': {
        "status": "completed",
        "input_elements": 428,
        "output_chunks": 574,
        "chunk_statistics": {
          "avg_chunk_size": 512,
          "min_chunk_size": 128,
          "max_chunk_size": 1024,
          "overlap_size": 64
        },
        "processing_time": "1.89s",
        "quality_metrics": {
          "semantic_coherence": 0.87,
          "boundary_quality": 0.92
        },
        "performance_metrics": {
          "throughput": "303.7 chunks/s",
          "memory_peak": "184MB",
          "cpu_avg": "31%"
        }
      },
      'embed': {
        "status": "completed",
        "chunks_processed": 574,
        "embeddings_generated": 574,
        "embedding_config": {
          "model": "text-embedding-ada-002",
          "dimensions": 1536,
          "batch_size": 32
        },
        "processing_time": "12.45s",
        "api_usage": {
          "total_tokens": 156789,
          "api_calls": 18,
          "cost_estimate": "$0.032"
        },
        "performance_metrics": {
          "throughput": "46.1 embeddings/s",
          "memory_peak": "312MB",
          "cpu_avg": "15%"
        }
      },
      'store': {
        "status": "completed",
        "vectors_stored": 574,
        "index_name": "vectorizer-index-prod",
        "storage_config": {
          "vector_db": "Pinecone",
          "namespace": "documents",
          "metric": "cosine"
        },
        "processing_time": "3.21s",
        "index_statistics": {
          "total_vectors": 574,
          "index_size_mb": 89.6,
          "avg_insert_time": "5.6ms"
        },
        "performance_metrics": {
          "throughput": "178.8 vectors/s",
          "memory_peak": "97MB",
          "cpu_avg": "18%"
        }
      }
    };
    
    return outputs[stepType] || { status: "completed", step_type: stepType };
  };

  const selectedStepData = pipelineSteps.find(step => step.id === selectedStep);
  const overallProgress = (pipelineSteps.filter(s => s.status === 'completed').length / pipelineSteps.length) * 100;

  return (
    <div className="pipeline-execution-logs">
      {/* Overall Progress */}
      <div className="overall-progress-section">
        <ProgressBar
          progress={overallProgress}
          isRunning={isRunning}
          label={`Pipeline Progress: ${pipelineSteps.filter(s => s.status === 'completed').length}/${pipelineSteps.length} steps completed`}
          icon={<img src="/icons/Side Icon Unselected.svg" alt="Pipeline" style={{ width: '16px', height: '16px' }} />}
        />
      </div>

      {/* Step Selection Pills */}
      <div className="step-selection" style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {pipelineSteps.map((step) => (
            <button
              key={step.id}
              onClick={() => setSelectedStep(step.id)}
              style={{
                padding: '6px 12px',
                fontSize: '12px',
                fontWeight: '500',
                borderRadius: '16px',
                border: '1px solid',
                backgroundColor: selectedStep === step.id ? '#f97316' : 'white',
                color: selectedStep === step.id ? 'white' : 
                       step.status === 'completed' ? '#059669' :
                       step.status === 'running' ? '#f59e0b' :
                       step.status === 'error' ? '#dc2626' : '#6b7280',
                borderColor: selectedStep === step.id ? '#f97316' :
                            step.status === 'completed' ? '#059669' :
                            step.status === 'running' ? '#f59e0b' :
                            step.status === 'error' ? '#dc2626' : '#e5e7eb',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              {step.status === 'completed' && '✓'}
              {step.status === 'running' && '⚡'}
              {step.status === 'error' && '❌'}
              {step.name}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Step Details */}
      {selectedStepData && (
        <div className="step-details">
          {/* Tabs for logs and output */}
          <LogsTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === "logs" && (
              <div className="logs-content">
                <pre className="logs-text">
                  {selectedStepData.logs && selectedStepData.logs.length > 0 
                    ? selectedStepData.logs.join('\n')
                    : 'Waiting for logs...'
                  }
                </pre>
              </div>
            )}
            
            {activeTab === "output" && (
              <div className="output-content">
                <pre className="output-text">
                  {selectedStepData.output 
                    ? JSON.stringify(selectedStepData.output, null, 2)
                    : selectedStepData.status === 'completed' 
                      ? 'Output generation in progress...'
                      : 'No output available yet...'
                  }
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}