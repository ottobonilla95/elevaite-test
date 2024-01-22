"use client";
import { useState, type JSX } from "react";
import { Loading } from "@repo/ui/components";
import { UploadHeader } from "../ui/components/UploadHeader";
import UploadExcel from "../ui/components/UploadExcel";
import ReviewManifest from "../ui/components/ReviewManifest";
import type { GenPPTResponse, UploadedFile } from "../lib/interfaces";
import { Stages } from "../lib/interfaces";
// import UploadTemplate from "../ui/components/UploadTemplate";
import PreviewPowerPoint from "../ui/components/PreviewPowerPoint";
import { generateManifest, generatePPT } from "../lib/actions";

function Homepage(): JSX.Element {
  const [stage, setStage] = useState<Stages>(Stages.Upload);
  const [file, setFile] = useState<File>();
  const [filename, setFilename] = useState<string>("");
  const [sheetNames, setSheetNames] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>();
  const [summary, setSummary] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const steps = [
    { label: "Upload Excel", link: "/homepage", stage: Stages.Upload, key: "upload" },
    {
      label: "Review Manifest List",
      link: "/homepage/manifest",
      stage: Stages.Manifest,
      key: "manifest",
    },
    {
      label: "Choose/Upload PPT Template",
      link: "/homepage/upload",
      stage: Stages.Template,
      key: "template",
    },
    { label: "View PPT", link: "/homepage/review", stage: Stages.Review, key: "review" },
  ];

  async function goToManifest(_serverFiles: UploadedFile[], _files: File[]): Promise<void> {
    try {
      //TODO: This is a temporary bodge as the server currently handles single files.
      const selectedFile = _serverFiles[0];
      setIsLoading(true);
      const data = await generateManifest({
        fileName: selectedFile.name.split(".")[0],
        filePath: selectedFile.name,
      });
      const _sheetNames = Array.isArray(data.sheet_names) ? data.sheet_names : [data.sheet_names];
      setIsLoading(false);
      setFile(_files[0]);
      setFilename(selectedFile.name.split(".")[0]);
      setSheetNames(_sheetNames);
      setStage(Stages.Manifest);
    } catch (error) {
      setIsLoading(false);
      // eslint-disable-next-line no-console -- Implement better logging
      console.error("Error generating manifest:", error);
    }
  }
  // eslint-disable-next-line @typescript-eslint/require-await, @typescript-eslint/no-unused-vars, no-unused-vars -- Might need it later
  async function goToTemplate(): Promise<void> {
    setStage(Stages.Template);
  }
  async function goToPPT(_selectedSheet: string): Promise<void> {
    setIsLoading(true);
    //This will be changed when we can select or upload a template
    setSelectedSheet(_selectedSheet);
    let res: GenPPTResponse;
    try {
      res = await generatePPT(filename, _selectedSheet);
    } catch (error) {
      throw new Error("Something went wrong", { cause: error });
    }
    if ("error" in res) throw new Error("Something went wrong", { cause: res.error });
    setLocation(res.export_url);
    setSummary(res.summary);
    setStage(Stages.Review);
    setIsLoading(false);
  }

  function reset(): void {
    setStage(Stages.Upload);
  }

  function contentSwitch(): JSX.Element {
    switch (stage) {
      case Stages.Upload:
        return (
          <div className="flex h-full items-center flex-col gap-5 justify-center border border-solid border-[#E5E5E5] rounded-xl bg-white w-full">
            <CardHeader title="Upload Excel" />
            <UploadExcel onSubmit={goToManifest} />
          </div>
        );
      case Stages.Manifest:
        return (
          <div className="flex h-full items-center flex-col gap-5 justify-center border border-solid border-[#E5E5E5] rounded-xl bg-white w-full">
            <CardHeader title="Review Manifest" />
            <ReviewManifest
              fileName={filename}
              onCancel={reset}
              onSubmit={goToPPT}
              originalFile={file}
              sheetNames={sheetNames}
            />
          </div>
        );
      case Stages.Template:
        return (
          <div className="flex h-full items-center flex-col gap-5 justify-center border border-solid border-[#E5E5E5] rounded-xl bg-white w-full">
            <CardHeader title="Upload PPTX Template" />
            {/* <UploadTemplate onSubmit={goToPPT} /> */}
          </div>
        );
      case Stages.Review:
        return (
          <PreviewPowerPoint location={location} sheetName={selectedSheet} summary={summary} workbookName={filename} />
        );
      default:
        return <>{null}</>;
    }
  }

  return (
    <>
      <UploadHeader currentStep={stage} steps={steps} />
      <div className="flex h-[calc(100%-136px)] w-full p-4 flex-col items-center justify-center bg-[#F7F6F1] overflow-hidden absolute bottom-0">
        {isLoading ? <Loading /> : contentSwitch()}
      </div>
    </>
  );
}

export default Homepage;

function CardHeader({ title }: { title: string }): JSX.Element {
  return (
    <span className="flex py-5 px-6 items-start self-stretch border-b border-solid border-[#E5E5E5] bg-[#D9F27E] font-semibold rounded-t-xl">
      {title}
    </span>
  );
}
