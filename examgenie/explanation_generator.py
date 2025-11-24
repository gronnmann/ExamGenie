"""Generate detailed explanations for topics."""

import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .llm_client import LLMClient
from .models import Explanation, ExampleQuestion, Topic, ExamDocument
from .rag_system import RAGSystem

console = Console()


class ExplanationGenerator:
    """Generate detailed explanations for topics using LLM and RAG."""
    
    def __init__(self, llm_client: LLMClient, rag_system: RAGSystem | None = None):
        """
        Initialize the explanation generator.
        
        Args:
            llm_client: LLM client for API calls
            rag_system: Optional RAG system for context retrieval
        """
        self.llm_client = llm_client
        self.rag_system = rag_system
    
    def _find_related_questions(
        self,
        topic_name: str,
        exam_docs: list[ExamDocument],
    ) -> list[ExampleQuestion]:
        """
        Find exam questions related to a topic.
        
        Args:
            topic_name: Name of the topic
            exam_docs: List of exam documents
            
        Returns:
            List of related example questions
        """
        # Simple keyword matching for now
        # Could be enhanced with semantic search
        questions: list[ExampleQuestion] = []
        
        topic_keywords = topic_name.lower().split()
        
        for doc in exam_docs:
            # Split document into potential questions (simple heuristic)
            lines = doc.text.split('\n')
            current_question = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_question:
                        question_text = ' '.join(current_question)
                        # Check if question relates to topic
                        if any(keyword in question_text.lower() for keyword in topic_keywords):
                            questions.append(ExampleQuestion(
                                question=question_text,
                                source_file=doc.filename,
                            ))
                        current_question = []
                else:
                    current_question.append(line)
        
        return questions[:3]  # Return top 3 related questions
    
    def generate_explanation(
        self,
        topic: Topic,
        exam_docs: list[ExamDocument],
        parent_context: str = "",
    ) -> Explanation:
        """
        Generate detailed explanation for a topic.
        
        Args:
            topic: Topic to explain
            exam_docs: List of exam documents for context
            parent_context: Context from parent topics
            
        Returns:
            Detailed explanation
        """
        # Build context
        topic_path = f"{parent_context} > {topic.name}" if parent_context else topic.name
        
        # Get RAG context if available
        rag_context = ""
        if self.rag_system:
            try:
                relevant_chunks = self.rag_system.search(topic.name, top_k=3)
                if relevant_chunks:
                    rag_context = "\n\n".join(relevant_chunks)
            except Exception:
                pass  # RAG is optional
        
        # Create prompt
        system_prompt = """You are an expert educator creating comprehensive study materials. Your task is to provide detailed, intuitive explanations of academic topics.

For each topic, provide:
1. A thorough explanation of the concept
2. Key concepts and principles to remember
3. Intuitive examples and analogies to aid understanding
4. Practical applications when relevant

Make your explanations clear, engaging, and accessible. Use analogies and real-world examples to make complex concepts easier to grasp."""

        user_prompt = f"""Topic: {topic_path}
Description: {topic.description}"""

        if rag_context:
            user_prompt += f"""

Reference Material:
{rag_context}"""

        user_prompt += """

Provide a detailed explanation in JSON format:
{
  "explanation": "Detailed explanation text",
  "key_concepts": ["concept1", "concept2", ...],
  "examples": ["example1", "example2", ...]
}

Return ONLY the JSON object, no additional text."""

        # Call LLM
        response = self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        
        # Parse response
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            # Find related questions
            related_questions = self._find_related_questions(topic.name, exam_docs)
            
            return Explanation(
                topic_name=topic_path,
                explanation=data.get("explanation", ""),
                examples=data.get("examples", []),
                key_concepts=data.get("key_concepts", []),
                related_questions=related_questions,
            )
        
        except json.JSONDecodeError as e:
            console.print(f"[yellow]⚠[/yellow] Failed to parse explanation JSON for {topic.name}: {e}")
            # Return basic explanation
            return Explanation(
                topic_name=topic_path,
                explanation=response,
                examples=[],
                key_concepts=[],
                related_questions=[],
            )
    
    def generate_all_explanations(
        self,
        topics: list[Topic],
        exam_docs: list[ExamDocument],
    ) -> dict[str, Explanation]:
        """
        Generate explanations for all topics and subtopics.
        
        Args:
            topics: List of hierarchical topics
            exam_docs: List of exam documents
            
        Returns:
            Dictionary mapping topic paths to explanations
        """
        explanations: dict[str, Explanation] = {}
        
        def process_topic(topic: Topic, parent_context: str = ""):
            topic_path = f"{parent_context} > {topic.name}" if parent_context else topic.name
            
            console.print(f"[cyan]→[/cyan] Generating explanation for: {topic_path}")
            
            explanation = self.generate_explanation(topic, exam_docs, parent_context)
            explanations[topic_path] = explanation
            
            # Process subtopics
            for subtopic in topic.subtopics:
                process_topic(subtopic, topic_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating explanations...", total=None)
            
            for topic in topics:
                process_topic(topic)
        
        console.print(f"[green]✓[/green] Generated {len(explanations)} explanations")
        return explanations
