import { CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { type PDFDocumentProxy } from "pdfjs-dist";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { useResizeDetector } from "react-resize-detector";
import { useRouter } from "next/navigation";
import { useDebouncedCallback } from "@/helpers";
import { type ContractObject } from "@/interfaces";
import "./PdfDisplay.scss";


pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;


interface PdfDisplayProps {
    handleExpansion: () => void;
    isExpanded: boolean;
    file: Blob;
    contract: ContractObject;
    projectId: string;
}

export function PdfDisplay(props: PdfDisplayProps): JSX.Element {
    const [pdfData, setPdfData] = useState<string>();
    const pageContainerRef = useRef<HTMLDivElement | null>(null);
    const { width: pageContainerWidth } = useResizeDetector<HTMLDivElement>({
        targetRef: pageContainerRef,
        refreshMode: "debounce",
        refreshRate: 200
    });
    const [pdfZoom, setPdfZoom] = useState<number | undefined>();
    const pageRefs = useRef<Record<string, HTMLDivElement | null>>({});
    const [pagesAmount, setPagesAmount] = useState<number>();
    const [pageNumber, setPageNumber] = useState(1);
    const [inputNumber, setInputNumber] = useState("");
    const movePage = useRef(false);
    const router = useRouter()


    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const child = entry.target.firstChild;
                    if (child instanceof Element) {
                        const elementNumber = child.getAttribute("data-page-number");
                        if (elementNumber) {
                            // setDisplayPageNumber(elementNumber);
                            setPageNumber(parseInt(elementNumber));
                        }
                    }
                }
            });
            observer.disconnect();
        },
        { threshold: 0.5 }
    );

    // TODO: We probably don't need these useEffects
    useEffect(() => {
        if (!props.contract) {
            setPdfData(undefined);

        }
    }, [props.contract]);

    useEffect(() => {
        formatPdfData(props.file);
    }, [props.file]);


    useEffect(() => {
        if (!movePage.current) return;
        const page = pageRefs.current[pageNumber];
        if (page) {
            page.scrollIntoView({ behavior: "smooth" });
        }
        movePage.current = false;
    }, [pageNumber]);


    function formatPdfData(file: Blob): void {
        setPagesAmount(undefined);
        const reader = new FileReader();
        reader.onload = (event: ProgressEvent<FileReader>) => {
            if (event.target?.result) {
                setPdfData(event.target.result as string);
            } else setPdfData(undefined);
        };
        reader.readAsDataURL(file);
    }

    function onClose(): void {
        router.push(`/${props.projectId}/`)
    }

    function handleExpansion(): void {
        props.handleExpansion();
    }

    function handleZoom(type: "in" | "out" | "reset"): void {
        if (type === "in") {
            setPdfZoom(current =>
                current ? parseFloat((current + 0.1).toFixed(2)) : 1.1
            )
        } else if (type === "out") {
            setPdfZoom(current =>
                current ? parseFloat((current - 0.1).toFixed(2)) : 0.9
            )
        } else setPdfZoom(undefined);
    }



    function getPagesAmount(document: PDFDocumentProxy): void {
        setPagesAmount(document.numPages);
        setPageNumber(1);
    }

    function previousPage(): void { changePage(-1); }
    function nextPage(): void { changePage(1); }
    function changePage(offset: number): void {
        movePage.current = true;
        setPageNumber(prevPageNumber => prevPageNumber + offset);
    }

    function handleInputNumber(input: string): void {
        setInputNumber(input);
    }
    function handleInputBlur(): void {
        setPageByInput();
    }
    function handleKeyDown(key: string, event: KeyboardEvent<HTMLInputElement>): void {
        if (key !== "Enter") return;
        setPageByInput();
        if (event.target instanceof HTMLElement)
            event.target.blur();
    }
    function setPageByInput(): void {
        const parsedInput = parseInt(inputNumber);
        if (!pagesAmount || isNaN(parsedInput) || parsedInput < 1 || parsedInput > pagesAmount) {
            setInputNumber("");
            return;
        }
        movePage.current = true;
        setPageNumber(parsedInput);
        setInputNumber("");
    }

    const onScroll = useDebouncedCallback(() => {
        for (const pageRef of Object.values(pageRefs.current)) {
            if (!pageRef) continue;
            observer.observe(pageRef);
        }
    }, 200);

    return (
        <div className="pdf-display-container">

            <div className="pdf-display-header">
                <div className="controls-box">
                    <CommonButton onClick={onClose}>
                        <ElevaiteIcons.SVGArrowBack />
                    </CommonButton>
                    <span>Preview</span>
                </div>
                {!pdfData ? undefined :
                    <div className="controls-box">
                        <CommonButton
                            onClick={() => { handleZoom("out"); }}
                            noBackground
                            disabled={pdfZoom !== undefined && pdfZoom <= 0.1}
                            title="Zoom out"
                        >
                            <ElevaiteIcons.SVGZoom type="out" />
                        </CommonButton>
                        <CommonButton
                            className="reset"
                            onClick={() => { handleZoom("reset"); }}
                            noBackground
                            title="Reset zoom"
                        >
                            {pdfZoom ? `${(pdfZoom * 100).toFixed(0).toString()} %` : "100%"}
                        </CommonButton>
                        <CommonButton
                            onClick={() => { handleZoom("in"); }}
                            noBackground
                            disabled={pdfZoom !== undefined && pdfZoom >= 3}
                            title="Zoom in"
                        >
                            <ElevaiteIcons.SVGZoom />
                        </CommonButton>
                        <CommonButton
                            className={["expansion-arrow", props.isExpanded ? "expanded" : undefined].filter(Boolean).join(" ")}
                            onClick={handleExpansion}
                            noBackground
                            title={props.isExpanded ? "Restore views" : "Maximize pdf view"}
                        >
                            <ElevaiteIcons.SVGSideArrow />
                        </CommonButton>
                    </div>
                }
            </div>

            <div
                ref={pageContainerRef}
                className="pdf-display-scroller"
                onScroll={onScroll}
            >
                <div className="pdf-display-contents">
                    {!pdfData ? <div className="no-file">No pdf attached.</div> :
                        <Document
                            file={pdfData}
                            onLoadSuccess={getPagesAmount}
                            loading={<div className="loading large"><ElevaiteIcons.SVGSpinner /></div>}
                        >
                            {pagesAmount === undefined ? undefined : Array.from(new Array(pagesAmount),
                                (entry, index) => (
                                    <div
                                        key={`page_${(index + 1).toString()}`}
                                        ref={item => { pageRefs.current[index + 1] = item; }}
                                    >
                                        <Page
                                            pageNumber={index + 1}
                                            width={pageContainerWidth ? pageContainerWidth : 1}
                                            scale={pdfZoom}
                                            // customTextRenderer={textRenderer}
                                            loading={<div className="loading large"><ElevaiteIcons.SVGSpinner /></div>}
                                        />
                                    </div>
                                ),
                            )}
                        </Document>
                    }
                </div>
            </div>

            {!pdfData ? undefined :
                <div className="pdf-controls-container">
                    <div className="page-display">
                        <span>Page:</span>
                        <div className="page-input-container">
                            <div className="page-number">{pageNumber}</div>
                            <SimpleInput
                                value={inputNumber}
                                onChange={handleInputNumber}
                                onBlur={handleInputBlur}
                                onKeyDown={handleKeyDown}
                            />
                        </div>
                        <span>/ {pagesAmount}</span>
                    </div>


                    <div className="page-buttons">
                        <CommonButton
                            onClick={previousPage}
                            disabled={pageNumber <= 1}
                        >
                            <ElevaiteIcons.SVGChevron type="right" />
                        </CommonButton>
                        <CommonButton
                            onClick={nextPage}
                            disabled={!pagesAmount || pageNumber >= pagesAmount}
                        >
                            <ElevaiteIcons.SVGChevron type="right" />
                        </CommonButton>
                    </div>

                </div>
            }

        </div>
    );
}
