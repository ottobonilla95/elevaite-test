"use client"
import { useState } from "react";
// import { ChatbotInput } from "./components/ChatbotInput";
// import { ChatbotWindow } from "./components/ChatbotWindow";
import "./page.scss";
import Header from "./components/Header";
import Tabs from "./components/Tabs";
import { DateRange } from "./components/Summary/types";

export default function Chatbot(): JSX.Element {
  // Initialize with empty strings
  const [dateRange, setDateRange] = useState<DateRange>({
    fromDate: '',
    toDate: ''
  });

  const handleDateChange = (fromDate: string, toDate: string) => {
    setDateRange({ fromDate, toDate });
    console.log(`Date range updated: ${fromDate} to ${toDate}`);
  };

  return (
    <main className="chatbot-main-container">
      <Header onDateChange={handleDateChange} />
      <Tabs dateRange={dateRange} />
    </main>
  );
}