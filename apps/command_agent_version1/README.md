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

## Key Features

- **Drag and Drop Interface**: Create agent flows by dragging agents from the sidebar onto the canvas
- **Interactive Connections**: Connect agents with animated flow lines
- **UUID Implementation**: All workflows and agents have UUIDs for reliable tracking
- **Agent Configuration**: Configure specific options for each agent type
- **Deploy Functionality**: Deploy workflows and test them in a chat interface
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **TypeScript Support**: Full TypeScript integration for better code reliability

## Components

1. **AgentConfigForm**: Main component that orchestrates the workflow builder and chat interface
2. **FlowCanvas**: Component that handles the React Flow canvas for the agent workflow
3. **AgentNode**: Component that defines the visual representation of agent nodes
4. **Flow Types**: Type definitions for nodes, edges, and workflows

## Agent Types

- **Router Agent**: Entry point for all queries (ID: 1)
- **Web Search Agent**: Searches the web for information (ID: 2)
- **API Agent**: Connects to external APIs (ID: 3)
- **Data Agent**: Processes and analyzes data (ID: 4)
- **Troubleshooting Agent**: Helps solve technical problems (ID: 5)

## Workflow Structure

Each workflow has:
- A unique workflow ID (UUID)
- A name
- A collection of agents (each with its own UUID)
- A set of connections between agents

## Data Flow

The system:
1. Allows creating a workflow with a unique ID
2. Enables adding agents to a canvas, each with a UUID
3. Facilitates connections between agents
4. Supports deploying the workflow to a chat interface
5. Processes queries through the workflow
6. Returns responses based on the agent flow

## UUID Implementation

The system uses UUIDs to ensure:
- No ID collisions even with millions of workflows
- Each component is uniquely identifiable
- Workflows can be moved between environments
- Complete path history can be recorded with UUID references

## Dependencies

- React
- React Flow
- UUID
- Lucide React (for icons)
- Tailwind CSS

## File Structure

```
/components
  /AgentConfigForm.tsx  # Main workflow builder component
  /FlowCanvas.tsx       # React Flow canvas component
  /AgentNode.tsx        # Node component for agents
/types
  /flow.ts              # Type definitions for the flow system
/styles
  /flow.css             # Styling for flow components
```

## Usage

1. Drag agents from the sidebar to the canvas
2. Connect agents by dragging from one handle to another
3. Configure each agent's properties
4. Name your workflow
5. Save or deploy your workflow
6. If deployed, use the chat interface to test your agent flow

## JSON Workflow Format

```json
{
  "workflowId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "workflowName": "My Agent Workflow",
  "agents": [
    {
      "id": "1",
      "uuid": "a1b2c3d4-...",
      "type": "router",
      "name": "Router Agent"
    },
    {
      "id": "2",
      "uuid": "e5f6g7h8-...",
      "type": "web_search",
      "name": "Web Search Agent"
    }
  ],
  "connections": [
    {
      "fromUuid": "a1b2c3d4-...",
      "toUuid": "e5f6g7h8-..."
    }
  ]
}
```