"use client";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { CreativeData } from "../types";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

const getFileType = (File_Name: string) => {
  const videoExtensions = ['.mp4', '.mov', '.gif'];
  const extension = File_Name?.split('.').pop()?.toLowerCase() || '';
  return videoExtensions.includes(`.${extension}`) ? 'video' : 'image';
};

const CreativeTable = ({ creatives }: { creatives: CreativeData[] }) => {
  if (!creatives?.length) return <div className="text-muted-foreground">No creatives available</div>;

  const attributes = [
    {label: "Preview", key: "URL", type: "image" },
    {label: "Creative ID", key: "Unique_ID", type: "text" },
    { label: "Campaign Name", key: "Campaign_Name", type: "text" },
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
    { label: "Classification", key: "Creative_classification", type: "text" },
    { label: "Landscape", key: "Landscape", type: "text" },
    { label: "Person", key: "Person", type: "text" },
    { label: "Animal", key: "Animal", type: "text" },
    { label: "Clickable Impressions", key: "Clickable_Impressions", type: "numeric" },
    { label: "Delivered Trips", key: "Delivered_Trips", type: "numeric" },
    { label: "CTR", key: "CTR", type: "numeric" },
  ];

  const getDisplayValue = (value: any) => {
    if (value == null || value === '') return '-';
    return value;
  };

  const getColumnClass = (type: string) => {
    if (type === "numeric") {
      return "min-w-[100px] max-w-[150px]";
    }
    return "min-w-[200px] max-w-[300px]";
  };

  return (
      <div className="rounded-md border flex h-full shadow-[inset_-10px_0_12px_-8px_rgba(0,0,0,0.1)]">
        <Table className="min-w-[800px] ">
          <TableHeader className="sticky top-0 bg-thbackground z-20 ">
            <TableRow>
              <TableHead className="sticky left-0 bg-thbackground z-30 min-w-[100px] max-w-[250px] truncate ">
                Preview
              </TableHead>
              {attributes.slice(1).map((attr) => (
                <TableHead
                  key={attr.label}
                  className={`${getColumnClass(attr.type)} truncate p-4 border-l`}
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
                          src={creative["URL"] as string}
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
                              src={creative.Full_File_URL as string}
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
                    className={`${getColumnClass(attr.type)} h-12 px-4 overflow-x-auto text-ellipsis border-l`}
                    title={getDisplayValue(creative[attr.key as keyof CreativeData])}
                  >
                    {attr.key === "combinedIndustryVertical" ? (
                      <p className="text-muted-foreground">
                        {creative["Industry_sectors"]} / {creative["Verticals"]}
                      </p>
                    ) : (
                      <p className="text-muted-foreground p-2 truncate">
                        {attr.key === "Creative_Video_Length"
                          ? creative[attr.key as keyof CreativeData] === 0
                            ? "N/A(Image)"
                            : getDisplayValue(creative[attr.key as keyof CreativeData])
                          : getDisplayValue(creative[attr.key as keyof CreativeData])}
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
