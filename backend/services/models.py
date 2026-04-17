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


class PaperSections(BaseModel):
    """
    Intermediate structure to hold raw text segments extracted from the full paper.
    """
    title: str = Field(..., description="The exact title of the paper.")
    github_url: Optional[str] = Field(None, description="The HTTP URL to the code repository (GitHub/GitLab) if mentioned.")
    
    # We group sections logically to keep the context window focused
    abstract_text: str = Field(..., description="Full text of the Abstract.")
    introduction_text: str = Field(..., description="Full text of the Introduction and Related Work sections.")
    contributions_text: str = Field(..., description="Verbatim text of the 'Our Contributions' list, usually found at the end of the Introduction (e.g., 'Our main contributions are...').")
    methodology_text: str = Field(..., description="Full text of sections describing the Method, Architecture, or Approach.")
    experiments_text: str = Field(..., description="Full text of Experiments, Results, and Tables (including captions).")
    conclusion_text: str = Field(..., description="Full text of the Conclusion, Discussion, and Limitations.")

    def to_clean_markdown(self) -> str:
        """Reconstructs a clean, token-efficient markdown string for the next step."""
        # We explicitly omit References and Appendices here
        return f"""
# {self.title}

## Abstract
{self.abstract_text}

## Introduction & Context
{self.introduction_text}

## 🌟 Authors' Stated Contributions
{self.contributions_text}

## Methodology
{self.methodology_text}

## Experiments & Results
{self.experiments_text}

## Conclusion & Limitations
{self.conclusion_text}

## Meta Info
GitHub: {self.github_url or 'Not found'}
"""

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


# ─── Solution / System plan models (codegen-ready) ───────────────────────────
# These extend the lightweight ApplicationPlan with concrete artefacts that an
# LLM code generator (e.g. for a "build my app" agent) can directly consume.

class SolutionModule(BaseModel):
    name: str = Field(..., description="Short module / service name (e.g. 'PaperIngestor', 'PlanRenderer').")
    responsibility: str = Field(..., description="One-sentence statement of what this module owns.")
    inputs: List[str] = Field(default_factory=list, description="Names of inputs / upstream data this module consumes.")
    outputs: List[str] = Field(default_factory=list, description="Names of outputs this module produces.")
    technologies: List[str] = Field(default_factory=list, description="Concrete libraries / frameworks suggested for this module.")
    paper_grounding: List[str] = Field(default_factory=list, description="Paper titles or arxiv ids whose results justify this module.")


class SolutionDataModel(BaseModel):
    name: str = Field(..., description="Entity / table name.")
    fields: List[str] = Field(..., description="List of 'field_name: type — description' lines.")
    notes: Optional[str] = Field(None, description="Storage / indexing / lifecycle notes.")


class SolutionAPI(BaseModel):
    method: str = Field(..., description="HTTP method, e.g. GET / POST.")
    path: str = Field(..., description="Route path, e.g. /api/jobs/{id}.")
    purpose: str = Field(..., description="What this endpoint does in one sentence.")
    request: Optional[str] = Field(None, description="Request body / params summary.")
    response: Optional[str] = Field(None, description="Response shape summary.")


class SolutionMilestone(BaseModel):
    title: str = Field(..., description="Milestone / phase name.")
    deliverables: List[str] = Field(..., description="Concrete artefacts produced in this milestone.")
    estimated_effort: Optional[str] = Field(None, description="Rough effort estimate (e.g. '1 week', 'M').")


class SolutionRisk(BaseModel):
    description: str = Field(..., description="Risk in one sentence.")
    mitigation: str = Field(..., description="How to mitigate / monitor.")


