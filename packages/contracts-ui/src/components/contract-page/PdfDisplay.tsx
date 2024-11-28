import { CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useRouter } from "next/navigation";
import { type PDFDocumentProxy } from "pdfjs-dist";
import { type KeyboardEvent, type MutableRefObject, useEffect, useRef, useState, } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { useResizeDetector } from "react-resize-detector";
import { useDebouncedCallback } from "../../helpers";
import { type ContractObject, type ContractProjectObject } from "../../interfaces";
import "./PdfDisplay.scss";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;




const useIntersectionObserver = (
  callback: IntersectionObserverCallback,
  options?: IntersectionObserverInit
): MutableRefObject<IntersectionObserver | null> => {
  const observer = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "IntersectionObserver" in window) {
      observer.current = new IntersectionObserver(callback, options);
    }
    return () => {
      if (observer.current) {
        observer.current.disconnect();
        observer.current = null;
      }
    };
  }, [callback, options]);

  return observer;
};

interface PdfDisplayProps {
  handleExpansion: () => void;
  isExpanded: boolean;
  projectId: string;
  contract?: ContractObject;
  project?: ContractProjectObject;
  file?: Blob;
}

export function PdfDisplay(props: PdfDisplayProps): JSX.Element {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [pdfReference, setPdfReference] = useState<string | File | Blob | null>(null);
  const [pdfData, setPdfData] = useState<string>();
  const pageContainerRef = useRef<HTMLDivElement | null>(null);
  const { width: pageContainerWidth } = useResizeDetector<HTMLDivElement>({ targetRef: pageContainerRef, refreshMode: "debounce", refreshRate: 200, });
  const [pdfZoom, setPdfZoom] = useState<number | undefined>();
  const pageRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [pagesAmount, setPagesAmount] = useState<number>();
  const [pageNumber, setPageNumber] = useState(1);
  const [inputNumber, setInputNumber] = useState("");
  const movePage = useRef(false);

  
  const observer = useIntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const child = entry.target.firstChild;
          if (child instanceof Element) {
            const elementNumber = child.getAttribute("data-page-number");
            if (elementNumber) {
              setPageNumber(parseInt(elementNumber, 10));
            }
          }
          obs.disconnect();
        }
      });
    },
    { threshold: 0.5 }
  );



  useEffect(() => {
    if (!props.contract) {
      setPdfData(undefined);
      return;
    }
    if (props.file) setPdfReference(props.file);
    else if (props.contract.file_ref !== pdfReference) setPdfReference(props.contract.file_ref);
  }, [props.contract]);


  useEffect(() => {
    void formatPdfData(pdfReference);
  }, [pdfReference]);


  useEffect(() => {
    if (!movePage.current) return;
    const page = pageRefs.current[pageNumber];
    if (page) {
      page.scrollIntoView({ behavior: "smooth" });
    }
    movePage.current = false;
  }, [pageNumber]);




  async function formatPdfData(fileReference: string | File | Blob | null): Promise<void> {
    setPagesAmount(undefined);
    if (!props.project) return;
    
    setIsLoading(true);
    if (fileReference && props.contract) {
      let file: string | File | Blob = fileReference;
      if (typeof file === "string") {
        const url = new URL(`${window.location.origin}/api/contracts/`);
        url.searchParams.set("projectId", props.project.id.toString());
        url.searchParams.set(
          "contractId",
          props.contract.id.toString()
        );
        const response = await fetch(url, { method: "GET" });
        const blob = await response.blob();
        file = blob;
      }
      if (file.type === "application/pdf") {
        const reader = new FileReader();
        reader.onload = (event: ProgressEvent<FileReader>) => {
          if (event.target?.result) {
            setPdfData(event.target.result as string);
          } else setPdfData(undefined);
        };
        reader.readAsDataURL(file);
      } else setPdfData(undefined);
    } else setPdfData(undefined);
    setIsLoading(false);
  }


  function onClose(): void {
    router.push(`/${props.projectId}/`);
  }

  function onHover(): void {
    router.prefetch(`/${props.projectId}/`);
  }

  function handleExpansion(): void {
    props.handleExpansion();
  }

  function handleZoom(type: "in" | "out" | "reset"): void {
    if (type === "in") {
      setPdfZoom((current) =>
        current ? parseFloat((current + 0.1).toFixed(2)) : 1.1
      );
    } else if (type === "out") {
      setPdfZoom((current) =>
        current ? parseFloat((current - 0.1).toFixed(2)) : 0.9
      );
    } else setPdfZoom(undefined);
  }

  function getPagesAmount(document: PDFDocumentProxy): void {
    setPagesAmount(document.numPages);
    setPageNumber(1);
  }

  function previousPage(): void {
    changePage(-1);
  }
  function nextPage(): void {
    changePage(1);
  }
  function changePage(offset: number): void {
    movePage.current = true;
    setPageNumber((prevPageNumber) => prevPageNumber + offset);
  }

  function handleInputNumber(input: string): void {
    setInputNumber(input);
  }
  function handleInputBlur(): void {
    setPageByInput();
  }
  function handleKeyDown(
    key: string,
    event: KeyboardEvent<HTMLInputElement>
  ): void {
    if (key !== "Enter") return;
    setPageByInput();
    if (event.target instanceof HTMLElement) event.target.blur();
  }
  function setPageByInput(): void {
    const parsedInput = parseInt(inputNumber);
    if (
      !pagesAmount ||
      isNaN(parsedInput) ||
      parsedInput < 1 ||
      parsedInput > pagesAmount
    ) {
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
      observer.current?.observe(pageRef);
    }
  }, 200);

  function _highlightPattern(
    text: string,
    patterns: (string | RegExp)[],
    ignoreCase = true
  ): string {
    let processedText = text;
    patterns.forEach((pattern) => {
      let regex: RegExp;
      // If the pattern is a string, create a RegExp with optional case insensitivity
      if (typeof pattern === "string") {
        const escapedPattern = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        regex = new RegExp(escapedPattern, ignoreCase ? "gi" : "g");
      } else {
        // If it's already a RegExp, respect its original flags
        regex = new RegExp(
          pattern.source,
          pattern.flags +
          (ignoreCase && !pattern.flags.includes("i") ? "i" : "")
        );
      }
      processedText = processedText.replace(
        regex,
        (value) => `<mark>${value}</mark>`
      );
    });
    return processedText;
  }

  // const textRenderer = useCallback(
  //     (textItem: {str: string}) => highlightPattern(textItem.str, highlightTerms),
  //     [highlightTerms]
  // );

  return (
    <div className="pdf-display-container">
      <div className="pdf-display-header">
        <div className="controls-box">
          <CommonButton onClick={onClose} onMouseEnter={onHover}>
            <ElevaiteIcons.SVGArrowBack />
          </CommonButton>
          <span>Preview</span>
        </div>
        {!pdfData ? undefined : (
          <div className="controls-box">
            <CommonButton
              onClick={() => {
                handleZoom("out");
              }}
              noBackground
              disabled={pdfZoom !== undefined && pdfZoom <= 0.1}
              title="Zoom out"
            >
              <ElevaiteIcons.SVGZoom type="out" />
            </CommonButton>
            <CommonButton
              className="reset"
              onClick={() => {
                handleZoom("reset");
              }}
              noBackground
              title="Reset zoom"
            >
              {pdfZoom ? `${(pdfZoom * 100).toFixed(0).toString()} %` : "100%"}
            </CommonButton>
            <CommonButton
              onClick={() => {
                handleZoom("in");
              }}
              noBackground
              disabled={pdfZoom !== undefined && pdfZoom >= 3}
              title="Zoom in"
            >
              <ElevaiteIcons.SVGZoom />
            </CommonButton>
            <CommonButton
              className={[
                "expansion-arrow",
                props.isExpanded ? "expanded" : undefined,
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={handleExpansion}
              noBackground
              title={props.isExpanded ? "Restore views" : "Maximize pdf view"}
            >
              <ElevaiteIcons.SVGSideArrow />
            </CommonButton>
          </div>
        )}
      </div>

      <div
        ref={pageContainerRef}
        className="pdf-display-scroller"
        onScroll={onScroll}
      >
        <div className="pdf-display-contents">
          {isLoading ? (
            <div className="loading large">
              <ElevaiteIcons.SVGSpinner />
            </div>
          ) : !pdfData ? (
            <div className="no-file">No pdf attached.</div>
          ) : (
            <Document
              file={pdfData}
              onLoadSuccess={getPagesAmount}
              loading={
                <div className="loading large">
                  <ElevaiteIcons.SVGSpinner />
                </div>
              }
            >
              {pagesAmount === undefined
                ? undefined
                : Array.from(new Array(pagesAmount), (entry, index) => (
                  <div
                    key={`page_${(index + 1).toString()}`}
                    ref={(item) => {
                      pageRefs.current[index + 1] = item;
                    }}
                  >
                    <Page
                      pageNumber={index + 1}
                      width={pageContainerWidth ? pageContainerWidth : 1}
                      scale={pdfZoom}
                      // customTextRenderer={textRenderer}
                      loading={
                        <div className="loading large">
                          <ElevaiteIcons.SVGSpinner />
                        </div>
                      }
                    />
                  </div>
                ))}
            </Document>
          )}
        </div>
      </div>

      {!pdfData ? undefined : (
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
            <CommonButton onClick={previousPage} disabled={pageNumber <= 1}>
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
      )}
    </div>
  );
}
