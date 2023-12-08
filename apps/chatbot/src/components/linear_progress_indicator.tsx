import * as React from 'react';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';

export default function LinearIndeterminate({ agentStatus }: any) {
  const [showStatus, setShowStatus] = React.useState("Processing the query");
  React.useEffect(() => {
    if (
      agentStatus.includes("UnsupportedProduct") |
      agentStatus.includes("NotenoughContext") |
      agentStatus.includes("finalfinalFormatedOutput")
    ) {
      setShowStatus(()=>"Generating an answer")
    } else if (
      agentStatus.includes("getIssuseContexFromDetails") |
      agentStatus.includes("finalFormatedOutput") |
      agentStatus.includes("func_incidentScoringChain")
    ) {
      setShowStatus(()=>"Getting context for the issue")
    } else if (
      agentStatus.includes("getIssuseContexFromSummary") |
      agentStatus.includes("processQdrantOutput")
    ) {
      setShowStatus(()=>"Processing the context from the database")
    } else if (agentStatus.includes("getReleatedChatText")) {
      setShowStatus(()=>"Getting related chat history")
    }
  }, [agentStatus]);
  return (
    <Box sx={{ width: '100%' }}>
      <LinearProgress />
      <div className="progress">
        <p>{showStatus}</p>
        <div className="dot-pulse"></div>
      </div>
    </Box>
  );
}

