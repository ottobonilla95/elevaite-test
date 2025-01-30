import React, { useState } from 'react'

import Header from './Components/Header/Header'
import Tabs from './Components/Tabs/Tabs'

function App() {
  const [dateRange, setDateRange] = useState({ fromDate: '', toDate: '' });

  const handleDateChange = (fromDate, toDate) => {
    setDateRange({ fromDate, toDate });
  };

  return (
    <>
      <Header onDateChange={handleDateChange} /> 
      {/* //this the function that is in header */}
      <div style={{ backgroundColor: '#f1f1f1', margin: '20px' }}>
        <Tabs dateRange={dateRange} />
      </div>
    </>
  )
}

export default App