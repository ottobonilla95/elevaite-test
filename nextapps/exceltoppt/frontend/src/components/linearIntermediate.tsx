import * as React from 'react';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';

export default function LinearIndeterminate() {
  const [showStatus, setShowStatus] = React.useState("Processing the query");
  
  return (
    <Box sx={{ width: '100%', height: '10px', p: 1 }}>
      <LinearProgress />
      <div className="progress">
        <p>{showStatus}</p>
        <div className="dot-pulse"></div>
      </div>
    </Box>
  );
}

