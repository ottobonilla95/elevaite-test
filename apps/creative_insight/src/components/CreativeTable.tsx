"use client";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CreativeData } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

const getFileType = (File_Name: string) => {
  const videoExtensions = ['.mp4', '.mov', '.gif'];
  const extension = File_Name?.split('.').pop()?.toLowerCase() || '';
  return videoExtensions.includes(`.${extension}`) ? 'video' : 'image';
};

const CreativeTable = ({ creatives }: { creatives: CreativeData[] }) => {
  if (!creatives?.length) return <div className="text-muted-foreground">No creatives available</div>;

  const attributes = [
    {label: "Preview", key: "URL" },
    {label: "Creative ID", key: "Unique_ID" },
    { label: "Campaign Name", key: "Campaign_Name" },
    { label: "Letters", key: "No_of_Letters" },
    { label: "Words", key: "No_of_Words" },
    { label: "Logo (Y/N)", key: "Brand_Logo_Present" },
    { label: "Logo Size", key: "Brand_Logo_Size" },
    { label: "Logo Placement", key: "Brand_Logo_Location" },
    { label: "Industry Sector/Vertical", key: "combinedIndustryVertical" },
    { label: "Text Colors", key: "Text_Colors_Used" },
    { label: "Text Sizes", key: "Text_Sizes" },
    { label: "Text Placement", key: "Text_Locations" },
    { label: "Brand Name Present", key: "Does_Brand_Name_Appear" },
    { label: "Product Name Present", key: "Does_Product_Name_Appear" },
    { label: "Creative Name", key: "File_Name"},
    { label: "Product Description Text", key: "Is_Product_Description_In_Text" },
    { label: "Background Colors", key: "Colors_Background" },
    { label: "Length of Ad(Video)", key: "Creative_Video_Length" },
    { label: "Classification", key: "Creative_classification" },
    { label: "Clickable Impressions", key: "Clickable_Impressions" },
    { label: "Delivered Trips", key: "Delivered_Trips" },
    { label: "CTR", key: "CTR" },
  ];

  const getDisplayValue = (value: any) => {
    if (value == null || value === '') return '-';
    return value;
  };
  
  return (
    <div className="rounded-md border h-[800px]">
      <div className="flex overflow-x-auto h-full ">
        <Table className="min-w-[800px]">
          <TableHeader className="sticky top-0 bg-background z-20 ">
            <TableRow>
            <TableHead className="sticky left-0 bg-background z-30 min-w-[100px] max-w-[250px] truncate ">
              Preview
            </TableHead>
              {attributes.slice(1).map((attr) => (
                <TableHead key={attr.label} className="min-w-[150px] max-w-[400px] truncate p-8">
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
          className="sticky left-0 bg-background z-10 min-w-[100px] max-w-[250px] h-12 px-4 overflow-x-auto truncate border-l"
        >
          <Dialog>
            <DialogTrigger asChild>
              <div className="w-[180px] h-18 bg-muted/50 cursor-pointer">
                <img
                  src={creative["URL"] as string}
                  alt="Creative Preview"
                  className="h-[20vh] items-center  p-0.5 hover:opacity-80 transition-opacity"
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
                      src={creative.Full_File_URL as string}
                      type="video/mp4"
                    />
                  ) : (
                    <img
                      src={creative.Full_File_URL as string}
                      alt="Full Creative Preview"
                      className="max-w-full max-h-[60vh] mx-auto object-contain"
                    />
                  )}
                </div>
                <div className="text-sm text-muted-foreground text-center px-4 break-all">
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
            className="min-w-[100px] max-w-[150px] h-12 px-4 overflow-x-auto truncate border-l"
          >
            {attr.key === "combinedIndustryVertical" ? (
              <p className="text-muted-foreground">
                {creative["Industry_sectors"]} / {creative["Verticals"]}
              </p>
            ) : (
              <p className="text-muted-foreground p-2">
                {attr.key === "Creative_Video_Length"
                  ? creative[attr.key as keyof CreativeData] === 0
                    ? "N/A(Image)"
                    : getDisplayValue(creative[attr.key as keyof CreativeData])
                  : getDisplayValue(creative[attr.key as keyof CreativeData])}
              </p>
            )}
          </TableCell>
        ))}

        {/* Right-most Sticky Column */}
        {/* <TableCell
          key={`${attributes[attributes.length - 1].key}-${creative.Unique_ID}`}
          className="sticky right-0 bg-background z-10 min-w-[50px]  max-w-[100px] h-12 px-4"
        >
          {getDisplayValue(creative[attributes[attributes.length - 1].key as keyof CreativeData])}
        </TableCell> */}
      </TableRow>
    ))}
  </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default CreativeTable;
