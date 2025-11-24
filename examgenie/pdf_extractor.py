"""PDF text extraction module."""

from pathlib import Path

from pypdf import PdfReader
from rich.console import Console

from .models import ExamDocument

console = Console()


class PDFExtractor:
    """Extract text content from PDF files."""
    
    def extract_from_file(self, pdf_path: Path) -> ExamDocument:
        """
        Extract text from a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExamDocument with extracted text
        """
        try:
            reader = PdfReader(pdf_path)
            text_parts: list[str] = []
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            
            return ExamDocument(
                filename=pdf_path.name,
                text=full_text,
                page_count=len(reader.pages),
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Error extracting {pdf_path.name}: {e}")
            raise
    
    def extract_from_directory(self, directory: Path) -> list[ExamDocument]:
        """
        Extract text from all PDF files in a directory.
        
        Args:
            directory: Directory containing PDF files
            
        Returns:
            List of ExamDocuments
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            console.print(f"[yellow]⚠[/yellow] No PDF files found in {directory}")
            return []
        
        console.print(f"[cyan]→[/cyan] Found {len(pdf_files)} PDF file(s)")
        
        documents: list[ExamDocument] = []
        for pdf_path in pdf_files:
            console.print(f"[cyan]→[/cyan] Extracting: {pdf_path.name}")
            doc = self.extract_from_file(pdf_path)
            documents.append(doc)
            console.print(f"[green]✓[/green] Extracted {doc.page_count} pages from {pdf_path.name}")
        
        return documents
