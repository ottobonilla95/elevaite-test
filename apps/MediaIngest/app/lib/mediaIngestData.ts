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
    id: "datainput",
    title: "Data Input Components",
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
    configOptions: [],
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
    id: "parsing",
    title: "Feature Extraction",
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
    configOptions: [],
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
    title: "Creative Analysis Components",
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
    configOptions: [],
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
    title: "Creative Insights Agent",
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
    configOptions: [],
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
    title: "Storage Components",
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
    configOptions: [],
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
