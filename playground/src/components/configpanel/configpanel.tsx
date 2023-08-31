"use client";
import React, { useState } from "react";
import styles from "./configpanel.module.css";
import ConfigItem from "./configitem/configitem";
import axios from "axios";



const ConfigPanel = (props: any) => {
  const LLM = ["Open AI", "Palm", "Llama 2"];
  const DB = ["Qdrant","Pinecone", "Weaviate"];
  const Tenant = ["Cisco", "Netskope", "Netgear", "PAN"];
  const [llm, setLLM] = useState(LLM[0]);
  const [db, setDB] = useState(DB[0]);
  const [tenant, setTenant] = useState(Tenant[0]);


  async function getPrompt() {
    axios.get(
      process.env.NEXT_PUBLIC_BACKEND_URL +
        "playground/prompt?llm=" +
        llm +
        "&db=" +
        db +
        "&tenant=" +
        tenant
    ).then((data:any)=>{
      props.setConfigValues(data.data["prompt"], llm, db, tenant);
    })
  }
  return (
    <div className={styles.configPanel}>
      <ConfigItem
        type="LLM"
        options={LLM}
        setValue={setLLM}
        value ={llm}
      />
      <ConfigItem
        type="DB"
        options={DB}
        setValue={setDB}
        value ={db}
      />
      <ConfigItem
        type="Tenant"
        options={Tenant}
        setValue={setTenant}
        value={tenant}
      />
      <button className={styles.workareaButton} onClick={getPrompt}>
        Get Prompt
      </button>
    </div>
  );
};

export default ConfigPanel;
