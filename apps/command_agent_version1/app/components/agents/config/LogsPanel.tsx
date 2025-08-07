"use client";

import React, { useState } from "react";
import { LogsTabs } from "./LogsTabs";
import { ProgressBar } from "./ProgressBar";
import { type VectorizationStepType } from "../VectorizerBottomDrawer";
import "./LogsPanel.scss";

interface LogsPanelProps {
  stepType: VectorizationStepType;
  isRunning: boolean;
  progress: number;
}

// Mock log data for different step types
const getMockLogs = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return `[2024-01-15 10:15:22] INFO: Starting data loading process
[2024-01-15 10:15:22] INFO: Connecting to data source provider: s3
[2024-01-15 10:15:23] INFO: Loading files from bucket: my-vectorizer-bucket
[2024-01-15 10:15:23] INFO: Found 10/100 files matching pattern: *.pdf
[2024-01-15 10:15:24] INFO: Processing file: document_1.pdf (2.3MB)
[2024-01-15 10:15:25] INFO: Processing file: document_2.pdf (1.8MB)
[2024-01-15 10:15:26] INFO: Processing file: document_3.pdf (3.1MB)
[2024-01-15 10:15:27] INFO: Successfully loaded 3 files
[2024-01-15 10:15:27] INFO: Total data size: 7.2MB
[2024-01-15 10:15:27] SUCCESS: Data loading completed successfully`;

    case "parse":
      return `[2024-01-15 10:15:28] INFO: Starting document parsing
[2024-01-15 10:15:28] INFO: Using provider: unstructured.io
[2024-01-15 10:15:29] INFO: Parsing strategy: auto
[2024-01-15 10:15:29] INFO: Processing document_1.pdf
[2024-01-15 10:15:31] INFO: Extracted 127 text elements
[2024-01-15 10:15:31] INFO: Processing document_2.pdf
[2024-01-15 10:15:33] INFO: Extracted 98 text elements
[2024-01-15 10:15:33] INFO: Processing document_3.pdf
[2024-01-15 10:15:36] INFO: Extracted 203 text elements
[2024-01-15 10:15:36] INFO: Total elements extracted: 428
[2024-01-15 10:15:36] SUCCESS: Document parsing completed successfully`;

    case "chunk":
      return `[2024-01-15 10:15:37] INFO: Starting text chunking process
[2024-01-15 10:15:37] INFO: Using strategy: recursive character text splitter
[2024-01-15 10:15:37] INFO: Chunk size: 1000 characters
[2024-01-15 10:15:37] INFO: Chunk overlap: 200 characters
[2024-01-15 10:15:38] INFO: Processing 428 text elements
[2024-01-15 10:15:39] INFO: Created 156 chunks from element batch 1-100
[2024-01-15 10:15:40] INFO: Created 178 chunks from element batch 101-200
[2024-01-15 10:15:41] INFO: Created 142 chunks from element batch 201-300
[2024-01-15 10:15:42] INFO: Created 98 chunks from element batch 301-428
[2024-01-15 10:15:42] INFO: Total chunks created: 574
[2024-01-15 10:15:42] SUCCESS: Text chunking completed successfully`;

    case "embed":
      return `[2024-01-15 10:15:43] INFO: Starting embedding generation
[2024-01-15 10:15:43] INFO: Using provider: openai
[2024-01-15 10:15:43] INFO: Model: text-embedding-3-small
[2024-01-15 10:15:43] INFO: Batch size: 100 chunks
[2024-01-15 10:15:44] INFO: Processing batch 1/6 (chunks 1-100)
[2024-01-15 10:15:47] INFO: Generated 100 embeddings (1536 dimensions)
[2024-01-15 10:15:47] INFO: Processing batch 2/6 (chunks 101-200)
[2024-01-15 10:15:50] INFO: Generated 100 embeddings (1536 dimensions)
[2024-01-15 10:15:50] INFO: Processing batch 3/6 (chunks 201-300)
[2024-01-15 10:15:53] INFO: Generated 100 embeddings (1536 dimensions)
[2024-01-15 10:15:53] INFO: Processing batch 4/6 (chunks 301-400)
[2024-01-15 10:15:56] INFO: Generated 100 embeddings (1536 dimensions)
[2024-01-15 10:15:56] INFO: Processing batch 5/6 (chunks 401-500)
[2024-01-15 10:15:59] INFO: Generated 100 embeddings (1536 dimensions)
[2024-01-15 10:15:59] INFO: Processing batch 6/6 (chunks 501-574)
[2024-01-15 10:16:02] INFO: Generated 74 embeddings (1536 dimensions)
[2024-01-15 10:16:02] INFO: Total embeddings: 574
[2024-01-15 10:16:02] SUCCESS: Embedding generation completed successfully`;

    case "store":
      return `[2024-01-15 10:16:03] INFO: Starting vector storage process
[2024-01-15 10:16:03] INFO: Using provider: pinecone
[2024-01-15 10:16:03] INFO: Index name: vectorizer-index
[2024-01-15 10:16:04] INFO: Connecting to Pinecone index
[2024-01-15 10:16:05] INFO: Index connection established
[2024-01-15 10:16:05] INFO: Upserting vectors batch 1/6 (vectors 1-100)
[2024-01-15 10:16:07] INFO: Upserted 100 vectors successfully
[2024-01-15 10:16:07] INFO: Upserting vectors batch 2/6 (vectors 101-200)
[2024-01-15 10:16:09] INFO: Upserted 100 vectors successfully
[2024-01-15 10:16:09] INFO: Upserting vectors batch 3/6 (vectors 201-300)
[2024-01-15 10:16:11] INFO: Upserted 100 vectors successfully
[2024-01-15 10:16:11] INFO: Upserting vectors batch 4/6 (vectors 301-400)
[2024-01-15 10:16:13] INFO: Upserted 100 vectors successfully
[2024-01-15 10:16:13] INFO: Upserting vectors batch 5/6 (vectors 401-500)
[2024-01-15 10:16:15] INFO: Upserted 100 vectors successfully
[2024-01-15 10:16:15] INFO: Upserting vectors batch 6/6 (vectors 501-574)
[2024-01-15 10:16:17] INFO: Upserted 74 vectors successfully
[2024-01-15 10:16:17] INFO: Total vectors stored: 574
[2024-01-15 10:16:17] SUCCESS: Vector storage completed successfully`;

    case "query":
      return `[2024-01-15 10:16:18] INFO: Starting query processing
[2024-01-15 10:16:18] INFO: Query strategy: similarity search
[2024-01-15 10:16:18] INFO: Top K results: 5
[2024-01-15 10:16:18] INFO: Processing query: "What is machine learning?"
[2024-01-15 10:16:19] INFO: Generated query embedding (1536 dimensions)
[2024-01-15 10:16:19] INFO: Searching vector index for similar documents
[2024-01-15 10:16:20] INFO: Found 574 candidate vectors
[2024-01-15 10:16:20] INFO: Retrieved top 5 most similar results
[2024-01-15 10:16:20] INFO: Score threshold applied: 0.0
[2024-01-15 10:16:20] INFO: Similarity scores: [0.89, 0.87, 0.85, 0.83, 0.81]
[2024-01-15 10:16:20] SUCCESS: Query processing completed successfully`;

    default:
      return `[2024-01-15 10:16:21] INFO: Starting ${stepType} processing
[2024-01-15 10:16:21] INFO: Configuration loaded successfully
[2024-01-15 10:16:22] INFO: Processing data...
[2024-01-15 10:16:23] INFO: Step execution in progress
[2024-01-15 10:16:24] SUCCESS: ${stepType} processing completed successfully`;
  }
};

