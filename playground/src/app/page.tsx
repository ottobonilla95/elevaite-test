"use client";
import Image from "next/image";
import styles from "./page.module.css";
import ConfigPanel from "@/components/configpanel/configpanel";
import WorkArea from "@/components/workarea/workarea";
import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [llm, setLLM] = useState("");
  const [db, setDB] = useState("");
  const [tenant, setTenant] = useState("");

  function setConfigValues(new_prompt:string, new_llm:string, new_db:string, new_tenant:string){
    setPrompt(()=>new_prompt);
    setLLM(()=> new_llm);
    setDB(()=>new_db);
    setTenant(()=> new_tenant);
  }
  return (
    <main className={styles.main}>
      <ConfigPanel setConfigValues={setConfigValues} />
      <WorkArea
        prompt={prompt}
        setPrompt={setPrompt}
        answer={answer}
        setAnswer={setAnswer}
        llm={llm}
        setLLM={setLLM}
        db={db}
        setDB={setDB}
        tenant={tenant}
        setTenant={setTenant}
      />
    </main>
  );
}
