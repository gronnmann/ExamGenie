"""Type definitions and data models for ExamGenie."""

from pydantic import BaseModel, Field


class Topic(BaseModel):
    """Represents a hierarchical topic structure."""
    
    name: str = Field(description="Topic name")
    description: str = Field(description="Brief topic description")
    subtopics: list["Topic"] = Field(default_factory=list, description="Nested subtopics")
    level: int = Field(default=0, description="Hierarchy level (0=top level)")


class ExampleQuestion(BaseModel):
    """Represents an example question from an exam."""
    
    question: str = Field(description="The question text")
    source_file: str = Field(description="Source exam filename")
    page_number: int | None = Field(default=None, description="Page number in source")


class Explanation(BaseModel):
    """Detailed explanation for a topic."""
    
    topic_name: str = Field(description="Name of the topic being explained")
    explanation: str = Field(description="Detailed explanation text")
    examples: list[str] = Field(default_factory=list, description="Intuitive examples")
    key_concepts: list[str] = Field(default_factory=list, description="Key concepts to remember")
    related_questions: list[ExampleQuestion] = Field(default_factory=list, description="Related exam questions")


class ExamDocument(BaseModel):
    """Represents an extracted exam document."""
    
    filename: str = Field(description="Original filename")
    text: str = Field(description="Extracted text content")
    page_count: int = Field(description="Number of pages")


class ExamAnalysis(BaseModel):
    """Complete analysis result."""
    
    topics: list[Topic] = Field(description="Hierarchical topic structure")
    explanations: dict[str, Explanation] = Field(description="Explanations keyed by topic name")
    source_exams: list[str] = Field(description="List of analyzed exam filenames")
