import os
from openai import OpenAI
from typing import Optional
from .models import PaperAnalysis

client = None

def get_openai_client():
    """Get or create OpenAI client instance."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        client = OpenAI(api_key=api_key)
    return client

async def summarize_paper(markdown_text: str, max_length: int = 20000) -> dict:
    """
    Summarize a research paper
    
    Args:
        markdown_text: The full paper text in markdown format
        max_length: Maximum characters to send (to avoid token limits)
    
    Returns:
        dict with summary and metadata
    """
    try:
        # Truncate if too long (keep first part which usually has abstract/intro)
        if len(markdown_text) > max_length:
            truncated_text = markdown_text[:max_length] + "\n\n[Content truncated...]"
        else:
            truncated_text = markdown_text
        
        openai_client = get_openai_client()
        
        # Create the prompt
        prompt = f"""You are an expert research paper analyst. Please analyze the following research paper and provide a structured analysis.

Extract the following information:

1. **Paper Title**: The exact title of the paper

2. **Summary**: A comprehensive summary organized into these sections:
   - main_contribution: What is the key innovation or finding?
   - methodology: What approach or methods were used?
   - key_results: What were the main findings or outcomes?
   - significance: Why is this work important?
   - limitations: Any notable limitations or future work mentioned?

3. **Benchmarks**: Extract ALL quantitative performance metrics and benchmark results mentioned in the paper. For each benchmark, provide:
   - name: The name of the benchmark/dataset (e.g., "ImageNet", "GLUE", "SQuAD", "COCO")
   - score: The numerical result achieved (e.g., "88.5%", "76.3", "SOTA")
   - metric: The evaluation metric used (e.g., "Accuracy", "F1-Score", "BLEU", "mAP", "Top-1 Accuracy")

Important: 
- Extract ALL benchmarks mentioned, including baseline comparisons
- If no benchmarks are mentioned, return an empty list
- Be precise with numerical values
- Include the metric units

Paper Content:
{truncated_text}
"""
               
        response = openai_client.responses.parse(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": "You are an expert research paper analyst who provides clear, structured summaries and extracts quantitative benchmarks from academic papers."},
                {"role": "user", "content": prompt}
            ],
            text_format=PaperAnalysis
        )
        
        analysis = response.output_parsed
        
        # Convert to dict for response
        analysis_dict = {
            "paper_title": analysis.paper_title,
            "summary": {
                "main_contribution": analysis.summary.main_contribution,
                "methodology": analysis.summary.methodology,
                "key_results": analysis.summary.key_results,
                "significance": analysis.summary.significance,
                "limitations": analysis.summary.limitations
            },
            "benchmarks": [
                {
                    "name": b.name,
                    "score": b.score,
                    "metric": b.metric
                }
                for b in analysis.benchmarks
            ]
        }
        
        return {
            "success": True,
            "summary": analysis_dict,
            "model": response.model,
            "tokens_used": response.usage.total_tokens,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "summary": None,
            "model": None,
            "tokens_used": None,
            "error": str(e)
        }
