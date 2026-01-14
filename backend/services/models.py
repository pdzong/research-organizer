from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Benchmark(BaseModel):
    name: str = Field(..., description="The name of the benchmark or dataset (e.g., ImageNet, GLUE).")
    score: str = Field(..., description="The numerical score or result achieved.")
    metric: str = Field(..., description="The metric used (e.g., Accuracy, F1-Score, BLEU).")

class Summary(BaseModel):
    main_contribution: str = Field(..., description="The key innovation or finding of the paper.")
    methodology: str = Field(..., description="The approach or methods used in the research.")
    key_results: str = Field(..., description="The main findings or outcomes.")
    significance: str = Field(..., description="Why this work is important.")
    limitations: str = Field(..., description="Notable limitations or future work mentioned.")

class PaperAnalysis(BaseModel):
    paper_title: str = Field(..., description="The exact title of the research paper.")
    summary: Summary = Field(..., description="Structured summary of the paper.")
    benchmarks: List[Benchmark] = Field(..., description="List of all quantitative benchmarks mentioned.")

    # FUTURE EXTENSION POINT:
    # affiliations: List[Affiliation]
    # methods: List[Method]