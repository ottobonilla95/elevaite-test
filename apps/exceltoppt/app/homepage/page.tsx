"use client";
import { useState, type JSX } from "react";
import { UploadHeader } from "../ui/components/UploadHeader";
import UploadExcel from "../ui/components/UploadExcel";
import ReviewManifest from "../ui/components/ReviewManifest";
import { Stages } from "../lib/interfaces";
import UploadTemplate from "../ui/components/UploadTemplate";

function Homepage(): JSX.Element {
  const [stage, setStage] = useState<Stages>(Stages.Upload);
  const [file, setFile] = useState<File>();
  const [filename, setFilename] = useState<string>("");
  const [sheetNames, setSheetNames] = useState<string[]>([]);

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

  function goToManifest(_filename: string, _sheetNames: string[], _file: File): void {
    setStage(Stages.Manifest);
    setFile(_file);
    setFilename(_filename);
    setSheetNames(_sheetNames);
  }
  // eslint-disable-next-line @typescript-eslint/require-await -- Might need it later
  async function goToTemplate(): Promise<void> {
    setStage(Stages.Template);
  }
  // eslint-disable-next-line @typescript-eslint/require-await -- Might need it later
  async function goToPPT(): Promise<void> {
    setStage(Stages.Review);
  }

  function reset(): void {
    setStage(Stages.Upload);
  }

  function contentSwitch(): JSX.Element {
    switch (stage) {
      case Stages.Upload:
        return (
          <>
            <CardHeader title="Upload Excel" />
            <UploadExcel onSubmit={goToManifest} />
          </>
        );
      case Stages.Manifest:
        return (
          <div className="flex flex-col w-full h-full">
            <CardHeader title="Review Manifest" />
            <ReviewManifest
              fileName={filename}
              onCancel={reset}
              onSubmit={goToTemplate}
              originalFile={file}
              sheetNames={sheetNames}
            />
          </div>
        );
      case Stages.Template:
        return (
          <>
            <CardHeader title="Upload PPTX Template" />
            <UploadTemplate onSubmit={goToPPT} />
          </>
        );
      case Stages.Review:
      default:
        return <>{null}</>;
    }
  }

  return (
    <>
      <UploadHeader currentStep={stage} steps={steps} />
      <div className="flex h-[calc(100%-136px)] w-full p-4 flex-col items-center justify-center bg-[#F7F6F1] overflow-hidden absolute bottom-0">
        <div className="flex h-full items-center flex-col gap-5 justify-center border border-solid border-[#E5E5E5] rounded-xl bg-white w-full">
          {contentSwitch()}
        </div>
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
