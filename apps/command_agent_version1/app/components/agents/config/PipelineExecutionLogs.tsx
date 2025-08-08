"use client";

import React, { useState, useEffect } from 'react';
import { ProgressBar } from './ProgressBar';
import { LogsTabs } from './LogsTabs';
import "./PipelineExecutionLogs.scss";

interface PipelineStep {
  id: string;
  type: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
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
  const [currentStep, setCurrentStep] = useState(0);
  const [activeTab, setActiveTab] = useState<"logs" | "output">("logs");
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  // Initialize pipeline steps from props
  useEffect(() => {
    const initialSteps: PipelineStep[] = steps.map((step, index) => ({
      id: step.id || `step-${index}`,
      type: step.step_type || step.type,
      name: step.name || getStepDisplayName(step.step_type || step.type),
      status: 'pending',
      progress: 0,
      logs: [],
      output: undefined,
    }));
    setPipelineSteps(initialSteps);
    
    // Select first step by default
    if (initialSteps.length > 0) {
      setSelectedStep(initialSteps[0].id);
    }
  }, [steps]);

  // Simulate pipeline execution when running starts
  useEffect(() => {
    if (!isRunning || pipelineSteps.length === 0) return;

    // Start with first step
    setCurrentStep(0);
    
    // Simulate step-by-step execution
    const executeSteps = async () => {
      for (let i = 0; i < pipelineSteps.length; i++) {
        const step = pipelineSteps[i];
        
        // Start step with extensive initial logs (40+ lines)
        const initialLogs = [
          `[${new Date().toLocaleTimeString()}] ======================================`,
          `[${new Date().toLocaleTimeString()}] Starting ${step.name} (${step.type})`,
          `[${new Date().toLocaleTimeString()}] ======================================`,
          `[${new Date().toLocaleTimeString()}] INFO: Pipeline execution initiated`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Environment: Production`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Node version: v18.17.0`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Platform: linux x64`,
          `[${new Date().toLocaleTimeString()}] INFO: Initializing step environment`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Creating temporary workspace`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Workspace created: /tmp/pipeline-${Date.now()}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Setting environment variables`,
          `[${new Date().toLocaleTimeString()}] DEBUG: PATH updated with tool binaries`,
          `[${new Date().toLocaleTimeString()}] DEBUG: PYTHONPATH configured`,
          `[${new Date().toLocaleTimeString()}] DEBUG: JAVA_HOME detected: /usr/lib/jvm/java-11`,
          `[${new Date().toLocaleTimeString()}] INFO: Checking system requirements`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Available memory: ${Math.floor(Math.random() * 2048 + 1024)}MB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Available disk space: ${Math.floor(Math.random() * 50 + 10)}GB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: CPU cores: ${Math.floor(Math.random() * 8 + 4)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Network connectivity: OK`,
          `[${new Date().toLocaleTimeString()}] DEBUG: DNS resolution: OK`,
          `[${new Date().toLocaleTimeString()}] INFO: System requirements satisfied`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Loading configuration file`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Config file: /app/config/pipeline.yml`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Parsing YAML configuration`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Configuration validation passed`,
          `[${new Date().toLocaleTimeString()}] INFO: Configuration loaded successfully`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Validating input parameters`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Parameter validation: type checking`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Parameter validation: range checking`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Parameter validation: dependency checking`,
          `[${new Date().toLocaleTimeString()}] INFO: All input parameters valid`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Initializing logging framework`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Log level: DEBUG`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Log rotation: enabled (100MB max)`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Metrics collection: enabled`,
          `[${new Date().toLocaleTimeString()}] INFO: System monitoring started`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Health check endpoints registered`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Performance metrics initialized`,
          `[${new Date().toLocaleTimeString()}] INFO: Step initialization complete`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Beginning main processing loop`,
        ];

        setPipelineSteps(prev => prev.map((s, index) => 
          index === i ? { 
            ...s, 
            status: 'running', 
            progress: 0, 
            startTime: new Date().toISOString(),
            logs: initialLogs
          } : s
        ));
        
        // Simulate progress with extensive logs (50+ more lines)
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 300));
          
          const progressLogs = [
            `[${new Date().toLocaleTimeString()}] INFO: Processing batch ${Math.floor(progress/20) + 1}/5`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Progress: ${progress}%`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Current throughput: ${Math.floor(Math.random() * 1000 + 500)} items/sec`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Memory usage: ${Math.floor(Math.random() * 512 + 256)}MB`,
            `[${new Date().toLocaleTimeString()}] DEBUG: CPU usage: ${Math.floor(Math.random() * 40 + 20)}%`,
            `[${new Date().toLocaleTimeString()}] INFO: Network I/O: ${Math.floor(Math.random() * 10 + 1)}MB/s`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Active threads: ${Math.floor(Math.random() * 20 + 5)}`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Queue depth: ${Math.floor(Math.random() * 100 + 10)}`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Error rate: ${(Math.random() * 0.1).toFixed(3)}%`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Cache hit rate: ${(Math.random() * 30 + 70).toFixed(1)}%`,
          ];

          if (progress === 30) {
            progressLogs.push(
              `[${new Date().toLocaleTimeString()}] INFO: Reached 30% completion milestone`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Intermediate validation checkpoint`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Data consistency check: PASSED`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Memory fragmentation: ${(Math.random() * 10 + 2).toFixed(1)}%`,
              `[${new Date().toLocaleTimeString()}] INFO: Checkpoint validation successful`,
            );
          }

          if (progress === 50) {
            progressLogs.push(
              `[${new Date().toLocaleTimeString()}] INFO: Reached halfway checkpoint`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Performing garbage collection`,
              `[${new Date().toLocaleTimeString()}] DEBUG: GC completed: ${Math.floor(Math.random() * 100 + 50)}MB freed`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Memory optimization complete`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Defragmenting data structures`,
              `[${new Date().toLocaleTimeString()}] INFO: Mid-process optimization finished`,
            );
          }

          if (progress === 80) {
            progressLogs.push(
              `[${new Date().toLocaleTimeString()}] INFO: Entering final processing phase`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Preparing output buffers`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Allocating result storage: ${Math.floor(Math.random() * 500 + 200)}MB`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Validating intermediate results`,
              `[${new Date().toLocaleTimeString()}] DEBUG: Quality assurance checks running`,
              `[${new Date().toLocaleTimeString()}] INFO: Final phase preparation complete`,
            );
          }
          
          setPipelineSteps(prev => prev.map((s, index) => 
            index === i ? { 
              ...s, 
              progress,
              logs: [...(s.logs || []), ...progressLogs]
            } : s
          ));
        }
        
        // Complete step with extensive completion logs (30+ more lines)
        const completionLogs = [
          `[${new Date().toLocaleTimeString()}] INFO: Finalizing ${step.name} processing`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Entering finalization phase`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Flushing all buffers to disk`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Buffer flush complete: ${Math.floor(Math.random() * 1000 + 500)}KB written`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Syncing file system changes`,
          `[${new Date().toLocaleTimeString()}] DEBUG: File system sync complete`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Writing output data to buffer`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Output buffer size: ${Math.floor(Math.random() * 1024 + 512)}KB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Calculating data checksums`,
          `[${new Date().toLocaleTimeString()}] DEBUG: MD5 checksum: ${Math.random().toString(16).substr(2, 32)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: SHA256 checksum: ${Math.random().toString(16).substr(2, 64)}`,
          `[${new Date().toLocaleTimeString()}] INFO: Performing comprehensive data validation`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Schema validation: PASSED`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Data integrity check: PASSED`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Business rules validation: PASSED`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Cross-reference validation: PASSED`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Validation checks passed: 15/15`,
          `[${new Date().toLocaleTimeString()}] INFO: All validation checks successful`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Generating audit trail`,
          `[${new Date().toLocaleTimeString}] DEBUG: Audit log entries: ${Math.floor(Math.random() * 50 + 25)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Compliance checks: PASSED`,
          `[${new Date().toLocaleTimeString()}] INFO: Cleaning up temporary resources`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Closing database connections: ${Math.floor(Math.random() * 5 + 2)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Releasing file handles: ${Math.floor(Math.random() * 20 + 10)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Temp files cleaned: ${Math.floor(Math.random() * 10 + 5)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Memory freed: ${Math.floor(Math.random() * 256 + 128)}MB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Cache entries invalidated: ${Math.floor(Math.random() * 100 + 50)}`,
          `[${new Date().toLocaleTimeString()}] INFO: Resource cleanup complete`,
          `[${new Date().toLocaleTimeString()}] INFO: Generating performance metrics`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Total items processed: ${Math.floor(Math.random() * 10000 + 5000)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Average processing time: ${(Math.random() * 50 + 10).toFixed(2)}ms/item`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Peak memory usage: ${Math.floor(Math.random() * 512 + 256)}MB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Total CPU time: ${(Math.random() * 60 + 30).toFixed(1)} seconds`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Total network I/O: ${(Math.random() * 100 + 50).toFixed(1)}MB`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Disk I/O operations: ${Math.floor(Math.random() * 1000 + 500)}`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Cache hit/miss ratio: ${(Math.random() * 30 + 70).toFixed(1)}%`,
          `[${new Date().toLocaleTimeString()}] INFO: Performance metrics collection complete`,
          `[${new Date().toLocaleTimeString()}] SUCCESS: ${step.name} completed successfully!`,
          `[${new Date().toLocaleTimeString()}] INFO: Execution time: ${(Math.random() * 30 + 10).toFixed(2)} seconds`,
          `[${new Date().toLocaleTimeString()}] INFO: Step output ready for next stage`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Output validation: PASSED`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Output format: JSON`,
          `[${new Date().toLocaleTimeString()}] DEBUG: Output size: ${(Math.random() * 10 + 5).toFixed(1)}MB`,
          `[${new Date().toLocaleTimeString()}] INFO: Ready for pipeline continuation`,
          `[${new Date().toLocaleTimeString()}] ======================================`,
        ];

        setPipelineSteps(prev => prev.map((s, index) => 
          index === i ? { 
            ...s, 
            status: 'completed', 
            progress: 100,
            endTime: new Date().toISOString(),
            logs: [...(s.logs || []), ...completionLogs],
            output: getMockStepOutput(s.type)
          } : s
        ));
        
        setCurrentStep(i + 1);
      }
      
      // All steps completed
      onComplete();
    };

    executeSteps();
  }, [isRunning, pipelineSteps.length, onComplete]);

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
                    : 'No logs available yet...'
                  }
                </pre>
              </div>
            )}
            
            {activeTab === "output" && (
              <div className="output-content">
                <pre className="output-text">
                  {selectedStepData.output 
                    ? JSON.stringify(selectedStepData.output, null, 2)
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