"use client";
import { MainAreaSwitcher2 } from "./components/advanced/MainAreaSwitcher2";
import { Sidebar } from "./components/advanced/Sidebar";
import { MainAreaSwitcher } from "./components/advanced/MainAreaSwitcher";
import { useSearchParams } from "next/navigation";
import "./page.scss";

export default function Chatbot(): JSX.Element {
  const searchParams = useSearchParams() ;
  const caseID = searchParams.get("case_number") ?? undefined;

  return (
    <main className="chatbot-advanced-container">
      <Sidebar />
        {caseID ? <MainAreaSwitcher caseID={caseID}/> : <MainAreaSwitcher2/>}
    </main>
  );
}