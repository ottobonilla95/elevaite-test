"use client"
import { DatasetsContextProvider } from "../../lib/contexts/DatasetsContext";
import { DatasetsHeader } from "./components/DatasetsHeader";
import { DatasetsList } from "./components/DatasetsList";
import "./page.scss";




export default function Page(): JSX.Element {
  return (
    <DatasetsContextProvider>
      <div className="datasets-main-container">
        <DatasetsHeader/>
        <DatasetsList/>
      </div>
    </DatasetsContextProvider>
  );
}
