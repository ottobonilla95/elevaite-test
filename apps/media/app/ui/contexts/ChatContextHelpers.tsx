

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

export function tableToCsv(tableHtml: string): string {
    const parser = new DOMParser();
    const doc = parser.parseFromString(tableHtml, 'text/html');
    const rows = doc.querySelectorAll('table tr');
    
    return Array.from(rows)
      .map(row => {
        const cols = row.querySelectorAll('td, th');
        return Array.from(cols)
          .map(col => `"${col.textContent?.replace(/"/g, '""') || ''}"`)
          .join(',');
      })
      .join('\n');
  }

export function downloadCsv(csvContent: string, fileName: string): void {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', fileName);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }