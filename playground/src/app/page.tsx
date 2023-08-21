import Image from "next/image";
import styles from "./page.module.css";
import ConfigPanel from "@/components/configpanel/configpanel";
import WorkArea from "@/components/workarea/workarea";

export default function Home() {
  return (
    <main className={styles.main}>
      <ConfigPanel />
      <WorkArea />
    </main>
  );
}
