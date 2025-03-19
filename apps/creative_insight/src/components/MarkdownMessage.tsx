// MarkdownMessage.tsx
import React, { ComponentProps,ComponentPropsWithRef, ElementType, ReactNode, HTMLAttributes } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { CreateRendererProps, MarkdownMessageProps , CodeProps, ElementRefMap} from '../lib/interfaces';

// Get the ref type for a given element
type RefTypeFor<T extends keyof ElementRefMap | string> = T extends keyof ElementRefMap 
  ? ElementRefMap[T] 
  : HTMLElement;

// Generic createRenderer function with correct typings
const createRenderer = <T extends keyof JSX.IntrinsicElements = 'span'>({
  className,
  Element = 'span' as T,
}: CreateRendererProps & { Element?: T }) => {
  const RendererComponent = React.forwardRef<RefTypeFor<T>, ComponentPropsWithRef<T>>((props, ref) => {
    const { children, ...rest } = props;
    return React.createElement(
      Element,
      { ref, className, ...rest },
      children
    );
  });
  // Set the displayName based on the Element type
  RendererComponent.displayName = `Markdown${String(Element).charAt(0).toUpperCase() + String(Element).slice(1)}`;
  return RendererComponent;
};


// Individual renderers with specific element types
const H1Renderer = createRenderer<'h1'>({ className: "text-3xl font-bold my-4", Element: 'h1' });
const H2Renderer = createRenderer<'h2'>({ className: "text-2xl font-bold my-3", Element: 'h2' });
const H3Renderer = createRenderer<'h3'>({ className: "text-xl font-bold text-foreground my-2", Element: 'h3' });
const PRenderer = createRenderer<'p'>({ className: "my-2 text-foreground", Element: 'p' });
const StrongRenderer = createRenderer<'strong'>({ className: "font-bold", Element: 'strong' });
const EmRenderer = createRenderer<'em'>({ className: "italic", Element: 'em' });
const UlRenderer = createRenderer<'ul'>({ className: "list-disc pl-5 my-2", Element: 'ul' });
const OlRenderer = createRenderer<'ol'>({ className: "list-decimal pl-5 my-2", Element: 'ol' });
const LiRenderer = createRenderer<'li'>({ className: "ml-2 my-1", Element: 'li' });

const TableRenderer = React.forwardRef<HTMLTableElement, ComponentProps<'table'>>((props, ref) => {
  const { children, ...rest } = props;
  return (
    <div className="overflow-x-auto my-4 rounded-lg shadow">
      <table ref={ref} className="w-full text-left border-collapse bg-white" {...rest}>
        {children}
      </table>
    </div>
  );
});
TableRenderer.displayName = 'MarkdownTable';

const TheadRenderer = createRenderer<'thead'>({ className: "bg-thbackground border-b", Element: 'thead' });
const TbodyRenderer = createRenderer<'tbody'>({ className: "bg-mainbackground divide-y divide-text-foreground", Element: 'tbody' });
const TrRenderer = createRenderer<'tr'>({ className: "hover:bg-muted/50", Element: 'tr' });
const ThRenderer = createRenderer<'th'>({ className: "px-6 py-3 text-sm font-medium text-foreground uppercase tracking-wider", Element: 'th' });
const TdRenderer = createRenderer<'td'>({ className: "px-6 py-4 text-sm text-foreground", Element: 'td' });

// Define CodeRenderer separately with specific typing

const CodeRenderer = React.forwardRef<HTMLElement, CodeProps>((props, ref) => {
  const { inline, className, children, ...rest } = props;
  return inline ? (
    <code ref={ref} className="px-1 py-0.5 rounded bg-gray-100 text-gray-800 font-mono text-sm" {...rest}>
      {children}
    </code>
  ) : (
    <pre className="p-4 rounded-lg bg-gray-800 text-white overflow-x-auto my-4 font-mono text-sm">
      <code ref={ref} className={className ?? ""} {...rest}>
        {children}
      </code>
    </pre>
  );
});
CodeRenderer.displayName = 'MarkdownCode';

const BlockquoteRenderer = createRenderer<'blockquote'>({
  className: "pl-4 border-l-4 border-gray-300 italic my-4",
  Element: 'blockquote'
});

// Explicitly typed renderers object using Components from react-markdown
const renderers: Components = {
  h1: H1Renderer,
  h2: H2Renderer,
  h3: H3Renderer,
  p: PRenderer,
  strong: StrongRenderer,
  em: EmRenderer,
  ul: UlRenderer,
  ol: OlRenderer,
  li: LiRenderer,
  table: TableRenderer,
  thead: TheadRenderer,
  tbody: TbodyRenderer,
  tr: TrRenderer,
  th: ThRenderer,
  td: TdRenderer,
  code: CodeRenderer,
  blockquote: BlockquoteRenderer,
};

const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ text }) => {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={renderers}>
      {text}
    </ReactMarkdown>
  );
};

export default MarkdownMessage;
