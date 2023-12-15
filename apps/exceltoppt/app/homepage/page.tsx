"use client";
import { uploadToServer } from "@/app/lib/actions";
import UploadWidget from "../ui/components/UploadWidget";
import { SVGProps, useRef, useState } from "react";
import { useRouter } from "next/navigation";

interface UploadedFile {
  name: string;
  sheetCount: string;
  fileSize: string;
  key: string;
}

function Homepage() {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [manifest, setManifest] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleCanclebutton = () => {
    setFiles([]);
  };

  const handleFileSelect = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    setIsLoading(true);
    if (file) {
      const formData = new FormData();
      formData.append("file", file, encodeURIComponent(file.name));
      try {
        const data = await uploadToServer(formData);
        if (data) {
          files.push({ fileSize: data.file_size, key: data.id, name: data.file_name, sheetCount: data.sheet_count });
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Error uploading file:", error);
      }
    }
  };

  const handleSubmitbutton = async () => {
    try {
      console.log("Generating Manifest..");
      setManifest(true);
      //TODO: This is a temporary bodge as the server currently handles single files.
      const selectedFile = files[0];
      const url = new URL("http://localhost:8000/generateManifest/");
      url.searchParams.append("file_name", encodeURIComponent(selectedFile.name?.split(".")[0]));
      url.searchParams.append("file_path", "data/Excel/" + encodeURIComponent(selectedFile.name));
      url.searchParams.append("save_dir", "data/Manifest");
      const response = await fetch(url.toString(), { method: "GET" });

      if (response.ok) {
        console.log("Manifest Generated..");
        const data = await response.json();
        const sheetNames = Array.isArray(data.sheet_names) ? data.sheet_names : [data.sheet_names];
        console.log(typeof sheetNames);
        setManifest(false);
        router.push("/reviewManifest", {
          query: {
            fileName: selectedFile.name?.split(".")[0],
            sheetNames: sheetNames,
          },
        });
      }
    } catch (error) {
      setIsLoading(false);
      console.error("Error generating manifest:", error);
    }
  };

  return (
    <>
      <div className="flex p-4 flex-col items-center gap-5 justify-center">
        <span className="flex py-5 px-6 items-start self-stretch border-b border-solid border-[#E5E5E5] bg-[#D9F27E] font-semibold">
          Excel Upload
        </span>
        <div className="flex flex-col w-3/5 h-full gap-5 pt-12 justify-center">
          <UploadWidget handleFileSelect={handleFileSelect} />
          <div className="rest h-[calc(100vh/2)] overflow-auto flex flex-col gap-3">
            <div className="cards w-full flex flex-col gap-3">
              {files.map((file) => (
                <FileCard file={file} onXClose={(key) => setFiles(files.filter((file) => file.key !== key))} />
              ))}
            </div>
            <div className="buttons flex flex-row justify-end w-full items-end gap-3">
              <button
                className="cancel flex justify-center items-center py-2.5 px-4 rounded-lg border border-solid border-[#D0D5DD] bg-white shadow-sm font-semibold text-sm"
                onClick={handleCanclebutton}
              >
                Cancel
              </button>
              <button
                className="submit flex justify-center items-center py-2.5 px-4 rounded-lg border border-solid border-[#F46F22] bg-[#F46F22] shadow-sm font-semibold text-sm text-white"
                onClick={handleSubmitbutton}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default Homepage;

interface FileCardProps {
  file: UploadedFile;
  onXClose: (key: string) => void;
}

function FileCard({ file, onXClose }: FileCardProps) {
  return (
    <div className="flex flex-col w-full p-3 gap-3 justify-center items-start rounded-lg bg-[#F8FAFB]">
      <div className="flex flex-col gap-2 self-stretch">
        <div className="flex flex-1 items-center gap-2">
          <XLSXIcon className="w w-6 h-6" />
          <span className="flex-grow text-sm font-medium">{file.name}</span>
          <XClose className="close cursor-pointer" onClick={() => onXClose(file.key)} />
        </div>
        <line className="w-full h-px bg-[#ECEFF3]" />
        <div className="flex justify-between items-center self-stretch">
          <span className="text-[#666D80] font-medium text-xs">
            {file.sheetCount}
            {" Sheets Found"}
          </span>
          <span className="text-[#121212] font-medium text-xs">
            <span className="text-[#666D80] font-medium text-xs">{"Size: "}</span>
            {file.fileSize}
          </span>
        </div>
      </div>
    </div>
  );
}

const XLSXIcon = (props: SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={32} height={32} fill="none" {...props}>
    <path
      fill="#185C37"
      d="M19.581 15.35 8.512 13.4v14.409a1.192 1.192 0 0 0 1.193 1.19h19.1A1.192 1.192 0 0 0 30 27.81v-5.31l-10.419-7.15Z"
    />
    <path
      fill="#21A366"
      d="M19.581 3H9.705a1.192 1.192 0 0 0-1.193 1.191V9.5l11.07 6.5 5.86 1.95L30 16V9.5L19.581 3Z"
    />
    <path fill="#107C41" d="M8.512 9.5h11.07V16H8.511V9.5Z" />
    <path
      fill="#000"
      d="M16.434 8.2H8.512v16.25h7.922a1.2 1.2 0 0 0 1.194-1.19V9.39a1.2 1.2 0 0 0-1.194-1.19Z"
      opacity={0.1}
    />
    <path
      fill="#000"
      d="M15.783 8.85h-7.27V25.1h7.27a1.2 1.2 0 0 0 1.194-1.19V10.04a1.2 1.2 0 0 0-1.194-1.19Z"
      opacity={0.2}
    />
    <path
      fill="#000"
      d="M15.783 8.85h-7.27V23.8h7.27a1.2 1.2 0 0 0 1.194-1.19V10.04a1.2 1.2 0 0 0-1.194-1.19Z"
      opacity={0.2}
    />
    <path
      fill="#000"
      d="M15.132 8.85h-6.62V23.8h6.62a1.2 1.2 0 0 0 1.194-1.19V10.04a1.2 1.2 0 0 0-1.194-1.19Z"
      opacity={0.2}
    />
    <path
      fill="url(#a)"
      d="M3.194 8.85h11.938a1.193 1.193 0 0 1 1.194 1.191V21.96a1.193 1.193 0 0 1-1.194 1.191H3.194A1.19 1.19 0 0 1 2 21.96V10.04a1.192 1.192 0 0 1 1.194-1.19Z"
    />
    <path
      fill="#fff"
      d="m5.7 19.873 2.511-3.884-2.3-3.862h1.847L9.013 14.6c.116.234.2.408.238.524h.017c.082-.188.17-.369.26-.546l1.342-2.447h1.7l-2.359 3.84 2.42 3.905h-1.81l-1.45-2.711a2.357 2.357 0 0 1-.17-.365h-.025c-.042.123-.098.24-.168.351l-1.493 2.722H5.7Z"
    />
    <path fill="#33C481" d="M28.806 3h-9.225v6.5h10.42V4.191A1.193 1.193 0 0 0 28.805 3Z" />
    <path fill="#107C41" d="M19.581 16h10.42v6.5H19.58V16Z" />
    <defs>
      <linearGradient id="a" x1={4.494} x2={13.832} y1={7.914} y2={24.086} gradientUnits="userSpaceOnUse">
        <stop stopColor="#18884F" />
        <stop offset={0.5} stopColor="#117E43" />
        <stop offset={1} stopColor="#0B6631" />
      </linearGradient>
    </defs>
  </svg>
);

const XClose = (props: SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={16} height={16} fill="none" {...props}>
    <path stroke="#666D80" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.333} d="m12 4-8 8m0-8 8 8" />
  </svg>
);
