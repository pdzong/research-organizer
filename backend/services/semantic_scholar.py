from semanticscholar import SemanticScholar
from typing import Optional, Dict, Any, List
import asyncio

sch = SemanticScholar()

def _extract_arxiv_id(external_ids: Dict[str, Any]) -> Optional[str]:
    """Extract ArXiv ID from external IDs if available."""
    if external_ids and 'ArXiv' in external_ids:
        return external_ids['ArXiv']
    return None

def _format_related_paper(paper) -> Optional[Dict[str, Any]]:
    """Format a related paper object into a simple dict."""
    if not paper:
        return None
    
    try:
        external_ids = paper.externalIds if hasattr(paper, 'externalIds') else {}
        arxiv_id = _extract_arxiv_id(external_ids)
        
        return {
            "paperId": paper.paperId if hasattr(paper, 'paperId') else None,
            "title": paper.title if hasattr(paper, 'title') else None,
            "year": paper.year if hasattr(paper, 'year') else None,
            "authors": [
                {
                    "authorId": getattr(author, 'authorId', None),
                    "name": getattr(author, 'name', None),
                }
                for author in (paper.authors or [])
            ] if hasattr(paper, 'authors') and paper.authors else [],
            "citationCount": paper.citationCount if hasattr(paper, 'citationCount') else 0,
            "influentialCitationCount": paper.influentialCitationCount if hasattr(paper, 'influentialCitationCount') else 0,
            "referenceCount": paper.referenceCount if hasattr(paper, 'referenceCount') else 0,
            "url": paper.url if hasattr(paper, 'url') else None,
            "arxivId": arxiv_id,
            "externalIds": external_ids,
        }
    except Exception as e:
        print(f"Error formatting related paper: {e}")
        return None

async def get_paper_metadata(arxiv_id: str, include_related: bool = True) -> Dict[str, Any]:
    """
    Fetch paper metadata from Semantic Scholar using ArXiv ID.
    
    Args:
        arxiv_id: The ArXiv ID (e.g., "1706.03762")
        include_related: Whether to fetch citations and recommendations (default: True)
    
    Returns:
        dict with metadata or error
    """
    try:
        # Run the blocking API call in a thread pool
        loop = asyncio.get_event_loop()
        paper = await loop.run_in_executor(
            None, 
            sch.get_paper, 
            f"ARXIV:{arxiv_id}"
        )
        
        if not paper:
            return {
                "success": False,
                "error": f"Paper not found in Semantic Scholar for ArXiv ID: {arxiv_id}"
            }
        
        # Extract relevant metadata
        metadata = {
            "success": True,
            "paperId": paper.paperId if hasattr(paper, 'paperId') else None,
            "title": paper.title if hasattr(paper, 'title') else None,
            "abstract": paper.abstract if hasattr(paper, 'abstract') else None,
            "year": paper.year if hasattr(paper, 'year') else None,
            "publicationDate": str(paper.publicationDate) if hasattr(paper, 'publicationDate') and paper.publicationDate else None,
            "citationCount": paper.citationCount if hasattr(paper, 'citationCount') else 0,
            "referenceCount": paper.referenceCount if hasattr(paper, 'referenceCount') else 0,
            "influentialCitationCount": paper.influentialCitationCount if hasattr(paper, 'influentialCitationCount') else 0,
            "isOpenAccess": paper.isOpenAccess if hasattr(paper, 'isOpenAccess') else False,
            "fieldsOfStudy": paper.fieldsOfStudy if hasattr(paper, 'fieldsOfStudy') else [],
            "s2FieldsOfStudy": [
                {
                    "category": getattr(field, 'category', None) if hasattr(field, 'category') else field.get('category') if isinstance(field, dict) else None,
                    "source": getattr(field, 'source', None) if hasattr(field, 'source') else field.get('source') if isinstance(field, dict) else None
                }
                for field in (paper.s2FieldsOfStudy or [])
            ] if hasattr(paper, 's2FieldsOfStudy') and paper.s2FieldsOfStudy else [],
            "publicationTypes": paper.publicationTypes if hasattr(paper, 'publicationTypes') else [],
            "publicationVenue": {
                "name": paper.publicationVenue.name if hasattr(paper.publicationVenue, 'name') else None,
                "type": paper.publicationVenue.type if hasattr(paper.publicationVenue, 'type') else None,
                "url": paper.publicationVenue.url if hasattr(paper.publicationVenue, 'url') else None,
            } if hasattr(paper, 'publicationVenue') and paper.publicationVenue else None,
            "journal": {
                "name": paper.journal.name if hasattr(paper.journal, 'name') else None,
                "volume": paper.journal.volume if hasattr(paper.journal, 'volume') else None,
                "pages": paper.journal.pages if hasattr(paper.journal, 'pages') else None,
            } if hasattr(paper, 'journal') and paper.journal else None,
            "authors": [
                {
                    "authorId": getattr(author, 'authorId', None),
                    "name": getattr(author, 'name', None),
                    "url": getattr(author, 'url', None)
                }
                for author in (paper.authors or [])
            ] if hasattr(paper, 'authors') and paper.authors else [],
            "venue": paper.venue if hasattr(paper, 'venue') else None,
            "openAccessPdf": paper.openAccessPdf if hasattr(paper, 'openAccessPdf') else None,
            "externalIds": paper.externalIds if hasattr(paper, 'externalIds') else {},
            "url": paper.url if hasattr(paper, 'url') else None,
            "tldr": paper.tldr.text if hasattr(paper, 'tldr') and paper.tldr and hasattr(paper.tldr, 'text') else None,
            "corpusId": paper.corpusId if hasattr(paper, 'corpusId') else None,
        }
        
        # Fetch related papers if requested
        if include_related:
            try:
                # Get citations (papers that cite this one) - limit to 10
                citations = paper.citations if hasattr(paper, 'citations') else []
                if citations:
                    metadata["citations"] = [
                        _format_related_paper(cite) for cite in citations[:10]
                        if _format_related_paper(cite) is not None
                    ]
                else:
                    metadata["citations"] = []
                
                # Get recommendations - limit to 10
                paper_id = paper.paperId if hasattr(paper, 'paperId') else None
                if paper_id:
                    recommendations = await loop.run_in_executor(
                        None,
                        sch.get_recommended_papers,
                        paper_id
                    )
                    if recommendations:
                        metadata["recommendations"] = [
                            _format_related_paper(rec) for rec in recommendations[:10]
                            if _format_related_paper(rec) is not None
                        ]
                    else:
                        metadata["recommendations"] = []
                else:
                    metadata["recommendations"] = []
                    
            except Exception as e:
                print(f"Error fetching related papers for {arxiv_id}: {e}")
                metadata["citations"] = []
                metadata["recommendations"] = []
        else:
            metadata["citations"] = []
            metadata["recommendations"] = []
        
        return metadata
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "citations": [],
            "recommendations": []
        }