class SolutionPlan(BaseModel):
    """
    A codegen-ready system / solution description derived from one or more papers.
    Designed to be self-contained enough that a downstream code-generation LLM
    can scaffold an actual project from it.
    """
    name: str = Field(..., description="Short product name.")
    tagline: str = Field(..., description="Single-sentence pitch.")
    problem_statement: str = Field(..., description="Concrete user / business problem this solution solves.")
    target_users: List[str] = Field(..., description="Primary user personas / segments.")

    scientific_grounding: str = Field(..., description="Which specific scientific results from the supplied papers make this feasible *now*. Cite papers by title or arxiv id.")
    key_enabling_papers: List[str] = Field(..., description="List of paper titles or arxiv ids that are load-bearing for this design.")

    system_overview: str = Field(..., description="2-4 paragraphs describing the system end-to-end.")
    architecture_diagram: str = Field(..., description="ASCII / mermaid description of the architecture (single fenced block content, no fences).")

    modules: List[SolutionModule] = Field(..., description="Concrete modules / services that make up the system.")
    data_models: List[SolutionDataModel] = Field(default_factory=list, description="Persistent data models / entities.")
    apis: List[SolutionAPI] = Field(default_factory=list, description="External / inter-module API surface.")
    integration_points: List[str] = Field(default_factory=list, description="Third-party services, models, datasets, hardware that the system depends on.")

    tech_stack: List[str] = Field(..., description="Suggested concrete tech stack (languages, frameworks, model providers).")
    milestones: List[SolutionMilestone] = Field(..., description="Phased delivery plan.")
    risks: List[SolutionRisk] = Field(default_factory=list, description="Top risks + mitigations.")

    success_metrics: List[str] = Field(..., description="Measurable KPIs / acceptance criteria.")
    open_questions: List[str] = Field(default_factory=list, description="Things that need a human decision before code-gen.")

    code_generation_prompt: str = Field(..., description="A self-contained prompt that can be handed to a code-generation LLM to scaffold the system. Should restate scope, constraints, tech stack, and acceptance criteria.")

    def to_markdown(self) -> str:
        """Render the plan as a markdown document suitable for handing to a code-gen LLM."""
        def _bullets(items: List[str]) -> str:
            return "\n".join(f"- {x}" for x in items) if items else "_None_"

        modules_md = "\n\n".join(
            f"### {m.name}\n"
            f"**Responsibility:** {m.responsibility}\n\n"
            f"- **Inputs:** {', '.join(m.inputs) or '—'}\n"
            f"- **Outputs:** {', '.join(m.outputs) or '—'}\n"
            f"- **Tech:** {', '.join(m.technologies) or '—'}\n"
            f"- **Paper grounding:** {', '.join(m.paper_grounding) or '—'}"
            for m in self.modules
        ) or "_None_"

        data_md = "\n\n".join(
            f"### {d.name}\n"
            + "\n".join(f"- {f}" for f in d.fields)
            + (f"\n\n_Notes:_ {d.notes}" if d.notes else "")
            for d in self.data_models
        ) or "_None_"

        api_md = "\n".join(
            f"- `{a.method} {a.path}` — {a.purpose}"
            + (f"\n  - Request: {a.request}" if a.request else "")
            + (f"\n  - Response: {a.response}" if a.response else "")
            for a in self.apis
        ) or "_None_"

        milestones_md = "\n\n".join(
            f"### {i+1}. {m.title}"
            + (f" _(≈ {m.estimated_effort})_" if m.estimated_effort else "")
            + "\n" + "\n".join(f"- {d}" for d in m.deliverables)
            for i, m in enumerate(self.milestones)
        ) or "_None_"

        risks_md = "\n".join(
            f"- **{r.description}** — _Mitigation:_ {r.mitigation}"
            for r in self.risks
        ) or "_None_"

        return f"""# {self.name}

> {self.tagline}

## Problem statement
{self.problem_statement}

## Target users
{_bullets(self.target_users)}

## Scientific grounding
{self.scientific_grounding}

### Key enabling papers
{_bullets(self.key_enabling_papers)}

## System overview
{self.system_overview}

## Architecture
```
{self.architecture_diagram}
```

## Modules
{modules_md}

## Data models
{data_md}

## API surface
{api_md}

## Integration points
{_bullets(self.integration_points)}

## Tech stack
{_bullets(self.tech_stack)}

## Milestones
{milestones_md}

## Risks
{risks_md}

## Success metrics
{_bullets(self.success_metrics)}

## Open questions
{_bullets(self.open_questions)}

---

## Code-generation prompt
The block below is intended to be fed verbatim to a code-generation LLM.

```
{self.code_generation_prompt}
```
"""