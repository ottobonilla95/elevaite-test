"use client";
import React, { use, useState } from "react";
import styles from "./workarea-element.module.css";
import axios from "axios";
import { chunkType } from "../workarea";
import CircularIndeterminate from "../../progress-spinner/progress_spinner";

const WorkAreaElement = (props: any) => {
  const [isLoading, setIsLoading] = useState(false);
  function handleChange(e: any) {
    props.setValue(() => e.target.value);
  }
  async function getAnswer() {
    setIsLoading(() => true);
    axios
      .post(
        process.env.NEXT_PUBLIC_BACKEND_URL + "playground/query",
        props.data
      )
      .then((data: any) => {
        console.log(data);
        props.setAnswer(() => data.data["answer"]);
        let newChunks: chunkType[] = [];
        data.data["chunks"].forEach((data: chunkType) => {
          console.log(
            "Here is the chunk data",
            data.id,
            data.text,
            data.reference,
            data.score
          );
          newChunks.push({
            id: data.id,
            text: data.text,
            reference: data.reference,
            score: data.score,
          });
        });
        props.setChunks(() => newChunks);
        setIsLoading(() => false);
      });
  }
  return props.type !== "answer" ? (
    <div className={styles.workareaElement}>
      <label htmlFor="prompt">{props.type}</label>
      <textarea
        className={styles.workareaTextField}
        name="prompt"
        id="prompt"
        rows={props.rows}
        value={props.value}
        onChange={handleChange}
      ></textarea>
      {props.type === "query" ? (
        <button
          disabled={isLoading}
          className={styles.workareaButton}
          onClick={getAnswer}
        >
          {isLoading ? <CircularIndeterminate size={30} /> : <>Run</>}
        </button>
      ) : null}
    </div>
  ) : (
    <>
      <div className={styles.workareaElement}>
        <label htmlFor="answer">{props.type}</label>
        <textarea
          name="answer"
          id="answer"
          className={styles.workareaTextField}
          readOnly={true}
          rows={props.rows}
          value={props.answer}
        ></textarea>
      </div>
      <div className={styles.workareaChunkContainer}>
        {props.chunks.map((chunk: chunkType) => (
          <>
            <div className={styles.workeareaChunk}>
              <div className={styles.workareaChunkElement}>
                <label htmlFor="answer">ID:</label>
                <p>{chunk.id}</p>
              </div>
              <div className={styles.workareaChunkElement}>
                <label htmlFor="answer">Ref:</label>
                <p>{chunk.reference}</p>
              </div>
              <div className={styles.workareaChunkElement}>
                <label htmlFor="answer">Score:</label>
                <p>{chunk.score}</p>
              </div>
              <div className={styles.workareaChunkElement}>
                <label htmlFor="answer">Text:</label>
                <textarea
                  name="answer"
                  id="answer"
                  className={styles.workareaTextField}
                  readOnly={true}
                  rows={5}
                  value={chunk.text}
                ></textarea>
              </div>
            </div>
          </>
        ))}
      </div>
    </>
  );
};

export default WorkAreaElement;
