"""
High-level LLM tasks used by the rest of the backend.

Historically this module was hard-wired to OpenAI (``client.responses.parse``).
It is now a thin wrapper around :mod:`services.llm_clients`, which routes
each call to whichever provider (OpenAI / Anthropic / Gemini) the user has
configured for that role via :mod:`services.llm_config`.

The module keeps its original name + function signatures so existing
callers keep working unchanged. The legacy ``model_id`` override argument is
still accepted and forwarded as a per-call override.
"""

from typing import Optional, Dict, Any

from .models import PaperAnalysis, RelevanceDecision, ApplicationIdea, PaperSections
from . import llm_clients


async def summarize_paper(markdown_text: str, model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured knowledge from a paper's full markdown.

    Uses the provider configured for the ``deep_analysis`` role. The optional
    ``model_id`` overrides the model (provider stays as configured).
    """
    print("🤖 Starting LLM analysis...")
    system_prompt = """
    You are an expert AI Research Scientist. Your goal is to extract structured knowledge from academic papers.

    Follow this reasoning process:
    1. **Scan for Context**: Read the Abstract and Introduction to understand the "Status Quo".
    2. **Identify the Delta**: Look for the specific "Method" section to see what they changed.
    3. **Filter Benchmarks**: Look at Tables and Results. ONLY extract results that clearly belong to THIS paper's method. Mark baselines as `is_this_paper_result=False`.
    4. **Verify**: For every number you extract, find the exact quote/location in the text.
    """

    try:
        analysis, usage = await llm_clients.parse_structured(
            role="deep_analysis",
            schema=PaperAnalysis,
            system=system_prompt,
            user=f"Analyze this paper:\n\n{markdown_text}",
            model=model_id,
        )
        return {
            "success": True,
            "data": analysis.model_dump(exclude={"analysis_thought_process"}),
            "usage": usage,
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "usage": None,
            "error": str(e),
        }


async def extract_paper_sections(raw_markdown: str, model_id: Optional[str] = None) -> PaperSections:
    """Segment raw OCR markdown into sections using a cheap model."""
    print("🧹 Pre-processing paper sections...")
    system_prompt = """
    You are a Research Assistant. Your job is to organize raw OCR markdown into logical sections.

    Rules:
    1. **Extract Verbatim**: Do not summarize. Copy the text exactly as it appears in the sections.
    2. **Isolate Contributions**: Look specifically for the "Our contributions are..." or "In summary..." list at the end of the Introduction. Extract this text into `contributions_text`.
    3. **Group Smartly**:
       - Put "Related Work" into `introduction_text`.
       - Put "Ablation Studies" into `experiments_text`.
    4. **Find the Code**: Aggressively search for a GitHub or project page URL.
    5. **Ignore Noise**: Do not extract References, Citations lists, or Appendix unless it contains critical results.
    """

    try:
        parsed, _ = await llm_clients.parse_structured(
            role="sections",
            schema=PaperSections,
            system=system_prompt,
            user=f"Organize this raw paper text:\n\n{raw_markdown}",
            model=model_id,
        )
        return parsed
    except Exception as e:
        print(f"⚠️ Pre-processing failed: {e}")
        return PaperSections(
            title="Unknown Title",
            abstract_text=raw_markdown[:2000],
            introduction_text="",
            methodology_text="",
            experiments_text=raw_markdown,
            conclusion_text="",
            github_url=None,
        )


async def is_paper_relevant(
    application_idea: ApplicationIdea,
    paper_title: str,
    paper_abstract: str,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Yes/no filter that checks whether a paper matches an application idea."""
    system_prompt = """
    You are a strict Research Curator.
    Your task is to filter academic papers for a specific engineering application.

    Criteria for Relevance:
    1. Does this paper propose a method, model, or dataset useful for the target application?
    2. Is it technically aligned (e.g., if the app is Computer Vision, reject pure NLP papers unless multimodal)?

    Output a boolean decision and a one-sentence justification.
    """

    user_prompt = f"""
    Target Application (JSON):
    {application_idea.model_dump_json(indent=2)}

    Candidate Paper:
    - Title: {paper_title}
    - Abstract: {paper_abstract}
    """

    try:
        result, _ = await llm_clients.parse_structured(
            role="relevance",
            schema=RelevanceDecision,
            system=system_prompt,
            user=user_prompt,
            model=model_id,
        )
        return {
            "success": True,
            "decision": result.is_relevant,
            "reason": result.reasoning,
        }
    except Exception as e:
        print(f"Filter Error on '{paper_title}': {e}")
        return {
            "success": False,
            "decision": False,
            "reason": f"Error: {str(e)}",
        }
