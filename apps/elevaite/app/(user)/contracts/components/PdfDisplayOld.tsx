// import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
// import { type PDFDocumentProxy } from "pdfjs-dist";
// import { type TextItem } from "pdfjs-dist/types/src/display/api";
// import { useEffect, useRef, useState } from "react";
// import { PdfHighlighter, PdfLoader, type Highlight, type PdfHighlighterUtils } from "react-pdf-highlighter-extended";
// import { useContracts } from "../../../lib/contexts/ContractsContext";
// import { type ContractObject } from "../../../lib/interfaces";
// import "./PdfDisplay.scss";



// const fallbackUrl = "/testPdf.pdf";




// export function PdfDisplay(): JSX.Element {
//     const contractsContext = useContracts();
//     const highlighterUtilsRef = useRef<PdfHighlighterUtils | null>(null);
//     const pdfDocumentRef = useRef<PDFDocumentProxy | null>(null);
//     const [pdfData, setPdfData] = useState<string | null>(null);
//     const [highlights, setHighlights] = useState<Highlight[]>([]);



//     useEffect(() => {
//         if (!contractsContext.selectedContract) {
//             setPdfData(null);
//             return;
//         }
//         formatPdfData(contractsContext.selectedContract);
//     }, [contractsContext.selectedContract]);

//     // useEffect(() => {
//     //     console.log("Current", pdfDocumentRef.current);
        
//     //     if (!pdfDocumentRef.current) return;
//     //     void searchAndHighlight("document");    
//     // }, [pdfDocumentRef.current]);

//     useEffect(() => {
//         console.log("Highlights", highlights);
//     }, [highlights]);



//     function formatPdfData(passedContract: ContractObject): void {
//         if (passedContract.pdf) {
//             if (typeof passedContract.pdf === "string") {
//                 setPdfData(passedContract.pdf);
//                 return;
//             }
//             const reader = new FileReader();
//             reader.onload = (event: ProgressEvent<FileReader>) => {
//                 if (event.target?.result) {
//                     setPdfData(event.target.result as string);
//                 } else setPdfData(fallbackUrl);
//             };
//             reader.readAsDataURL(passedContract.pdf);
//         } else setPdfData(fallbackUrl);
//     }


//     async function searchAndHighlight(searchTerm: string): Promise<void> {
//         console.log("doc?", pdfDocumentRef.current);
//         if (!pdfDocumentRef.current) return;

//         const pdf = pdfDocumentRef.current;
//         const newHighlights: Highlight[] = [];
    
//         for (let i = 0; i < pdf.numPages; i++) {
//             const page = await pdf.getPage(i + 1);
//             const textContent = await page.getTextContent();
//             const strings = textContent.items
//                 .filter((item): item is TextItem => "str" in item)
//                 .map((item: TextItem) => item.str);
//             const pageText = strings.join(" ");
    
//             // Find the matches in the page text
//             let startIndex = 0;
//             while ((startIndex = pageText.indexOf(searchTerm, startIndex)) !== -1) {
//                 const itemIndex = strings.findIndex((text) =>
//                     text.includes(searchTerm)
//                 );
    
//                 if (itemIndex !== -1) {
//                     const item = textContent.items[itemIndex] as TextItem;
//                     const transform = item.transform as number[] | undefined;

//                     if (transform && transform.length >= 6) {
//                         const x1 = transform[4];
//                         const y1 = transform[5];
//                         const x2 = x1 + (item.width || transform[0]);
//                         const y2 = y1 - 10;
        
//                         // Add the highlight information
//                         newHighlights.push({
//                             id: Math.random().toString(), // Unique ID for each highlight
//                             position: {
//                                 boundingRect: {
//                                     x1,
//                                     x2,
//                                     y1,
//                                     y2,
//                                     width: x2 - x1,
//                                     height: y1 - y2,
//                                     pageNumber: i + 1,
//                                 },
//                                 rects: [],
//                             },
//                             content: {
//                             text: searchTerm,
//                             },
//                         });
//                     }
//                 }
        
//                 startIndex += searchTerm.length;
//             }
//         }    
//         setHighlights(newHighlights);
//     };


//     function onClose(): void {
//         contractsContext.setSelectedContract(undefined);
//     }



//     return (
//         <div className="pdf-display-container">

//             <div className="pdf-display-header">
//                 <CommonButton onClick={onClose}>
//                     <ElevaiteIcons.SVGArrowBack/>
//                 </CommonButton>
//                 <span>Preview</span>
//             </div>

//             <div className="pdf-display-contents">
//                 {!pdfData ? 
//                     <div className="loading"><ElevaiteIcons.SVGSpinner/></div>
//                 :
//                     <PdfLoader
//                         document={pdfData}
//                     >
//                         {pdfDocument => {
//                             console.log("pdfdoc", pdfDocument);
//                             if (pdfDocumentRef.current !== pdfDocument) {
//                                 pdfDocumentRef.current = pdfDocument;
//                                 void searchAndHighlight("document");
//                             }
//                             return (
//                                 <PdfHighlighter
//                                     pdfDocument={pdfDocument}
//                                     highlights={highlights}
//                                     utilsRef={(_pdfHighlighterUtils) => {
//                                         highlighterUtilsRef.current = _pdfHighlighterUtils;
//                                     }}                                    
//                                 >
//                                     <div>Test</div>
//                                 </PdfHighlighter>
//                             );
//                         }}
//                     </PdfLoader>
//                 }
//             </div>
            
//         </div>
//     );
// }


// // beforeLoad={<PdfLoading/>}
// // (progress: OnProgressParameters): ReactNode