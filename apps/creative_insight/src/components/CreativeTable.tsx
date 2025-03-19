"use client";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import Image from 'next/image';
import type { CreativeData } from "../lib/interfaces";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";

const getFileType = (fileName: string) => {
  const videoExtensions = ['.mp4', '.mov', '.gif'];
  const extension = fileName?.split('.').pop()?.toLowerCase() ?? '';
  return videoExtensions.includes(`.${extension}`) ? 'video' : 'image';
};

const CreativeTable = ({ creatives }: { creatives: CreativeData[] }) : JSX.Element => {
  if (!creatives?.length) return <div className="text-foreground">No creatives available</div>;
  console.log("Received the creative Object:",creatives);
  const attributes = [
    {label: "Preview", key: "URL", type: "image" },
    {label: "Creative ID", key: "creative_id", type: "text" },
    { label: "Campaign Name", key: "Campaign_Name", type: "text" },
    {label: "Start Date", key: "Start_Date", type: "numeric" },
    {label: "End Date", key: "End_Date", type: "numeric" },
    {label: "Scheduled Events", key: "Scheduled_Events", type: "text" },
    { label: "Delivered Trips", key: "Delivered_Trips", type: "numeric" },
    { label: "Clicks", key: "Clicks", type: "numeric" },
    { label: "CTR", key: "CTR", type: "numeric" },
    { label: "Summary", key: "creative_insight", type: "text" },
    { label: "Letters", key: "No_of_Letters", type: "numeric" },
    { label: "Words", key: "No_of_Words", type: "numeric" },
    { label: "Logo (Y/N)", key: "Brand_Logo_Present", type: "text" },
    { label: "Logo Size", key: "Brand_Logo_Size", type: "text" },
    { label: "Logo Placement", key: "Brand_Logo_Location", type: "text" },
    { label: "Industry Sector/Vertical", key: "combinedIndustryVertical", type: "text" },
    { label: "Text Colors", key: "Text_Colors_Used", type: "text" },
    { label: "Text Sizes", key: "Text_Sizes", type: "text" },
    { label: "Text Placement", key: "Text_Locations", type: "text" },
    { label: "Brand Name Present", key: "Does_Brand_Name_Appear", type: "text" },
    { label: "Product Name Present", key: "Does_Product_Name_Appear", type: "text" },
    { label: "Creative Name", key: "File_Name", type: "text" },
    { label: "Product Description Text", key: "Is_Product_Description_In_Text", type: "text" },
    { label: "Background Colors", key: "Colors_Background", type: "text" },
    { label: "Length of Ad(Video)", key: "Creative_Video_Length", type: "numeric" },
    // { label: "Classification", key: "Creative_classification", type: "text" },
    { label: "Landscape", key: "Landscape", type: "text" },
    { label: "Person", key: "Person", type: "text" },
    { label: "Animal", key: "Animal", type: "text" },
  ];


  const getDisplayValue = (value: string | number | boolean | null | undefined, key: string): string => {
    if (value === null || value === undefined) return '-';
    if (key === "CTR") {
      if (typeof value === 'number') {
        return (value * 100).toFixed(2) + '%';
      }
      return '-';
    }
    return String(value);
  };
  
  
  const getColumnClass = (type: string,key: string) => {
    if (key === "creative_insight") {
      return "min-w-[400px] max-w-[600px]  whitespace-pre-line text-left text-xs truncate text-ellipsis "; 
    }
    else if (key === "Start_Date" || key === "End_Date") {
      return "min-w-[130px] max-w-[200px] truncate";
    }
    if (type === "numeric") {
      return "min-w-[100px] max-w-[150px] truncate";
    }
    return "min-w-[200px] max-w-[300px] truncate";
  };

  return (
      <div className="rounded-md border flex h-full shadow-[inset_-10px_0_12px_-8px_rgba(0,0,0,0.1)]">
        <Table className="min-w-[800px] ">
          <TableHeader className="sticky top-0 bg-thbackground z-20 ">
            <TableRow>
              <TableHead className="sticky left-0 bg-thbackground z-30 min-w-[100px] max-w-[250px] p-4 ">
                Preview
              </TableHead>
              {attributes.slice(1).map((attr) => (
                <TableHead
                  key={attr.label}
                  className={`${getColumnClass(attr.type,attr.key)}  p-4 border-l`}
                  title={attr.label}
                >
                  {attr.label}
                  
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {creatives.map((creative) => (
              <TableRow key={creative.Unique_ID}>
                {/* Sticky Preview Column */}
                <TableCell
                  key={`URL-${creative.Unique_ID}`}
                  className="sticky left-0 bg-mainbackground z-10 min-w-[100px] max-w-[250px] h-12 px-4 overflow-x-auto text-ellipsis border-l"
                >
                  <Dialog>
                    <DialogTrigger asChild>
                      <div className="w-[180px] h-18  cursor-pointer ">
                        <img 
                          src={creative.URL as string}
                          alt="Creative Preview"
                          className="h-[20vh] p-2 object-contain hover:opacity-80 transition-opacity"
                        />
                      </div>
                    </DialogTrigger>
                    <DialogContent className="max-w-[50vw] max-h-[90vh]" aria-describedby="creative-description">
                      <DialogHeader>
                        <DialogTitle className="sr-only">Creative Preview</DialogTitle>
                      </DialogHeader>
                      <div className="flex flex-col items-center justify-center w-full h-full overflow-hidden gap-2">
                        <div className="flex-1 min-h-0 flex items-center justify-center">
                          {getFileType(creative.File_Name) === 'video' ? (
                            <video
                              controls
                              autoPlay
                              className="max-w-full max-h-[60vh] mx-auto object-contain"
                              src={creative.Full_File_URL as string}>
                                 <track kind="captions" srcLang="en" label="english_captions" />
                              </video>

                          ) : (
                            <img
                              src={creative.Full_File_URL as string}
                              alt="Full Creative Preview"
                              className="max-w-full max-h-[60vh] mx-auto object-contain"
                            />
                          )}
                        </div>
                        <div className="text-sm text-foreground text-center px-4 break-all">
                          {creative.File_Name}
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </TableCell>

                {/* Other Columns (Unique ID and all the others) */}
                {attributes.slice(1).map((attr) => (
                  <TableCell
                    key={`${attr.key}-${creative.Unique_ID}`}
                    className={`${getColumnClass(attr.type,attr.key)} overflow-clip text-ellipsis border-l`}
                    title={getDisplayValue(creative[attr.key as keyof CreativeData] as string,attr.key) as string}
                  >
                    {attr.key === "combinedIndustryVertical" ? (
                      <p className="text-foreground">
                        {creative.Industry_sectors} / {creative.Verticals}
                      </p>
                    ) : (
                    <p className="text-foreground p-2 ">
                      {attr.key === "Creative_Video_Length"
                        ? creative[attr.key as keyof CreativeData] === 0
                          ? "N/A(Image)"
                          : getDisplayValue(creative[attr.key as keyof CreativeData], attr.key)
                        : getDisplayValue(creative[attr.key as keyof CreativeData], attr.key)}
                    </p>
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
  );
};

export default CreativeTable;
