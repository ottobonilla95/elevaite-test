// MarkdownMessage.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './MarkdownMessage.scss';

const MarkdownMessage: React.FC<{ text: string; onImageClick: (url: string, alt: string, title: string) => void }> = ({ text, onImageClick }) => {
  const createRenderer = (className: string, Element: keyof JSX.IntrinsicElements = 'span') => {
    return ({ node, children, ...props }: any) => {
      return <Element className={className} {...props}>{children}</Element>;
    };
  };

  const renderers = {
    h1: createRenderer("markdown-heading-h1", 'h1'),
    h2: createRenderer("markdown-heading-h2", 'h2'),
    h3: createRenderer("markdown-heading-h3", 'h3'),
    p: createRenderer("markdown-paragraph", 'p'),
    strong: createRenderer("markdown-bold", 'strong'),
    em: createRenderer("markdown-italic", 'em'),
    ul: createRenderer("markdown-list", 'ul'),
    ol: createRenderer("markdown-list", 'ol'),
    li: createRenderer("markdown-list-item", 'li'),
    table: ({ node, children, ...props }: any) => (
      <div className="overflow-x-auto">
        <table className="markdown-table" {...props}>{children}</table>
      </div>
    ),
    thead: createRenderer("markdown-table-head", 'thead'),
    tbody: createRenderer("markdown-table-body", 'tbody'),
    tr: createRenderer("markdown-table-row", 'tr'),
    th: createRenderer("markdown-table-header", 'th'),
    td: createRenderer("markdown-table-cell", 'td'),
    img: ({ src, alt, title }: { src: string, alt: string, title: string }) => {
      const isThumbnail = src.includes('.thumbnail.jpg');
      return (
        <img
          src={src}
          alt={alt}
          title={title}
          onClick={() => onImageClick(src, alt || 'Image', title || 'No title provided')}
          style={{
            cursor: 'pointer', 
            borderRadius: '8px', 
            width: isThumbnail ? 'auto' : '300px', // Fixed size for non-thumbnail images
            height: isThumbnail ? 'auto' : '200px', // Resize non-thumbnail images
            objectFit: 'cover', // To ensure image maintains aspect ratio
          }}
        />
      );
    },
  };

  return (
    <ReactMarkdown
      children={text}
      remarkPlugins={[remarkGfm]}
      components={renderers}
    />
  );
};

export default MarkdownMessage;
