"use client"
import { ModelsContextProvider } from "../../lib/contexts/ModelsContext";
import { ModelsList } from "./components/ModelsList";
import { ModelsHeader } from "./components/ModelsHeader";
import "./page.scss";




export default function Page():JSX.Element {


  return (
    <ModelsContextProvider>
      <div className="models-main-container">
        <ModelsHeader/>
        <ModelsList/>
      </div>
    </ModelsContextProvider>
  );
}
