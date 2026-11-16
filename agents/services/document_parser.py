
from pathlib import Path

import pymupdf
from docx import Document


class DocumentParser:
    """
    Extracts text from PDF, DOCX and TXT documents.
    """

    SUPPORTED_FORMATS = {".pdf", ".docx", ".txt"}

    def extract_text(self, file_path: str | Path) -> str:
        """
        Identifies the document format and extracts its text.
        """

        path = Path(file_path)

        # Check whether the file exists
        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        # Check whether the format is supported
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported document format: {extension}"
            )

        # Extract according to file type
        if extension == ".pdf":
            text = self._extract_pdf(path)

        elif extension == ".docx":
            text = self._extract_docx(path)

        else:
            text = self._extract_txt(path)

        # Reject empty documents
        text = text.strip()

        if not text:
            raise ValueError(
                f"No readable text found in document: {path.name}"
            )

        return text

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF pages."""

        extracted_pages = []

        with pymupdf.open(path) as pdf:
            for page in pdf:
                extracted_pages.append(page.get_text())

        return "\n".join(extracted_pages)

    def _extract_docx(self, path: Path) -> str:
        """Extract text from Word paragraphs and tables."""

        document = Document(path)

        extracted_content = []

        # Extract paragraphs
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                extracted_content.append(paragraph.text)

        # Extract tables
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )
                extracted_content.append(row_text)

        return "\n".join(extracted_content)

    def _extract_txt(self, path: Path) -> str:
        """Extract text from TXT files."""

        return path.read_text(encoding="utf-8-sig")
