import React from "react";
import styles from "./workarea.module.css";
const WorkArea = (props: any) => {
  return (
    <div className={styles.workareaContainer}>
      <div className={styles.workareaElement}>
        <label htmlFor="prompt">Sys Prompt</label>
        <textarea name="prompt" id="prompt" cols={100} rows={10}></textarea>
      </div>
    </div>
  );
};

export default WorkArea;
