import React from "react"
import styles from './pageheader.module.css';

const PageHeader = () => {
  return (
    <div className={styles.container}>
        <div className={`${styles.container} ${styles.element}`}> elevAIte | Playground </div>
      
    </div>
  )
};

export default PageHeader;
