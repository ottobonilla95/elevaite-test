

export function getLoadingMessageFromAgentStatus(agentStatus: string): string {
    if (
        agentStatus.includes("UnsupportedProduct") ||
        agentStatus.includes("NotenoughContext") ||
        agentStatus.includes("finalfinalFormatedOutput")
    ) {
        return "Generating an answer";

    } else if (
        agentStatus.includes("getIssuseContexFromDetails") ||
        agentStatus.includes("finalFormatedOutput") ||
        agentStatus.includes("func_incidentScoringChain")
    ) {
        return "Getting context for the issue";

    } else if (
        agentStatus.includes("getIssuseContexFromSummary") ||
        agentStatus.includes("processQdrantOutput")
    ) {
        return "Processing the context from the database";

    } else if (agentStatus.includes("getReleatedChatText")) {
        return "Getting related chat history";
    }
    
    return "";
}



