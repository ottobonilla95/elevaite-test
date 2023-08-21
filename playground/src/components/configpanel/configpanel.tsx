import React from "react";
import styles from "./configpanel.module.css";
import ConfigItem from "./configitem/configitem";

enum LLM {
  optionA = "Open AI",
  optionB = "Palm",
  optionC = "Llama 2",
}
enum DB {
  optionA = "Qdrant",
  optionB = "Pinecone",
  optionC = "Weaviate",
}
enum Tenant {
  optionA = "Netgear",
  optionB = "Netskope",
  optionC = "Cisco",
}

const ConfigPanel = () => {
  return (
    <div className={styles.configPanel}>
      <ConfigItem type="LLM" options={LLM} />
      <ConfigItem type="DB" options={DB} />
      <ConfigItem type="Tenant" options={Tenant} />
    </div>
  );
};

export default ConfigPanel;
