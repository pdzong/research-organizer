"""
Test script for paper sections extraction and analysis flow
"""
import asyncio
from services import cache_service
from services.openai_service import extract_paper_sections, summarize_paper
from services.models import PaperSections

async def test_sections_flow():
    """Test the complete sections extraction and analysis flow"""
    
    print("=" * 60)
    print("Testing Paper Sections Flow")
    print("=" * 60)
    
    # Test paper ID (use an existing cached paper)
    test_arxiv_id = "1706.03762"  # Attention Is All You Need
    
    print(f"\n1. Checking cache status for {test_arxiv_id}...")
    status = cache_service.get_cache_status(test_arxiv_id)
    print(f"   Cache status: {status}")
    
    if not status['markdown']:
        print(f"\n⚠️  Paper {test_arxiv_id} not in cache.")
        print("   Please load the paper first via the frontend or API.")
        return
    
    print(f"\n2. Loading markdown from cache...")
    markdown = cache_service.load_markdown(test_arxiv_id)
    if markdown:
        print(f"   ✅ Loaded markdown ({len(markdown)} chars)")
    else:
        print("   ❌ Failed to load markdown")
        return
    
    print(f"\n3. Testing section extraction...")
    try:
        sections: PaperSections = await extract_paper_sections(markdown)
        print(f"   ✅ Extracted sections:")
        print(f"      Title: {sections.title}")
        print(f"      GitHub: {sections.github_url or 'Not found'}")
        print(f"      Abstract: {len(sections.abstract_text)} chars")
        print(f"      Introduction: {len(sections.introduction_text)} chars")
        print(f"      Methodology: {len(sections.methodology_text)} chars")
        print(f"      Experiments: {len(sections.experiments_text)} chars")
        print(f"      Conclusion: {len(sections.conclusion_text)} chars")
        
        # Save to cache
        sections_dict = sections.model_dump()
        cache_service.save_sections(test_arxiv_id, sections_dict)
        print(f"\n   ✅ Saved sections to cache")
        
    except Exception as e:
        print(f"   ❌ Section extraction failed: {e}")
        return
    
    print(f"\n4. Testing clean markdown generation...")
    clean_markdown = sections.to_clean_markdown()
    print(f"   ✅ Generated clean markdown ({len(clean_markdown)} chars)")
    print(f"   Token reduction: {len(markdown)} → {len(clean_markdown)} chars")
    print(f"   Savings: {((len(markdown) - len(clean_markdown)) / len(markdown) * 100):.1f}%")
    
    print(f"\n5. Preview of clean markdown (first 500 chars):")
    print("   " + "-" * 56)
    print("   " + clean_markdown[:500].replace('\n', '\n   '))
    print("   " + "-" * 56)
    
    print(f"\n6. Testing analysis with clean markdown...")
    response = input("\n   Run full analysis? This will use OpenAI API (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            print("   🤖 Running analysis...")
            result = await summarize_paper(clean_markdown)
            
            if result.get('success'):
                print(f"   ✅ Analysis successful!")
                print(f"      Model: {result['usage']['model']}")
                print(f"      Input tokens: {result['usage']['input_tokens']}")
                print(f"      Output tokens: {result['usage']['output_tokens']}")
                
                data = result['data']
                print(f"\n   📊 Analysis Preview:")
                print(f"      Title: {data['paper_title']}")
                print(f"      Main Contribution: {data['summary']['main_contribution'][:100]}...")
                print(f"      Benchmarks found: {len(data['benchmarks'])}")
                print(f"      Applications found: {len(data['summary']['applications'])}")
            else:
                print(f"   ❌ Analysis failed: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
    else:
        print("   ⏭️  Skipped analysis")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sections_flow())
