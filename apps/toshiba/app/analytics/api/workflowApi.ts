const API_BASE_URL = 'http://localhost:8000';

export const WorkflowAPI = {
    // Deploy a workflow (save the workflow structure)
    deployWorkflow: async (nodes, edges) => {
        // Convert nodes to agents format
        const agents = nodes.map(node => [
            node.data.type.charAt(0), // First letter as shorthand (r for router)
            node.id
        ]);

        // Convert edges to connections format
        const connections = edges.map(edge => (
            `${nodes.find(n => n.id === edge.source)?.data.type.charAt(0)}->${nodes.find(n => n.id === edge.target)?.data.type.charAt(0)
            }`
        ));

        // Create the payload
        const payload = {
            'agents': agents,
            'connections': connections
        };

        console.log("Sending deploy payload:", payload);

        const response = await fetch(`${API_BASE_URL}/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Failed to deploy workflow');
        }

        return response.json();
    },

    // Run a query through the workflow
    runWorkflow: async (routerId, query) => {
        const payload = {
            router_id: routerId,
            query: query
        };

        console.log("Sending run payload:", payload);

        const response = await fetch(`${API_BASE_URL}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Failed to process query');
        }

        return response.json();
    }
};