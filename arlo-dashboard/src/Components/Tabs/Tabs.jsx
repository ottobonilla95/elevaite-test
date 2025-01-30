import React, { useState } from 'react';
import { Box, Tab, Tabs, Typography } from '@mui/material';

import Agents from './TabsComponents/Agents/Agents'
import Problems from './TabsComponents/Problems/Problems';
import Products from './TabsComponents/Products/Products'
import RootCause from './TabsComponents/RootCause/RootCause'
import Summary from './TabsComponents/Summary/Summary'

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
      style={{ padding: '0px 12px 0px 12px', height: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: 1, backgroundColor: 'white', height: '100%' }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function TabComponent({ dateRange }) {

  const [value, setValue] = useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  const tabDetails = [
    { label: 'Summary', component: <Summary dateRange={dateRange} /> },
    { label: 'Problems', component: <Problems dateRange={dateRange} /> },
    { label: 'Root Cause', component: <RootCause dateRange={dateRange} /> },
    { label: 'Products', component: <Products dateRange={dateRange} /> },
    { label: 'Agents', component: <Agents dateRange={dateRange} /> },
  ];

  return (
    <div style={{ backgroundColor: '#ccc', height: '100%' }}>
      <Box sx={{ width: '100%', height: '100%' }}>
        <Box sx={{ padding: 1, paddingBottom: 0, paddingTop: 2 }}>
          <Tabs value={value} onChange={handleChange} aria-label="user details tabs" textColor="inherit" indicatorColor="primary">
            {tabDetails.map((tab, index) => (
              <Tab
                key={tab.label}
                label={tab.label}
                sx={{
                  backgroundColor: value === index ? 'white' : '#1B4965',
                  color: value === index ? '#1B4965' : 'white',
                  margin: '0 5px',
                  borderRadius: 1,
                  borderBottomLeftRadius: 0,
                  borderBottomRightRadius: 0,
                  fontSize: '12px',
                  paddingTop: '0px',
                  paddingBottom: '0',
                }}
              />
            ))}
          </Tabs>
        </Box>
        {tabDetails.map((tab, index) => (
          <TabPanel key={tab.label} value={value} index={index}>
            {tab.component}
          </TabPanel>
        ))}
      </Box>
    </div>
  )
}

export default TabComponent