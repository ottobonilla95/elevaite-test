import "./DocumentHeadersParser.scss";



export interface ParsedExtraction {
  contains_header_error: boolean;
  document_headers: string[];
  line_item_headers: string[];
  // header is duplicate; kept here for reference only
  // header?: {
  //   document_headers: string[];
  //   line_item_headers: string[];
  // };
  prompt: string;
  result: ExtractionResult;
}

export type ExtractionResult = Record<string, string> & {
  line_items: Record<string, string>[];
};



interface DocumentHeadersParserProps {

}

export function DocumentHeadersParser(props: DocumentHeadersParserProps): JSX.Element {
    return (
        <div className="-document-headers-parser-container">

        </div>
    );
}