// MarkdownMessage.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// import rehypeRaw from 'rehype-raw';
import './MarkdownMessage.scss'

const MarkdownMessage: React.FC<{ text: string }> = ({ text }) => {
  const createRenderer = (className: string, Element: keyof JSX.IntrinsicElements = 'span') => {
    return ({ node, children, ...props }: any) => {
      return <Element className={className} {...props}>{children}</Element>;
    };
  };

  const renderers = {
    h1: createRenderer("markdown-heading", 'h1'),
    h2: createRenderer("markdown-heading", 'h2'),
    h3: createRenderer("markdown-heading", 'h3'),
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
  };

  return (
    <div className="prose inline leading-normal break-words min-w-0 [word-break:break-word]">
      <ReactMarkdown
        children={text}
        remarkPlugins={[remarkGfm]}
        // rehypePlugins={[rehypeRaw]}
        components={renderers}
      />
    </div>
  );
};

export default MarkdownMessage;