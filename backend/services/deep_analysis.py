from typing import Optional, Dict, Any

from cache_service import load_analysis, load_metadata, load_markdown, save_markdown, save_metadata
from some_extensions.research_tools import arxiv_search_tool
from semantic_scholar import get_paper_metadata
from openai_service import is_paper_relevant
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
        arxiv_ids.append(arxiv_id)

    for r in metadata["recommendations"]:
        arxiv_id = r["arxivId"]
        arxiv_ids.append(arxiv_id)

    return arxiv_ids

async def analyze_deeply(arxiv_id: str) -> Optional[Dict[str, Any]]:
    base_article_analysis = load_analysis(arxiv_id)    
    applications = base_article_analysis['data']['summary']['applications']
    application_context = applications[0]
    search_results = arxiv_search_tool(application_context, 10)
    metadata = load_metadata(arxiv_id)
    arxiv_ids = extract_arxiv_ids(search_results, metadata)
     
    async def process_paper(paper_id: str):
        arxiv_url = f"https://arxiv.org/abs/{paper_id}"
        related_paper_metadata = load_metadata(arxiv_id)
        if related_paper_metadata:
            relevancy = await is_paper_relevant(application_context, related_paper_metadata["title"], related_paper_metadata["abstract"])
            print(relevancy["decision"])
            print(relevancy["reason"])
        # try:
        #     cached_markdown = load_markdown(paper_id)
        #     if not cached_markdown:
        #         result = await download_and_parse_paper(arxiv_url)
        #         if result.get("success") and result.get("markdown"):
        #             save_markdown(paper_id, result["markdown"])
        #             return f"Saved {paper_id}"
        #     else:
        #         return f"Loaded markdown from cache for {paper_id}"
        # except Exception as e:
        #     return f"Failed {paper_id}: {e}"
    
    tasks = [process_paper(pid) for pid in arxiv_ids]
    results = await asyncio.gather(*tasks)
    # print(results)
    print(f"Downloaded {len(results)} markdowns for papers.")

if __name__ == "__main__":
    
    asyncio.run(analyze_deeply("2601.17058"))