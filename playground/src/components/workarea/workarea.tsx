"use client"; //this needs to be refactored
import React, { useState } from "react";
import styles from "./workarea.module.css";
import WorkAreaElement from "./workarea-element/workarea-element";

export type chunkType = {
  id: string;
  reference: string;
  score: number;
  text: string;
};
const WorkArea = (props: any) => {
  const [answer, setAnswer] = useState("");
  const [query, setQuery] = useState("");
  const [chunks, setChunks] = useState<chunkType[]>([]);
  return (
    <div className={styles.workareaContainer}>
      <div className={styles.workareaSubContainer}>
        <WorkAreaElement
          type="prompt"
          value={props.prompt}
          setValue={props.setPrompt}
          rows={10}
        />
        <WorkAreaElement
          type="query"
          data={{
            prompt: props.prompt,
            llm: props.llm,
            db: props.db,
            tenant: props.tenant,
            query: query,
          }}
          value={query}
          setValue={setQuery}
          answer={answer}
          setAnswer={setAnswer}
          chunks={chunks}
          setChunks={setChunks}
          rows={5}
        />
      </div>
      <div className={styles.workareaSubContainer}>
        <WorkAreaElement
          type="answer"
          answer={answer}
          setAnswer={setAnswer}
          chunks={chunks}
          setChunks={setChunks}
          rows={5}
        />
      </div>
    </div>
  );
};

export default WorkArea;
