import React from "react";
import Tabs from "./components/Tabs";
import "./page.scss";

export default function AnalyticsPage() {
  return (
    <main style={{
      height: 'calc(100vh - var(--navbar-height))',
      width: '100vw',
      overflow: 'auto',
      position: 'relative',
      padding: '20px',
      paddingTop: '40px',
      backgroundColor: 'white',
      color: '#333'
    }}>
      <Tabs />
    </main>
  );
}