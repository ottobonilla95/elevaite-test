import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useRef, useState } from "react";
import { PdfHighlighter, type PdfHighlighterUtils, PdfLoader } from "react-pdf-highlighter-extended";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import "./PdfDisplay.scss";



const fallbackUrl = "/testPdf.pdf";




export function PdfDisplay(): JSX.Element {
    const contractsContext = useContracts();
    const highlighterUtilsRef = useRef<PdfHighlighterUtils>();
    const [pdfData, setPdfData] = useState<string | null>(null);


    useEffect(() => {
        if (!contractsContext.selectedContract) {
            setPdfData(null);
            return;
        }
        if (contractsContext.selectedContract.pdf) {
            if (typeof contractsContext.selectedContract.pdf === "string") {
                setPdfData(contractsContext.selectedContract.pdf);
                return;
            }
            const reader = new FileReader();
            reader.onload = (event: ProgressEvent<FileReader>) => {
                if (event.target?.result) {
                    setPdfData(event.target.result as string);
                } else setPdfData(fallbackUrl);
            };
            reader.readAsDataURL(contractsContext.selectedContract.pdf);
        } else setPdfData(fallbackUrl);
    }, [contractsContext.selectedContract]);



    function onClose(): void {
        contractsContext.setSelectedContract(undefined);
    }



    return (
        <div className="pdf-display-container">

            <div className="pdf-display-header">
                <CommonButton onClick={onClose}>
                    <ElevaiteIcons.SVGArrowBack/>
                </CommonButton>
                <span>Preview</span>
            </div>

            <div className="pdf-display-contents">
                {!pdfData ? 
                    <div className="loading"><ElevaiteIcons.SVGSpinner/></div>
                :
                    <PdfLoader
                        document={pdfData}
                    >
                        {(pdfDocument) => (
                            <PdfHighlighter
                                pdfDocument={pdfDocument}
                                highlights={[]}
                                utilsRef={(_pdfHighlighterUtils) => {
                                    highlighterUtilsRef.current = _pdfHighlighterUtils;
                                }}
                            >
                                <div>Test</div>
                            </PdfHighlighter>
                        )}
                    </PdfLoader>
                }
            </div>
            
        </div>
    );
}


// beforeLoad={<PdfLoading/>}
// (progress: OnProgressParameters): ReactNode