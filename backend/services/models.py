from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator


class ApplicationIdea(BaseModel):
    domain: str = Field(..., description="Short keyword for search queries (e.g., 'Robotic Manipulation').")
    specific_utility: str = Field(..., description="Specific explanation of how this paper's method applies. Format: '[Action] by [Mechanism]'. Example: 'Enables precise robotic hand angle adjustments by calculating spatial distance between visual features.'")

class BenchmarkResult(BaseModel):
    name: str = Field(..., description="The standardized name of the benchmark or dataset (e.g., ImageNet-1k, GSM8K).")
    score: str = Field(..., description="The numerical score achieved (e.g., '88.5%', '76.3').")
    metric: str = Field(..., description="The metric used (e.g., Accuracy, F1-Score, Pass@1).")
    setting: Optional[str] = Field(None, description="The specific setting (e.g., 'Zero-shot', 'Fine-tuned', '5-shot').")
    
    # Validation fields
    is_this_paper_result: bool = Field(..., description="True if this result was achieved by the authors of this paper. False if it is a baseline from prior work.")
    source_quote: str = Field(..., description="The exact text snippet or table row where this number appears. Used for verification.")

class NoveltyAnalysis(BaseModel):
    status_quo: str = Field(..., description="What was the problem with previous methods? (The 'Before' state).")
    proposed_delta: str = Field(..., description="What specific technical change did this paper introduce? (The 'After' state).")
    novelty_summary: str = Field(..., description="A concise synthesis of the innovation.")
    real_world_analogy: str = Field(..., description="Explain the innovation using a simple analogy (e.g., 'Like switching from a map to GPS').")

class Summary(BaseModel):
    main_contribution: str = Field(..., description="The key innovation or finding.")
    methodology: str = Field(..., description="The approach or methods used.")
    applications: List[ApplicationIdea] = Field(..., description="List of potential real-world applications derived from this method.")
    limitations: str = Field(..., description="Notable limitations or future work mentioned.")
    
    @model_validator(mode='before')
    @classmethod
    def handle_legacy_string_format(cls, data: Any) -> Any:
        """Handle old saved summaries that were just a single string value."""
        if isinstance(data, str):
            # Convert old string format to new structured format
            return {
                'main_contribution': data,
                'methodology': 'Legacy format - details not available',
                'applications': [],
                'limitations': 'Legacy format - details not available'
            }
        return data

class PaperAnalysis(BaseModel):
    paper_title: str = Field(..., description="The exact title of the research paper.")
    
    # The "Reasoning" Scratchpad: The LLM fills this first to 'think' 
    # This improves the quality of the subsequent fields significantly.
    analysis_thought_process: Optional[str] = Field(default=None, description="Step-by-step reasoning: First, list related work mentions. Second, identify the gap. Third, summarize the author's specific solution.")
    
    novelty: NoveltyAnalysis = Field(..., description="Deep dive into the paper's novelty.")
    summary: Summary = Field(..., description="General summary of the paper.")
    github_repo: str = Field(..., description="Attached repository address containing the code created alongside this paper.")
    benchmarks: List[BenchmarkResult] = Field(..., description="List of all quantitative benchmarks found in tables or text.")

class RelevanceDecision(BaseModel):
    is_relevant: bool = Field(
        ..., 
        description="True if the paper provides technical methods, data, or insights directly applicable to the target application."
    )
    reasoning: str = Field(
        ..., 
        description="A single sentence explaining why it is relevant or why it was rejected."
    )

class ImplementationStep(BaseModel):
    phase: str = Field(..., description="Phase name (e.g., 'Prototype', 'Scaling').")
    action_items: List[str] = Field(..., description="Specific technical tasks.")
    risk: str = Field(..., description="Primary risk in this phase.")

class ROIAnalysis(BaseModel):
    target_metric: str = Field(..., description="What number are we trying to improve? (e.g., 'Inference Latency', 'Diagnostic Accuracy').")
    estimated_impact: str = Field(..., description="Projected improvement based on the papers analyzed.")
    cost_driver: str = Field(..., description="The most expensive part of this solution (e.g., 'GPU Compute', 'Data Labeling').")

class ApplicationPlan(BaseModel):
    application_name: str = Field(..., description="A catchy but descriptive name for this solution.")
    executive_summary: str = Field(..., description="The elevator pitch.")
    
    # Synthesis of the collection
    key_enabling_papers: List[str] = Field(..., description="Which specific papers from the collection make this possible?")
    technical_architecture: str = Field(..., description="High-level system design.")
    
    # The business logic
    implementation_plan: List[ImplementationStep]
    roi_analysis: ROIAnalysis
    definition_of_done: str = Field(..., description="The specific criteria to declare the project a success.")