// Mock JSON output data for different step types
const getMockOutput = (stepType: VectorizationStepType): object => {
  switch (stepType) {
    case "load":
      return {
        "status": "completed",
        "files_processed": 3,
        "total_size_mb": 7.2,
        "files": [
          {
            "name": "document_1.pdf",
            "size_mb": 2.3,
            "status": "loaded"
          },
          {
            "name": "document_2.pdf", 
            "size_mb": 1.8,
            "status": "loaded"
          },
          {
            "name": "document_3.pdf",
            "size_mb": 3.1,
            "status": "loaded"
          }
        ],
        "execution_time_seconds": 5.2,
        "timestamp": "2024-01-15T10:15:27Z"
      };

    case "parse":
      return {
        "status": "completed",
        "documents_processed": 3,
        "total_elements": 428,
        "elements_by_type": {
          "text": 324,
          "title": 18,
          "table": 12,
          "list": 74
        },
        "extraction_stats": {
          "avg_elements_per_doc": 142.7,
          "total_text_length": 45621,
          "avg_text_length_per_element": 106.6
        },
        "execution_time_seconds": 8.1,
        "timestamp": "2024-01-15T10:15:36Z"
      };

    case "chunk":
      return {
        "status": "completed",
        "input_elements": 428,
        "output_chunks": 574,
        "chunking_stats": {
          "avg_chunk_size": 876,
          "max_chunk_size": 1000,
          "min_chunk_size": 245,
          "overlap_characters": 200
        },
        "chunk_distribution": {
          "small_chunks_(<500_chars)": 89,
          "medium_chunks_(500-800_chars)": 198,
          "large_chunks_(>800_chars)": 287
        },
        "execution_time_seconds": 4.8,
        "timestamp": "2024-01-15T10:15:42Z"
      };

    case "embed":
      return {
        "status": "completed",
        "chunks_processed": 574,
        "embeddings_generated": 574,
        "embedding_stats": {
          "model": "text-embedding-3-small",
          "dimensions": 1536,
          "total_tokens": 98743,
          "avg_tokens_per_chunk": 172.1
        },
        "batching_info": {
          "batch_size": 100,
          "total_batches": 6,
          "last_batch_size": 74
        },
        "cost_estimation": {
          "total_tokens": 98743,
          "estimated_cost_usd": 0.0099
        },
        "execution_time_seconds": 19.2,
        "timestamp": "2024-01-15T10:16:02Z"
      };

    case "store":
      return {
        "status": "completed",
        "vectors_stored": 574,
        "index_info": {
          "provider": "pinecone",
          "index_name": "vectorizer-index",
          "namespace": "default",
          "dimension": 1536
        },
        "storage_stats": {
          "total_batches": 6,
          "batch_size": 100,
          "last_batch_size": 74,
          "upsert_success_rate": 100.0
        },
        "index_stats": {
          "total_vectors_in_index": 574,
          "index_fullness": 0.001,
          "approximate_size_mb": 8.7
        },
        "execution_time_seconds": 14.3,
        "timestamp": "2024-01-15T10:16:17Z"
      };

    case "query":
      return {
        "status": "completed",
        "query": "What is machine learning?",
        "results_found": 5,
        "search_stats": {
          "total_vectors_searched": 574,
          "search_time_ms": 142,
          "score_threshold": 0.0
        },
        "results": [
          {
            "id": "chunk_127",
            "score": 0.89,
            "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed...",
            "metadata": {
              "source": "document_1.pdf",
              "page": 3,
              "chunk_index": 127
            }
          },
          {
            "id": "chunk_89", 
            "score": 0.87,
            "text": "Supervised learning algorithms use labeled training data to learn patterns and make predictions on new, unseen data...",
            "metadata": {
              "source": "document_2.pdf",
              "page": 2,
              "chunk_index": 89
            }
          },
          {
            "id": "chunk_203",
            "score": 0.85,
            "text": "Deep learning is a specialized branch of machine learning that uses neural networks with multiple layers...",
            "metadata": {
              "source": "document_3.pdf",
              "page": 1,
              "chunk_index": 203
            }
          }
        ],
        "execution_time_seconds": 2.1,
        "timestamp": "2024-01-15T10:16:20Z"
      };

    default:
      return {
        "status": "completed",
        "step_type": stepType,
        "message": `${stepType} processing completed successfully`,
        "execution_time_seconds": 3.5,
        "timestamp": new Date().toISOString()
      };
  }
};

export function LogsPanel({ stepType, isRunning, progress }: LogsPanelProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<"logs" | "output">("logs");

  const logs = getMockLogs(stepType);
  const output = getMockOutput(stepType);

  return (
    <div className="logs-panel">
      {/* Progress Bar */}
      {isRunning && (
        <div className="progress-section">
          <ProgressBar
            progress={progress}
            isRunning={isRunning}
            label={`${Math.round(progress)}% files processed`}
            icon="📁"
          />
        </div>
      )}

      {/* Tabs */}
      <LogsTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === "logs" && (
          <div className="logs-content">
            <pre className="logs-text">{logs}</pre>
          </div>
        )}
        
        {activeTab === "output" && (
          <div className="output-content">
            <pre className="output-text">
              {JSON.stringify(output, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}