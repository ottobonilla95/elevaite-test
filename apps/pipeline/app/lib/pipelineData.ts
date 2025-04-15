export interface PipelineStep {
  id: string;
  title: string;
  description: string;
  details: string;
  features: string[];
  examples: {
    input: string;
    output: string;
  }[];
}

export const pipelineSteps: PipelineStep[] = [
  {
    id: "parsing",
    title: "Parsing",
    description: "Extract text and metadata from various document formats",
    details: "The parsing step involves extracting raw text and metadata from documents in various formats such as PDF, DOCX, HTML, etc. This step prepares the content for further processing.",
    features: [
      "Support for multiple document formats (PDF, DOCX, TXT, HTML, etc.)",
      "Extraction of document metadata (title, author, creation date, etc.)",
      "Preservation of document structure (headings, paragraphs, lists, etc.)",
      "Handling of embedded images and tables",
      "OCR for scanned documents"
    ],
    examples: [
      {
        input: "PDF document with text, images, and tables",
        output: "Extracted plain text with metadata and structural information"
      },
      {
        input: "Scanned document with handwritten notes",
        output: "OCR-processed text with confidence scores"
      }
    ]
  },
  {
    id: "chunking",
    title: "Chunking",
    description: "Split documents into smaller, manageable pieces",
    details: "Chunking divides the extracted text into smaller segments based on semantic meaning, fixed size, or natural breaks like paragraphs. This makes the content more manageable for processing and retrieval.",
    features: [
      "Multiple chunking strategies (fixed size, semantic, sliding window)",
      "Preservation of context across chunks",
      "Handling of document structure during chunking",
      "Customizable chunk size and overlap",
      "Intelligent chunk boundary detection"
    ],
    examples: [
      {
        input: "Long document with multiple sections",
        output: "Series of semantically coherent chunks"
      },
      {
        input: "Technical document with code blocks",
        output: "Chunks that preserve code block integrity"
      }
    ]
  },
  {
    id: "embedding",
    title: "Embedding",
    description: "Convert text chunks into vector representations",
    details: "The embedding step transforms text chunks into numerical vector representations using machine learning models. These vectors capture the semantic meaning of the text, enabling similarity searches and other operations.",
    features: [
      "Support for various embedding models (OpenAI, Hugging Face, etc.)",
      "Customizable embedding dimensions",
      "Batch processing for efficiency",
      "Handling of multilingual content",
      "Specialized embeddings for different content types"
    ],
    examples: [
      {
        input: "Text chunk: 'The quick brown fox jumps over the lazy dog'",
        output: "Vector: [0.021, -0.036, 0.058, ..., 0.073]"
      },
      {
        input: "Technical term with specific meaning in context",
        output: "Context-aware vector representation"
      }
    ]
  },
  {
    id: "indexing",
    title: "Indexing",
    description: "Organize vectors for efficient retrieval",
    details: "Indexing organizes the vector embeddings in a way that enables efficient storage and retrieval. This step often involves creating specialized data structures that support fast similarity searches.",
    features: [
      "Vector database integration (Pinecone, Qdrant, etc.)",
      "Efficient indexing algorithms (HNSW, IVF, etc.)",
      "Metadata filtering capabilities",
      "Scalable to millions of vectors",
      "Real-time index updates"
    ],
    examples: [
      {
        input: "Collection of vector embeddings",
        output: "Indexed vector database ready for querying"
      },
      {
        input: "New document to be added to existing index",
        output: "Updated index with new vectors and metadata"
      }
    ]
  },
  {
    id: "retrieval",
    title: "Retrieval",
    description: "Find and return the most relevant information",
    details: "The retrieval step involves searching the indexed vectors to find the most relevant information based on a query. This step returns the most semantically similar content to the user's request.",
    features: [
      "Semantic search capabilities",
      "Hybrid search (combining semantic and keyword search)",
      "Relevance scoring and ranking",
      "Metadata filtering during retrieval",
      "Customizable retrieval parameters (k, similarity threshold, etc.)"
    ],
    examples: [
      {
        input: "Query: 'How does photosynthesis work?'",
        output: "Ranked list of most relevant document chunks about photosynthesis"
      },
      {
        input: "Query with metadata filters (date range, document type)",
        output: "Filtered results matching both semantic relevance and metadata criteria"
      }
    ]
  }
];
