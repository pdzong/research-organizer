import os
from openai import OpenAI
from typing import Optional, Dict, Any
from .models import PaperAnalysis, RelevanceDecision, ApplicationIdea, PaperSections

# Global client variable
_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
    return _client

async def summarize_paper(markdown_text: str, model_id: str = "gpt-5.2") -> Dict[str, Any]:
    """
    Summarize a research paper using Structured Outputs.
    
    Args:
        markdown_text: The full paper text in markdown format.
        
    Returns:
        dict: A dictionary representation of the PaperAnalysis model.
    """
    try:
        print("🤖 Starting LLM analysis...")
        client = get_openai_client()
        
        # We use a multi-step prompt strategy within the system message
        system_prompt = """
        You are an expert AI Research Scientist. Your goal is to extract structured knowledge from academic papers.
        
        Follow this reasoning process:
        1. **Scan for Context**: Read the Abstract and Introduction to understand the "Status Quo".
        2. **Identify the Delta**: Look for the specific "Method" section to see what they changed.
        3. **Filter Benchmarks**: Look at Tables and Results. ONLY extract results that clearly belong to THIS paper's method. Mark baselines as `is_this_paper_result=False`.
        4. **Verify**: For every number you extract, find the exact quote/location in the text.
        """

        # Using OpenAI's native Structured Outputs (beta.chat.completions.parse)
        response = client.responses.parse(
            model=model_id, 
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this paper:\n\n{markdown_text}"}
            ],
            text_format=PaperAnalysis,
        )
        
        # The SDK automatically validates and parses the JSON into your Pydantic model
        analysis: PaperAnalysis = response.output_parsed
        
        # Convert Pydantic model to a clean dictionary
        # excluding the "thought_process" field if you don't want to show it in the UI
        return {
            "success": True,
            "data": analysis.model_dump(exclude={"analysis_thought_process"}), 
            "usage": {
                "model": response.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "usage": None,
            "error": str(e)
        }

async def extract_paper_sections(raw_markdown: str, model_id: str = "gpt-5-nano") -> PaperSections:
    """
    Uses a fast, cheap model to segment the paper and discard noise (References, Appendix).
    """
    print(f"🧹 Pre-processing with {model_id}...")
    client = get_openai_client()

    # The prompt is simple and instructional, focusing on "Segmentation" not "Reasoning"
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
        response = client.responses.parse(
            model=model_id,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Organize this raw paper text:\n\n{raw_markdown}"}
            ],
            text_format=PaperSections,
        )
        return response.output_parsed

    except Exception as e:
        print(f"⚠️ Pre-processing failed: {e}")
        # Fallback: If pre-processing fails, return a dummy object containing the raw text
        # so the pipeline doesn't break.
        return PaperSections(
            title="Unknown Title",
            abstract_text=raw_markdown[:2000], 
            introduction_text="",
            methodology_text="",
            experiments_text=raw_markdown, # dump everything here
            conclusion_text="",
            github_url=None
        )


async def is_paper_relevant(
    application_idea: ApplicationIdea,
    paper_title: str,
    paper_abstract: str,
    model_id: str = "gpt-5-nano" 
) -> Dict[str, Any]:
    """
    Quickly filters a paper based on its Title and Abstract against a target Application.
    """
    try:
        client = get_openai_client()
        
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

        response = client.responses.parse(
            model=model_id,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            text_format=RelevanceDecision,
        )
        
        result: RelevanceDecision = response.output_parsed
        
        return {
            "success": True,
            "decision": result.is_relevant,
            "reason": result.reasoning
        }

    except Exception as e:
        print(f"Filter Error on '{paper_title}': {e}")
        # Fail safe: In case of error, we default to False (skip) or True (keep) depending on your preference.
        # usually defaulting to False is safer to prevent pipeline clutter.
        return {
            "success": False, 
            "decision": False, 
            "reason": f"Error: {str(e)}"
        }