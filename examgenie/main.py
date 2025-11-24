"""ExamGenie CLI - Analyze exam PDFs and generate study guides."""

from pathlib import Path

import click
from rich.console import Console

from .llm_client import LLMClient
from .pdf_extractor import PDFExtractor
from .rag_system import RAGSystem
from .topic_analyzer import TopicAnalyzer
from .explanation_generator import ExplanationGenerator
from .output_generator import OutputGenerator
from .models import ExamAnalysis

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """ExamGenie - AI-powered exam analysis and study guide generator."""
    pass


@cli.command()
@click.option(
    "--exams-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Directory containing exam PDFs",
)
@click.option(
    "--context-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Optional directory with context documents (textbooks, etc.)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default="study_guide.pdf",
    help="Output PDF path",
)
@click.option(
    "--rebuild-index",
    is_flag=True,
    help="Force rebuild of RAG index",
)
@click.option(
    "--db-dir",
    type=click.Path(path_type=Path),
    default=".examgenie_db",
    help="Directory for ChromaDB persistence",
)
def analyze(
    exams_dir: Path,
    context_dir: Path | None,
    output: Path,
    rebuild_index: bool,
    db_dir: Path,
):
    """Analyze exams and generate a comprehensive study guide."""
    
    console.print("\n[bold cyan]ExamGenie - Exam Analysis[/bold cyan]\n")
    
    try:
        # Initialize components
        console.print("[cyan]→[/cyan] Initializing components...")
        llm_client = LLMClient()
        
        # Initialize RAG system if context directory provided
        rag_system = None
        if context_dir:
            rag_system = RAGSystem(db_dir, llm_client)
            rag_system.index_documents(context_dir, rebuild=rebuild_index)
        
        # Extract exam PDFs
        console.print(f"\n[cyan]→[/cyan] Extracting exam PDFs from {exams_dir}...")
        extractor = PDFExtractor()
        exam_docs = extractor.extract_from_directory(exams_dir)
        
        if not exam_docs:
            console.print("[red]✗[/red] No exam documents found!")
            return
        
        # Analyze topics
        console.print("\n[cyan]→[/cyan] Analyzing topics...")
        analyzer = TopicAnalyzer(llm_client)
        topics = analyzer.analyze_exams(exam_docs)
        
        # Generate explanations
        console.print("\n[cyan]→[/cyan] Generating detailed explanations...")
        generator = ExplanationGenerator(llm_client, rag_system)
        explanations = generator.generate_all_explanations(topics, exam_docs)
        
        # Create analysis result
        analysis = ExamAnalysis(
            topics=topics,
            explanations=explanations,
            source_exams=[doc.filename for doc in exam_docs],
        )
        
        # Generate PDF output
        console.print("\n[cyan]→[/cyan] Generating PDF output...")
        output_gen = OutputGenerator()
        output_gen.generate_pdf(analysis, output)
        
        console.print(f"\n[bold green]✓ Analysis complete![/bold green]")
        console.print(f"[green]Study guide saved to:[/green] {output.absolute()}")
    
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
