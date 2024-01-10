"use client";
import { useEffect, useState } from "react";
import type { SVGProps, JSX } from "react";
import { highlight, languages } from "prismjs";
import "prismjs/components/prism-yaml";
import Editor from "react-simple-code-editor";
import { Source_Code_Pro as SourceCodePro } from "next/font/google";
import type XLSX from "xlsx";
import { read } from "xlsx";
import { Tab } from "@headlessui/react";
import { getYamlContent } from "../../lib/actions";
import "prismjs/themes/prism.css";
import type { Manifest } from "../../lib/interfaces";
import type { StringOrUndefined } from "./ExcelRender";
import { ExcelWorkSheetRenderer, OutTable } from "./ExcelRender";

const sourceCodePro = SourceCodePro({ subsets: ["latin"] });

interface ReviewManifestProps {
  onSubmit: (_selectedSheet: string) => void;
  onCancel: () => void;
  sheetNames: string[];
  fileName: string;
  originalFile?: File;
}

function ReviewManifest({ onSubmit, onCancel, sheetNames, fileName, originalFile }: ReviewManifestProps): JSX.Element {
  const [loadedManifest, setLoadedManifest] = useState<Manifest | undefined>(undefined);
  const [selectedSheet, setSelectedSheet] = useState<string | undefined>(undefined);

  async function handleViewClick(sheetName: string, selected: boolean): Promise<void> {
    if (selected) {
      setLoadedManifest(undefined);
      setSelectedSheet(undefined);
    } else {
      setSelectedSheet(sheetName);
      const content = await getYamlContent({ fileName, sheetName });
      if (typeof content === "string") setLoadedManifest({ content, name: sheetName });
    }
  }

  function handleSubmit(): void {
    if (selectedSheet) onSubmit(selectedSheet);
  }

  return (
    <div className="flex flex-grow p-2 justify-center items-start gap-2 self-stretch bg-white rounded-b-xl">
      <div className="flex w-2/3 flex-col items-start flex-grow self-stretch rounded-lg border border-solid border-[#E5E5E5]">
        <div className="flex p-4 justify-between items-start self-stretch">
          <span className="font text-[#171717] text-sm font-semibold">File Viewer</span>
        </div>

        {loadedManifest && originalFile ? (
          <FileViewer manifest={loadedManifest} originalFile={originalFile} />
        ) : (
          <span className="flex flex-grow w-full items-center justify-center text-lg font-medium">
            Select a file to view
          </span>
        )}
      </div>
      <div className="flex w-1/3 flex-col items-start flex-grow self-stretch rounded-lg border border-solid border-[#E5E5E5]">
        <div className="flex p-4 flex-col items-start gap-2 self-stretch">
          <span className="text text-[#171717] font-semibold text-sm">Manifest List</span>
          <span className="text text-[#171717] opacity-75 text-sm">
            Generated manifest files from your spreadsheet, select to view and edit.
          </span>
        </div>
        <div className="flex px-2 pb-4 flex-col items-start gap-2 flex-grow self-stretch border-b border-solid border-[#E5E5E5] bg-white">
          {sheetNames.map((sheet, index) => (
            <ManifestCard
              index={index}
              key={sheet}
              onClick={handleViewClick}
              selected={loadedManifest?.name === sheet}
              sheetName={sheet}
            />
          ))}
        </div>
        <div className="flex p-2 items-start gap-2 self-stretch">
          <button
            className="flex h-12 flex-grow px-6 py-3 items-center justify-center rounded-lg border border-solid border-[#E5E5E5] text-sm font-semibold"
            onClick={onCancel}
            type="button"
          >
            Cancel
          </button>
          <div
            className={`flex h-12 flex-grow items-center justify-center rounded-lg ${
              !selectedSheet ? "bg-[#F7F6F1]" : "bg-[#F46F22]"
            }`}
          >
            <button
              className={`flex flex-grow h-12 w-full items-center justify-center px-6 py-3 ${
                !selectedSheet ? "text-[#171717]" : "text-white"
              }`}
              disabled={!selectedSheet}
              onClick={handleSubmit}
              type="button"
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReviewManifest;

function FileViewer({ manifest, originalFile }: { manifest: Manifest; originalFile: File }): JSX.Element {
  const [code, setCode] = useState(manifest.content);
  const [worksheet, setWorksheet] = useState<XLSX.WorkSheet>();
  const [tableData, setTableData] = useState<StringOrUndefined[][]>([]);
  const [tableCols, setTableCols] = useState<{ name: string; key: number }[]>([]);

  /* Fetch and update the state once */
  useEffect(() => {
    (async () => {
      const ab = await originalFile.arrayBuffer();

      /* parse */
      const wb = read(ab);
      const _sheetName = manifest.name.split(".")[0];
      if (!wb.SheetNames.includes(_sheetName))
        throw new Error("Something went wrong", { cause: "Sheet name not found" });
      const ws = wb.Sheets[_sheetName]; // get the worksheet
      setWorksheet(ws);
      const { rows: _data, cols: _cols } = ExcelWorkSheetRenderer(ws);
      setTableData(_data);
      setTableCols(_cols);
      // eslint-disable-next-line @typescript-eslint/no-confusing-void-expression, no-console -- TEMPORARY
    })().catch((e) => console.error(e));
  }, [manifest.name, originalFile]);

  return (
    <div className="flex flex-col w-[calc(66vw-33px)] h-[calc(100vh-356px)]">
      <Tab.Group>
        <Tab.List className="flex flex-row items-start self-stretch gap-2 border-b border-solid border-[#E5E5E5]">
          <Tab className="flex w-64 justify-center px-2 items-center h-12 font-semibold text-ellipsis text-[#171717] text-sm cursor-pointer opacity-50 ui-selected:opacity-100 ui-selected:border-b-2 ui-selected:border-solid ui-selected:border-[#F46F22]">
            Manifest
          </Tab>
          <Tab className="flex w-64 justify-center px-2 items-center h-12 font-semibold text-ellipsis text-[#171717] text-sm cursor-pointer opacity-50 ui-selected:opacity-100 ui-selected:border-b-2 ui-selected:border-solid ui-selected:border-[#F46F22]">
            Original File
          </Tab>
        </Tab.List>
        <Tab.Panel className={` ${sourceCodePro.className} flex flex-grow h-full max-h-full bg-[#FAFAFA]`}>
          <div className="h-[calc(100vh-376px)] w-full overflow-y-scroll">
            <Editor
              // className="h-full"
              highlight={(_code) => highlight(_code, languages.yaml, "yaml")}
              onValueChange={(_code) => {
                setCode(_code);
              }}
              padding={32}
              style={{
                // overflowY: "scroll",
                background: "#FAFAFA",
                fontSize: "14px",
                fontStyle: "normal",
                fontWeight: "500",
                opacity: "0.72",
                color: "var(--3-Black, #171717)",
              }}
              value={code}
            />
          </div>
        </Tab.Panel>
        <Tab.Panel className={` ${sourceCodePro.className} flex max-h-full`}>
          {worksheet ? (
            <OutTable
              className="max-h-full bg-[#FAFAFA] overflow-scroll"
              columns={tableCols}
              data={tableData}
              tableClassName="table-auto"
              withZeroColumn
            />
          ) : (
            "Something went wrong"
          )}
        </Tab.Panel>
      </Tab.Group>
    </div>
  );
}

interface ManifestCardProps {
  selected: boolean;
  onClick: (sheetName: string, selected: boolean) => void;
  sheetName: string;
  index: number;
}

function ManifestCard({ selected, onClick, sheetName, index }: ManifestCardProps): JSX.Element {
  function handleViewClick(): void {
    onClick(sheetName, selected);
  }

  return (
    <div
      className={`flex h-12 px-4 py-2 items-center gap-3 self-stretch rounded-lg bg-white border-solid ${
        selected ? "border-2 border-[#F46F22]" : "border border-[#E5E5E5]"
      }`}
    >
      <div className="flex items-center gap-2.5 flex-grow">
        <Clipboard />
        {sheetName}
        <span className="flex px-2 py-0.5 justify-center items-center rounded-[80px] bg-[#F46F2233] font-semibold text-xs text-[#F46F22]">
          Sheet {index + 1}
        </span>
      </div>
      <button
        className={`${selected ? "text-[#171717d2]" : "text-[#F46F22d2]"} text-sm font-semibold`}
        onClick={handleViewClick}
        type="button"
      >
        {selected ? "Close" : "View"}
      </button>
    </div>
  );
}

function Clipboard(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={25} width={24} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M14 2.77V6.9c0 .56 0 .84.109 1.054a1 1 0 0 0 .437.437c.214.11.494.11 1.054.11h4.13M16 13.5H8m8 4H8m2-8H8m6-7H8.8c-1.68 0-2.52 0-3.162.327a3 3 0 0 0-1.311 1.311C4 4.78 4 5.62 4 7.3v10.4c0 1.68 0 2.52.327 3.162a3 3 0 0 0 1.311 1.311c.642.327 1.482.327 3.162.327h6.4c1.68 0 2.52 0 3.162-.327a3 3 0 0 0 1.311-1.311C20 20.22 20 19.38 20 17.7V8.5l-6-6Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
      />
    </svg>
  );
}
