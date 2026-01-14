from semanticscholar import SemanticScholar
from typing import Optional, Dict, Any
import asyncio

sch = SemanticScholar()

async def get_paper_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Fetch paper metadata from Semantic Scholar using ArXiv ID.
    
    Args:
        arxiv_id: The ArXiv ID (e.g., "1706.03762")
    
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
        
        return metadata
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
