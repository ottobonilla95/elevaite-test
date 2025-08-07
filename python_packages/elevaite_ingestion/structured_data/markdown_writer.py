"""
Markdown writer for structured data output.
"""

from utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownWriter:
    """Writer for converting parsed content to markdown format."""

    def __init__(self):
        self.name = "markdown_writer"
        logger.info("Initialized Markdown writer")

    def write(self, content: str, metadata: dict) -> str:
        """
        Convert content to markdown format.

        Args:
            content: Raw text content
            metadata: Optional metadata dictionary

        Returns:
            Formatted markdown content
        """
        try:
            markdown_content = []

            # Add metadata as front matter if provided
            if metadata:
                markdown_content.append("---")
                for key, value in metadata.items():
                    markdown_content.append(f"{key}: {value}")
                markdown_content.append("---")
                markdown_content.append("")

            # Add the main content
            markdown_content.append(content)

            result = "\n".join(markdown_content)
            logger.info(f"Generated markdown content with {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"Failed to write markdown content: {e}")
            # Return original content as fallback
            return content

    def write_to_file(self, content: str, file_path: str, metadata: dict) -> bool:
        """
        Write markdown content to a file.

        Args:
            content: Raw text content
            file_path: Output file path
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            markdown_content = self.write(content, metadata)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"Successfully wrote markdown to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write markdown to {file_path}: {e}")
            return False
