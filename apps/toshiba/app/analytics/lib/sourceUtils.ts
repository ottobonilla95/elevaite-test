import { SourceReference } from "../../lib/interfaces";

/**
 * Extracts source information from the accumulated text
 * Looks for patterns like:
 * - Source: 6800 Hardware Service Guide (2).pdf, Page 41
 * - Sources: 6800 Hardware Service Guide (2).pdf, Page [41,54]
 * - Sources: 6800 Hardware Service Guide (2).pdf, Page [11,154]
 * - Source: 6800 Parts Manual (3).pdf, Pages: 40-45
 * - Source: [6800 Hardware Service Guide (2).pdf](https://example.com/file.pdf), Page 41
 * - 6800 Hardware Service Guide (2).pdf, Page 213 [aws_link: 6800_Hardware_Service_Guide_(2).pdf_page_213]
 * - 6800 Parts Manual (3) page 91 [aws_id: 6800 Parts Manual (3)_page_91]
 *
 * @param text The accumulated text to extract sources from
 * @returns Array of SourceReference objects or undefined if no sources found
 */
export function extractSourcesFromText(text: string): SourceReference[] | undefined {
  if (!text) return undefined;

  // Look for source information at the end of the text after <Answer> tag or "**Sources:**"
  let textAfterAnswerTag = text;

  // First try to find the <Answer> tag
  const answerTagIndex = text.lastIndexOf("<Answer>");
  if (answerTagIndex !== -1) {
    textAfterAnswerTag = text.substring(answerTagIndex);
  } else {
    // If no <Answer> tag, look for "**Sources:**"
    const sourcesHeaderIndex = text.lastIndexOf("**Sources:**");
    if (sourcesHeaderIndex !== -1) {
      textAfterAnswerTag = text.substring(sourcesHeaderIndex);
    } else {
      // If neither is found, try to find any source pattern directly
      const sourceIndex = text.lastIndexOf("Source:");
      if (sourceIndex === -1) {
        // If no source indicators are found, return undefined
        return undefined;
      }
      textAfterAnswerTag = text.substring(sourceIndex);
    }
  }
  console.log("textAfterAnswerTag:", textAfterAnswerTag);

  // Different patterns to match
  const patterns = [
    // Source: filename.pdf, Page XX
    /Source:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+)/i,

    // Source: filename.pdf, Page [X,Y]
    /Source(?:s)?:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+\[(\d+,\d+)\]/i,

    // Source: filename.pdf, Pages: X-Y
    /Source(?:s)?:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+-\d+)/i,

    // - filename.pdf, Pages: XX [aws_link: filename_page_XX]
    /-\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+|\[.*?\])\s+\[aws_link:\s+(.*?)\]/i
  ];

  // Pattern for markdown-style links: [filename](url)
  const markdownLinkPattern = /\[(.*?\.pdf)\]\((https?:\/\/[^\s)]+)\)/g;

  // Pattern for aws_links: [aws_link: filename_page_XX]
  const awsLinkPattern = /\[aws_link:\s+(.*?)\]/g;

  // Pattern for aws_id: [aws_id: filename_page_XX]
  const awsIdPattern = /\[aws_id:\s+(.*?)\]/g;

  const sources: SourceReference[] = [];

  // First, extract any markdown-style links and store them in a map
  const linkMap = new Map<string, string>();
  let markdownMatch;
  while ((markdownMatch = markdownLinkPattern.exec(textAfterAnswerTag)) !== null) {
    if (markdownMatch.length >= 3) {
      linkMap.set(markdownMatch[1].trim(), markdownMatch[2].trim());
    }
  }

  // Extract aws_links and store them in a map
  const awsLinkMap = new Map<string, string>();
  let awsLinkMatch;
  while ((awsLinkMatch = awsLinkPattern.exec(textAfterAnswerTag)) !== null) {
    if (awsLinkMatch.length >= 2) {
      const awsLink = awsLinkMatch[1].trim();
      // Store the aws_link to be used later when matching with filenames
      awsLinkMap.set(awsLink, awsLink);
    }
  }

  // Extract aws_ids and store them in the same map as aws_links
  // since they serve the same purpose
  let awsIdMatch;
  while ((awsIdMatch = awsIdPattern.exec(textAfterAnswerTag)) !== null) {
    if (awsIdMatch.length >= 2) {
      const awsId = awsIdMatch[1].trim();
      // Store the aws_id to be used later
      awsLinkMap.set(awsId, awsId);
    }
  }

  console.log("awsLinkMap:", awsLinkMap);
  console.log("textAfterAnswerTag:", textAfterAnswerTag);
  console.log("patterns:", patterns);
  const firstEntry = awsLinkMap.entries().next().value;
  if (firstEntry) {
    const [key, value] = firstEntry;
    console.log("First key:", key);
    console.log("First value:", value);
  }
  // const [key, value] = firstEntry;
  //   const sourceObjects: SourceReference[] = [{ filename: "Source", pages: "page" , awsLink: key.toString() }];
  //   console.log("sourceObjects:", sourceObjects);
  //   sources.push(...sourceObjects);
  for (const [key] of awsLinkMap.entries()) {
    const sourceObject: SourceReference = { filename: "Source", pages: "", awsLink: key.toString() };
    sources.push(sourceObject);
  }

  // Look for direct aws_id pattern in the format: "6800 Parts Manual (3) page 91 [aws_id: 6800 Parts Manual (3)_page_91]"
  const directAwsIdPattern = /(.*?)\s+page\s+(\d+)\s+\[aws_id:\s+(.*?)\]/g;
  let directAwsIdMatch;
  while ((directAwsIdMatch = directAwsIdPattern.exec(textAfterAnswerTag)) !== null) {
    if (directAwsIdMatch.length >= 4) {
      const filename = directAwsIdMatch[1].trim();
      const pageNum = directAwsIdMatch[2].trim();
      const awsId = directAwsIdMatch[3].trim();

      // Create a source reference object
      const source: SourceReference = {
        filename: `${filename}.pdf`, // Add .pdf extension for consistency
        pages: pageNum,
        awsLink: awsId // Use awsLink field for the aws_id
      };

      // Store the full match text to help with replacement later
      source.fullMatchText = directAwsIdMatch[0];

      sources.push(source);
    }
  }

  // Try each pattern
  for (const pattern of patterns) {
    const matches = textAfterAnswerTag.match(pattern);
    console.log("matches:", matches);
    if (matches && matches.length >= 3) {
      const filename = matches[1].trim();
      const pages = matches[2].trim();
      const source: SourceReference = {
        filename,
        pages
      };

      console.log("matches:", matches);

      // Check if we have a URL for this filename
      if (linkMap.has(filename)) {
        source.url = linkMap.get(filename);
      }

      // Check if this is the aws_link pattern (which has 4 capture groups)
      if (matches.length >= 4 && matches[3]) {
        // Use the aws_link as the URL
        const awsLink = matches[3].trim();
        console.log("awsLink:", awsLink);
        // Generate a URL for the aws_link
        // This would typically be handled by getImageUrl, but we'll set it here
        // so it can be processed later
        source.awsLink = awsLink;
      } else {
        // Check if we have an aws_link that matches this filename and page
        // This is a fallback for when the aws_link is mentioned separately
        const baseFilename = filename.replace(".pdf", "");

        // Handle different page formats: single number, range, or array
        let pageNum = "";
        if (pages.startsWith("[") && pages.endsWith("]")) {
          // Handle array format like [135, 136, 334, 337, 338]
          const pageArray = pages.substring(1, pages.length - 1).split(",");
          if (pageArray.length > 0) {
            pageNum = pageArray[0].trim();
          }
        } else if (pages.includes("-")) {
          // Handle range format like 40-45
          pageNum = pages.split("-")[0].trim();
        } else {
          // Handle single number format
          pageNum = pages.split(",")[0].trim();
        }

        const possibleAwsLink = `${baseFilename.replace(/ /g, "_")}_page_${pageNum}`;

        if (awsLinkMap.has(possibleAwsLink)) {
          source.awsLink = possibleAwsLink;
        }
      }

      sources.push(source);
    }
  }

  // Log the extracted sources for debugging
  console.log("Extracted sources:", sources);

  // If we found any sources, return them
  return sources.length > 0 ? sources : undefined;
}
