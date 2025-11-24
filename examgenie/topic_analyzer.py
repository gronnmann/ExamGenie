"""Topic extraction and hierarchical structuring."""

import json
from rich.console import Console

from .llm_client import LLMClient
from .models import ExamDocument, Topic

console = Console()


class TopicAnalyzer:
    """Extract and structure topics from exam documents."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the topic analyzer.
        
        Args:
            llm_client: LLM client for API calls
        """
        self.llm_client = llm_client
    
    def analyze_exams(self, exam_docs: list[ExamDocument]) -> list[Topic]:
        """
        Analyze exam documents and extract hierarchical topics.
        
        Args:
            exam_docs: List of exam documents
            
        Returns:
            List of hierarchical topics
        """
        console.print("[cyan]→[/cyan] Analyzing exams to extract topics...")
        
        # Combine all exam texts
        combined_text = "\n\n---\n\n".join([
            f"EXAM: {doc.filename}\n{doc.text}"
            for doc in exam_docs
        ])
        
        # Create prompt for topic extraction
        system_prompt = """You are an expert academic analyst. Your task is to analyze university exam questions and extract a comprehensive, hierarchical list of all topics and concepts covered.

For each topic:
1. Identify the main topic area
2. Break it down into relevant subtopics
3. Provide a brief description of what each topic covers

Return your response as a JSON array of topics with this structure:
[
  {
    "name": "Topic Name",
    "description": "Brief description of the topic",
    "level": 0,
    "subtopics": [
      {
        "name": "Subtopic Name",
        "description": "Brief description",
        "level": 1,
        "subtopics": []
      }
    ]
  }
]

Be thorough and comprehensive. Include all concepts, theories, methods, and techniques mentioned or implied by the exam questions."""

        user_prompt = f"""Analyze the following exam questions and extract all topics in a hierarchical structure:

{combined_text}

Return ONLY the JSON array, no additional text."""

        # Call LLM
        response = self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent structure
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            
            topics_data = json.loads(json_str)
            topics = [Topic(**topic_dict) for topic_dict in topics_data]
            
            console.print(f"[green]✓[/green] Extracted {len(topics)} main topics")
            return topics
        
        except json.JSONDecodeError as e:
            console.print(f"[red]✗[/red] Failed to parse topic JSON: {e}")
            console.print(f"[yellow]Response:[/yellow] {response[:500]}")
            raise
    
    def get_all_topic_paths(self, topics: list[Topic]) -> list[str]:
        """
        Get all topic paths (including nested subtopics) as flat list.
        
        Args:
            topics: List of hierarchical topics
            
        Returns:
            List of topic name paths (e.g., ["Topic A", "Topic A > Subtopic 1"])
        """
        paths: list[str] = []
        
        def traverse(topic: Topic, parent_path: str = ""):
            current_path = f"{parent_path} > {topic.name}" if parent_path else topic.name
            paths.append(current_path)
            
            for subtopic in topic.subtopics:
                traverse(subtopic, current_path)
        
        for topic in topics:
            traverse(topic)
        
        return paths
