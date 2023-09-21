import * as React from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';

export default function CircularIndeterminate(props:any) {
  const[size, setSize] = React.useState(30);
  React.useEffect(()=>setSize(props?.size), [props]);
  return (
    <Box sx={{ display: 'flex'}}>
      <CircularProgress size={size}/>
    </Box>
  );
}