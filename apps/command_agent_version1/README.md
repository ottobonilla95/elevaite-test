This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
# Agent Flow System

A modern, interactive agent flow builder with TypeScript and Tailwind CSS that allows users to create, configure, and deploy agent workflows.

# Agent Workflow Designer

A modular React application for designing and deploying agent-based workflows.

## Components Overview

### Main Components

- **AgentConfigForm**: The main controller component that orchestrates the entire application, managing state for designer mode and chat mode.

- **DesignerSidebar**: Left sidebar containing draggable agent components, actions, and tools. Also contains Save/Deploy buttons.

- **DesignerCanvas**: Main canvas where agent nodes can be placed and connected to form workflows.

- **ConfigureAgent**: Right panel that appears when an agent is selected, allowing configuration of parameters and tools.

- **AgentConfigModal**: Modal window for detailed agent configuration with tabs for Prompt, Parameters, and Testing.

- **ChatInterface**: Interface for interacting with deployed agent workflows in chat mode.

- **ChatSidebar**: Left sidebar for chat mode, providing options to edit workflow or create new ones.

### Agent-Related Components

- **AgentNode**: Visual representation of an agent in the flow, displaying name, type, and tools.

- **AgentPromptEditor**: Simplified editor for modifying agent prompts and basic configuration.

- **CustomEdge**: Visual representation of connections between agents, with support for different action types.

## Features

- Drag-and-drop interface for creating agent workflows
- Configuration options for each agent (model, parameters, tools)
- System message/prompt editing
- Deployment of agent workflows
- Chat interface for interacting with deployed workflows
- Save/load functionality for workflows

## State Management

The application manages several key states:
- Node configuration (type, parameters, tools, prompts)
- Workflow structure (nodes and edges)
- UI mode (designer or chat)
- Selected node for configuration

## Styling

Each component has dedicated SCSS files for styling, with shared variables for consistency.

## Backend Integration

The components are designed to interact with backend services for:
- Saving workflow configurations
- Deploying workflows
- Processing chat messages through the agent workflow

## Usage

1. Drag agents from the sidebar onto the canvas
2. Connect agents to form a workflow
3. Configure each agent as needed
4. Save your workflow
5. Deploy to start using it in chat mode
6. Interact with your workflow through the chat interface