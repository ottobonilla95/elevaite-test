export interface ConfigOption {
  id: string;
  label: string;
  type: "select" | "text" | "number" | "checkbox" | "radio";
  options?: string[];
  default?: string | number | boolean;
  description?: string;
}

export interface MediaIngestStep {
  id: string;
  title: string;
  description: string;
  details: string;
  features: string[];
  examples: {
    input: string;
    output: string;
  }[];
  configOptions: ConfigOption[];
  providers: {
    [key: string]: {
      supported: boolean;
      description?: string;
    };
  };
}

export const mediaIngestSteps: MediaIngestStep[] = [
  {
    id: "loading",
    title: "Loading",
    description: "Load documents from various sources",
    details:
      "The loading step involves fetching documents from different sources such as S3 buckets, local file systems, or URLs. This step prepares the documents for the parsing stage.",
    features: [
      "Support for multiple data sources (S3, local files, URLs, etc.)",
      "Handling of various file formats",
      "Batch loading capabilities",
      "Error handling and retry mechanisms",
      "Progress tracking and reporting",
    ],
    examples: [
      {
        input: "S3 bucket containing PDF, DOCX, and TXT files",
        output: "Loaded documents ready for parsing",
      },
      {
        input: "Local directory with mixed document types",
        output: "Organized file list with metadata",
      },
    ],
    configOptions: [
      {
        id: "source_type",
        label: "Source Type",
        type: "select",
        options: ["s3", "local", "url"],
        default: "s3",
        description: "Select the source type for loading documents",
      },
      {
        id: "bucket_name",
        label: "S3 Bucket Name",
        type: "text",
        default: "kb-check-pdf",
        description: "Name of the S3 bucket containing documents",
      },
      {
        id: "local_directory",
        label: "Local Directory",
        type: "text",
        default: "/INPUT",
        description: "Path to local directory containing documents",
      },
    ],
    providers: {
      sagemaker: {
        supported: true,
        description: "Fully supported with S3 integration",
      },
      airflow: {
        supported: true,
        description: "Excellent for scheduled loading from multiple sources",
      },
      bedrock: {
        supported: true,
        description: "Native support for AWS data sources",
      },
    },
  },
  {
    id: "parsing",
    title: "Parsing",
    description: "Extract text and metadata from various document formats",
    details:
      "The parsing step involves extracting raw text and metadata from documents in various formats such as PDF, DOCX, HTML, etc. This step prepares the content for further processing.",
    features: [
      "Support for multiple document formats (PDF, DOCX, TXT, HTML, etc.)",
      "Extraction of document metadata (title, author, creation date, etc.)",
      "Preservation of document structure (headings, paragraphs, lists, etc.)",
      "Handling of embedded images and tables",
      "OCR for scanned documents",
    ],
    examples: [
      {
        input: "PDF document with text, images, and tables",
        output: "Extracted plain text with metadata and structural information",
      },
      {
        input: "Scanned document with handwritten notes",
        output: "OCR-processed text with confidence scores",
      },
    ],
    configOptions: [
      {
        id: "parsing_mode",
        label: "Parsing Mode",
        type: "select",
        options: ["auto_parser", "custom_parser"],
        default: "auto_parser",
        description:
          "Choose between automatic parser selection or custom parser",
      },
      {
        id: "file_type",
        label: "File Type",
        type: "select",
        options: ["pdf", "docx", "txt", "html", "url"],
        default: "pdf",
        description: "Select the type of document to parse",
      },
      {
        id: "ocr_enabled",
        label: "Enable OCR",
        type: "checkbox",
        default: true,
        description:
          "Enable Optical Character Recognition for scanned documents",
      },
    ],
    providers: {
      sagemaker: {
        supported: true,
        description: "Fully supported with all parsing options",
      },
      airflow: {
        supported: true,
        description: "Supported with limited OCR capabilities",
      },
      bedrock: {
        supported: true,
        description: "Native support for all document types",
      },
    },
  },
  {
    id: "chunking",
    title: "Chunking",
    description: "Split documents into smaller, manageable pieces",
    details:
      "Chunking divides the extracted text into smaller segments based on semantic meaning, fixed size, or natural breaks like paragraphs. This makes the content more manageable for processing and retrieval.",
    features: [
      "Multiple chunking strategies (fixed size, semantic, sliding window)",
      "Preservation of context across chunks",
      "Handling of document structure during chunking",
      "Customizable chunk size and overlap",
      "Intelligent chunk boundary detection",
    ],
    examples: [
      {
        input: "Long document with multiple sections",
        output: "Series of semantically coherent chunks",
      },
      {
        input: "Technical document with code blocks",
        output: "Chunks that preserve code block integrity",
      },
    ],
    configOptions: [
      {
        id: "chunking_strategy",
        label: "Chunking Strategy",
        type: "select",
        options: [
          "semantic_chunking",
          "recursive_chunking",
          "sentence_chunking",
          "mdstructure",
        ],
        default: "semantic_chunking",
        description: "Select the strategy for dividing documents into chunks",
      },
      {
        id: "chunk_size",
        label: "Chunk Size",
        type: "number",
        default: 500,
        description:
          "Target size of chunks in tokens (for fixed-size strategies)",
      },
      {
        id: "chunk_overlap",
        label: "Chunk Overlap",
        type: "number",
        default: 50,
        description: "Number of tokens to overlap between chunks",
      },
      {
        id: "breakpoint_threshold_type",
        label: "Breakpoint Threshold Type",
        type: "select",
        options: ["percentile", "absolute"],
        default: "percentile",
        description:
          "Method for determining chunk boundaries in semantic chunking",
      },
    ],
    providers: {
      sagemaker: {
        supported: true,
        description: "Supports all chunking strategies",
      },
      airflow: {
        supported: true,
        description: "Best performance with semantic chunking",
      },
      bedrock: {
        supported: true,
        description: "Native support for all chunking strategies",
      },
    },
  },
  {
    id: "embedding",
    title: "Embedding",
    description: "Convert text chunks into vector representations",
    details:
      "The embedding step transforms text chunks into numerical vector representations using machine learning models. These vectors capture the semantic meaning of the text, enabling similarity searches and other operations.",
    features: [
      "Support for various embedding models (OpenAI, Hugging Face, etc.)",
      "Customizable embedding dimensions",
      "Batch processing for efficiency",
      "Handling of multilingual content",
      "Specialized embeddings for different content types",
    ],
    examples: [
      {
        input: "Text chunk: 'The quick brown fox jumps over the lazy dog'",
        output: "Vector: [0.021, -0.036, 0.058, ..., 0.073]",
      },
      {
        input: "Technical term with specific meaning in context",
        output: "Context-aware vector representation",
      },
    ],
    configOptions: [
      {
        id: "embedding_model",
        label: "Embedding Model",
        type: "select",
        options: ["openai", "huggingface", "cohere", "custom"],
        default: "openai",
        description: "Select the model to use for generating embeddings",
      },
      {
        id: "embedding_dimensions",
        label: "Embedding Dimensions",
        type: "select",
        options: ["768", "1024", "1536", "3072"],
        default: "1536",
        description: "Number of dimensions in the embedding vectors",
      },
      {
        id: "batch_size",
        label: "Batch Size",
        type: "number",
        default: 32,
        description: "Number of chunks to process in a single batch",
      },
    ],
    providers: {
      sagemaker: {
        supported: true,
        description: "Supports all embedding models with GPU acceleration",
      },
      airflow: {
        supported: true,
        description: "Best for batch processing of large document sets",
      },
      bedrock: {
        supported: true,
        description: "Native integration with AWS embedding models",
      },
    },
  },
  {
    id: "vectorstore",
    title: "Vector Store",
    description: "Store and index vectors for efficient retrieval",
    details:
      "The Vector Store step involves storing the generated embeddings in a specialized database optimized for vector similarity search. This enables efficient retrieval of relevant information based on semantic similarity.",
    features: [
      "Vector database integration (Pinecone, Qdrant, etc.)",
      "Efficient indexing algorithms (HNSW, IVF, etc.)",
      "Metadata filtering capabilities",
      "Scalable to millions of vectors",
      "Real-time index updates",
    ],
    examples: [
      {
        input: "Collection of vector embeddings",
        output: "Indexed vector database ready for querying",
      },
      {
        input: "New document to be added to existing index",
        output: "Updated index with new vectors and metadata",
      },
    ],
    configOptions: [
      {
        id: "vector_db",
        label: "Vector Database",
        type: "select",
        options: ["pinecone", "qdrant", "weaviate", "milvus", "faiss"],
        default: "pinecone",
        description: "Select the vector database for storing embeddings",
      },
      {
        id: "index_algorithm",
        label: "Indexing Algorithm",
        type: "select",
        options: ["hnsw", "ivf", "flat"],
        default: "hnsw",
        description: "Algorithm used for vector indexing",
      },
      {
        id: "distance_metric",
        label: "Distance Metric",
        type: "select",
        options: ["cosine", "euclidean", "dot_product"],
        default: "cosine",
        description: "Metric used to measure similarity between vectors",
      },
      {
        id: "index_name",
        label: "Index Name",
        type: "text",
        default: "default-index",
        description: "Name of the vector index",
      },
    ],
    providers: {
      sagemaker: {
        supported: true,
        description: "Supports all vector databases with AWS integration",
      },
      airflow: {
        supported: true,
        description: "Best for scheduled index updates and maintenance",
      },
      bedrock: {
        supported: true,
        description: "Native integration with AWS vector databases",
      },
    },
  },
];
