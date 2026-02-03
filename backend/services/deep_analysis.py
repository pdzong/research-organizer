from typing import Optional, Dict, Any, List
import csv
from pathlib import Path
from datetime import datetime

from cache_service import load_analysis, load_metadata, load_markdown, save_markdown, save_metadata
from some_extensions.research_tools import arxiv_search_tool
from semantic_scholar import get_paper_metadata
from openai_service import is_paper_relevant, summarize_paper
from models import ApplicationIdea, PaperAnalysis
from pdf_parser import download_and_parse_paper
import asyncio


def extract_arxiv_ids(search_results, metadata):        
    # extract arxiv_id 
    arxiv_ids = []
    for sr in search_results:
        # Skip results with errors or missing URL
        if 'error' in sr or 'url' not in sr:
            continue
        url_part = sr['url'].split('/')[-1]  # Get '2601.04252v1'
        arxiv_id = url_part.split('v')[0]     # Get '2601.04252'
        if arxiv_id:
            arxiv_ids.append(arxiv_id)

    for r in metadata["recommendations"]:
        arxiv_id = r.get("arxivId")
        if arxiv_id:
            arxiv_ids.append(arxiv_id)

    return arxiv_ids


async def extract_markdown(paper_id):
    cached_markdown = load_markdown(paper_id)
    if not cached_markdown:
        arxiv_url = f"https://arxiv.org/abs/{paper_id}"
        result = await download_and_parse_paper(arxiv_url)
        if result.get("success") and result.get("markdown"):
            save_markdown(paper_id, result["markdown"])
            return result["markdown"]
        else:
            return None
    return cached_markdown

async def analyze_deeply(root_paper_arxiv_id: str) -> Optional[Dict[str, Any]]:
    base_article_analysis = load_analysis(root_paper_arxiv_id)    
    analysis_object: PaperAnalysis = PaperAnalysis.model_validate(base_article_analysis["data"])
    application_ideas = analysis_object.summary.applications
    model_id = "gpt-5-mini"
    csv_rows = []
    
    for application_idea in application_ideas:
        print(f"Started analysis for: {application_idea}")
        search_results = arxiv_search_tool(application_idea.domain, 10)
        metadata = load_metadata(root_paper_arxiv_id)
        arxiv_ids = extract_arxiv_ids(search_results, metadata)
        arxiv_ids.append(root_paper_arxiv_id)
        async def process_paper(paper_id: str):        
            related_paper_metadata = load_metadata(paper_id)            
            if not related_paper_metadata:
                related_paper_metadata = await get_paper_metadata(paper_id)
                if not related_paper_metadata["success"]:
                    related_paper_metadata = None                

            if related_paper_metadata:
                relevancy = await is_paper_relevant(application_idea, related_paper_metadata["title"], related_paper_metadata["abstract"], model_id)
                
                # Record to CSV data
                csv_rows.append({
                    'application_context': application_idea.specific_utility,
                    'related_paper_title': related_paper_metadata["title"],
                    'related_paper_summary': related_paper_metadata["abstract"],
                    'relevancy_decision': relevancy["decision"],
                    'relevancy_reasoning': relevancy.get("reason", ""),
                    'model_id': model_id
                })
                
                if relevancy["decision"]:
                    cached_analysis = load_analysis(paper_id)
                    return cached_analysis
                    # if not cached_analysis:
                    #     try:
                    #         markdown = extract_markdown(paper_id)
                    #         analysis = summarize_paper(markdown)


                    #     except Exception as e:
                    #         return f"Failed {paper_id}: {e}"
        
        tasks = [process_paper(pid) for pid in arxiv_ids]
        results = await asyncio.gather(*tasks)
        print(f"Processing comleted, found {len(results)} cached analysis.")
    
    # Write CSV file
    if csv_rows:
        results_dir = Path(__file__).parent.parent / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = results_dir / f"relevancy_analysis_{root_paper_arxiv_id}_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['application_context', 'related_paper_title', 'related_paper_summary', 
                         'relevancy_decision', 'relevancy_reasoning', 'model_id']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        print(f"CSV results saved to: {csv_file}")
        

if __name__ == "__main__":
    
    asyncio.run(analyze_deeply("2601.21558"))