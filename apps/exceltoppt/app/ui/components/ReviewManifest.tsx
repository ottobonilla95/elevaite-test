"use client";
import { useEffect, useState } from "react";
import type { SVGProps, JSX } from "react";
import { highlight, languages } from "prismjs";
import "prismjs/components/prism-yaml";
import { Tab, TabList, TabPanel, Tabs } from "react-tabs";
import Editor from "react-simple-code-editor";
import { Source_Code_Pro as SourceCodePro } from "next/font/google";
import type XLSX from "xlsx";
import { read } from "xlsx";
import { getYamlContent } from "../../lib/actions";
import "prismjs/themes/prism.css";
import { ExcelWorkSheetRenderer, OutTable } from "./ExcelRender";

const sourceCodePro = SourceCodePro({ subsets: ["latin"] });

interface Manifest {
  name: string;
  content: string;
}

interface ReviewManifestProps {
  goToNextStage: () => void;
  sheetNames: string[];
  fileName: string;
  originalFile?: File;
}

function ReviewManifest({ goToNextStage, sheetNames, fileName, originalFile }: ReviewManifestProps): JSX.Element {
  const [loadedManifest, setLoadedManifest] = useState<Manifest | undefined>(undefined);

  async function handleViewClick(sheetName: string, selected: boolean): Promise<void> {
    if (selected) setLoadedManifest(undefined);
    else {
      const content = await getYamlContent({ fileName, sheetName });
      if (typeof content === "string") setLoadedManifest({ content, name: sheetName });
    }
  }

  function handleSubmit(): void {
    goToNextStage();
  }

  return (
    <div className="flex flex-grow p-2 justify-center items-start gap-2 self-stretch bg-white rounded-b-xl">
      <div className="flex w-1/2 flex-col items-start flex-grow self-stretch rounded-lg border border-solid border-[#E5E5E5]">
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
      <div className="flex w-1/2 flex-col items-start flex-grow self-stretch rounded-lg border border-solid border-[#E5E5E5]">
        <div className="flex p-4 flex-col items-start gap-2 self-stretch">
          <span className="text text-[#171717] font-semibold text-sm">Manifest List</span>
          <span className="text text-[#171717] opacity-75 text-sm">
            In euismod consequat orci, ut sollicitudin mauris ultricies nec.
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
            type="button"
          >
            Cancel
          </button>
          <div className="flex h-12 flex-grow px-6 py-3 items-center justify-center rounded-lg bg-[#F46F22]">
            <button className="text-white" onClick={handleSubmit} type="button">
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
  const [tableData, setTableData] = useState<string[][]>([]);
  const [tableCols, setTableCols] = useState<{ name: string; key: number }[]>([]);
  const tabClassNameBase =
    "flex flex-grow justify-center px-2 items-center h-12 font-semibold text-ellipsis text-[#171717] text-sm cursor-pointer";
  const tabClassName = `${tabClassNameBase} opacity-50`;
  const tabClassNameSelected = ` opacity-100 border-b-2 border-solid border-[#F46F22]`;

  /* Fetch and update the state once */
  useEffect(() => {
    (async () => {
      /* Download from https://sheetjs.com/pres.numbers */
      const ab = await originalFile.arrayBuffer();

      /* parse */
      const wb = read(ab);
      const _sheetName = manifest.name.split(".")[0];
      if (!wb.SheetNames.includes(_sheetName))
        throw new Error("Something went wrong", { cause: "Sheet name not found" });
      /* generate array of presidents from the worksheet */
      const ws = wb.Sheets[_sheetName]; // get the worksheet
      setWorksheet(ws);
      const { rows: _data, cols: _cols } = ExcelWorkSheetRenderer(ws);
      setTableData(_data);
      setTableCols(_cols);
      // eslint-disable-next-line @typescript-eslint/no-confusing-void-expression, no-console -- TEMPORARY
    })().catch((e) => console.error(e));
  }, [manifest.name, originalFile]);

  return (
    <Tabs className="flex flex-col w-[calc(50vw-28px)] h-[calc(100vh-356px)]">
      <TabList className="flex flex-row justify-evenly self-stretch gap-2">
        <Tab className={tabClassName} default selectedClassName={tabClassNameSelected}>
          Manifest
        </Tab>
        <Tab className={tabClassName} selectedClassName={tabClassNameSelected}>
          Original File
        </Tab>
      </TabList>
      <TabPanel className={` ${sourceCodePro.className} flex  max-h-full`}>
        <Editor
          highlight={(_code) => highlight(_code, languages.yaml, "yaml")}
          onValueChange={(_code) => {
            setCode(_code);
          }}
          style={{
            padding: "32px",
            overflowY: "scroll",
            width: "100%",
            background: "#FAFAFA",
            // height: "396px",
            // height: "calc(100vh - 356px)",
            maxHeight: "100%",
            fontSize: "14px",
            fontStyle: "normal",
            fontWeight: "500",
            opacity: "0.72",
            color: "var(--3-Black, #171717)",
          }}
          value={code}
        />
      </TabPanel>
      <TabPanel className={` ${sourceCodePro.className} flex max-h-full`}>
        {worksheet ? (
          <OutTable
            className=" max-h-full bg-[#FAFAFA] overflow-scroll"
            columns={tableCols}
            data={tableData}
            tableClassName="table-auto"
            withZeroColumn
          />
        ) : (
          "Something went wrong"
        )}
      </TabPanel>
    </Tabs>
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
