"""PDF output generation using pypandoc."""

from pathlib import Path
import tempfile

import pypandoc
from rich.console import Console

from .models import ExamAnalysis, Topic, Explanation

console = Console()


class OutputGenerator:
    """Generate PDF study guides from analysis results."""
    
    def _topic_to_markdown(self, topic: Topic, explanations: dict[str, Explanation], level: int = 1, parent_path: str = "") -> str:
        """
        Convert a topic and its explanations to markdown.
        
        Args:
            topic: Topic to convert
            explanations: Dictionary of explanations
            level: Heading level
            parent_path: Parent topic path
            
        Returns:
            Markdown string
        """
        topic_path = f"{parent_path} > {topic.name}" if parent_path else topic.name
        heading = "#" * level
        
        md_parts = [f"{heading} {topic.name}\n"]
        
        if topic.description:
            md_parts.append(f"*{topic.description}*\n")
        
        # Add explanation if available
        if topic_path in explanations:
            explanation = explanations[topic_path]
            
            md_parts.append(f"\n{explanation.explanation}\n")
            
            # Add key concepts
            if explanation.key_concepts:
                md_parts.append("\n**Key Concepts:**\n")
                for concept in explanation.key_concepts:
                    md_parts.append(f"- {concept}\n")
            
            # Add examples
            if explanation.examples:
                md_parts.append("\n**Examples:**\n")
                for i, example in enumerate(explanation.examples, 1):
                    md_parts.append(f"\n{i}. {example}\n")
            
            # Add related questions
            if explanation.related_questions:
                md_parts.append("\n**Example Questions:**\n")
                for question in explanation.related_questions:
                    md_parts.append(f"\n> **From {question.source_file}:**\n")
                    md_parts.append(f"> {question.question}\n")
        
        # Process subtopics
        for subtopic in topic.subtopics:
            md_parts.append("\n")
            md_parts.append(self._topic_to_markdown(subtopic, explanations, level + 1, topic_path))
        
        return "".join(md_parts)
    
    def generate_pdf(self, analysis: ExamAnalysis, output_path: Path) -> None:
        """
        Generate a PDF study guide from analysis results.
        
        Args:
            analysis: Complete exam analysis
            output_path: Path for output PDF
        """
        console.print("[cyan]→[/cyan] Generating study guide PDF...")
        
        # Build markdown content
        md_parts = [
            "# Exam Study Guide\n\n",
            f"*Generated from {len(analysis.source_exams)} exam(s)*\n\n",
            "---\n\n",
        ]
        
        # Add table of contents
        md_parts.append("## Table of Contents\n\n")
        for topic in analysis.topics:
            md_parts.append(f"- [{topic.name}](#{topic.name.lower().replace(' ', '-')})\n")
            for subtopic in topic.subtopics:
                md_parts.append(f"  - [{subtopic.name}](#{subtopic.name.lower().replace(' ', '-')})\n")
        md_parts.append("\n---\n\n")
        
        # Add all topics and explanations
        for topic in analysis.topics:
            md_parts.append(self._topic_to_markdown(topic, analysis.explanations))
            md_parts.append("\n---\n\n")
        
        # Add source information
        md_parts.append("## Source Exams\n\n")
        for exam in analysis.source_exams:
            md_parts.append(f"- {exam}\n")
        
        markdown_content = "".join(md_parts)
        
        # Write markdown to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_md:
            tmp_md.write(markdown_content)
            tmp_md_path = tmp_md.name
        
        try:
            # Convert markdown to PDF using pypandoc
            pypandoc.convert_file(
                tmp_md_path,
                'pdf',
                outputfile=str(output_path),
                extra_args=[
                    '--pdf-engine=pdflatex',
                    '--variable', 'geometry:margin=1in',
                    '--variable', 'fontsize=11pt',
                    '--toc',
                    '--toc-depth=2',
                ],
            )
            
            console.print(f"[green]✓[/green] Study guide saved to: {output_path}")
        
        except Exception as e:
            console.print(f"[red]✗[/red] PDF generation failed: {e}")
            console.print(f"[yellow]⚠[/yellow] Saving markdown instead...")
            
            # Fallback: save as markdown
            md_output = output_path.with_suffix('.md')
            md_output.write_text(markdown_content, encoding='utf-8')
            console.print(f"[green]✓[/green] Markdown saved to: {md_output}")
            raise
        
        finally:
            # Clean up temporary file
            Path(tmp_md_path).unlink(missing_ok=True)
