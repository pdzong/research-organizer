from typing import List, Optional
from pydantic import BaseModel, Field

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
    applications: List[str] = Field(..., description="Real-world use cases mentioned (e.g., 'Medical Diagnosis', 'Robotics').")
    limitations: str = Field(..., description="Notable limitations or future work mentioned.")

class PaperAnalysis(BaseModel):
    paper_title: str = Field(..., description="The exact title of the research paper.")
    
    # The "Reasoning" Scratchpad: The LLM fills this first to 'think' 
    # This improves the quality of the subsequent fields significantly.
    analysis_thought_process: str = Field(..., description="Step-by-step reasoning: First, list related work mentions. Second, identify the gap. Third, summarize the author's specific solution.")
    
    novelty: NoveltyAnalysis = Field(..., description="Deep dive into the paper's novelty.")
    summary: Summary = Field(..., description="General summary of the paper.")
    benchmarks: List[BenchmarkResult] = Field(..., description="List of all quantitative benchmarks found in tables or text.")