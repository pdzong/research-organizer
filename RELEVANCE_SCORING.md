# Relevance Scoring for Related Papers

## Overview

The Research Agent now displays **Citations** and **Recommendations** with visual indicators showing their relevance/importance. Papers are color-coded using a gradient system based on metrics from **Semantic Scholar**.

## 🔥 Visual Indicators

### Color Gradient System

Papers are displayed with background colors and border styles that indicate their relevance:

| Relevance Level | Score Range | Background | Border | Icon |
|-----------------|-------------|------------|--------|------|
| **Highly Relevant** | 70-100 | Light Gold | Gold (2px) | 🔥 Flame |
| **Very Relevant** | 50-69 | Very Light Yellow | Yellow (2px) | 📈 Trending |
| **Relevant** | 30-49 | Very Light Blue | Blue (1px) | - |
| **Related** | 0-29 | Transparent | Gray (1px) | - |

Papers with scores ≥50 have **thicker borders** (2px) to make them more prominent.

## 📊 Relevance Scoring Algorithm

The relevance score (0-100) is calculated using **Semantic Scholar's own metrics** - no custom or arbitrary values:

### For Citations (Papers Citing This Work)

```
Score = citationScore + influenceScore

Where:
- citationScore = min(50, log10(citationCount + 1) × 10)
  • Uses logarithmic scale for citation count
  • Capped at 50 points
  
- influenceScore = (influentialCitationCount / citationCount) × 30
  • Ratio of influential citations (Semantic Scholar's proprietary metric)
  • Up to 30 points for highly influential papers
```

### For Recommendations

```
Score = citationScore + influenceScore + positionBonus

Where:
- citationScore = same as above
- influenceScore = same as above
- positionBonus = max(0, (10 - index) × 2)
  • Semantic Scholar orders recommendations by relevance
  • Earlier positions get a bonus (up to 20 points)
  • First paper: +20 points, Second: +18, Third: +16, etc.
```

## 🎯 Semantic Scholar Metrics Used

### 1. Citation Count
- Total number of times the paper has been cited
- Standard academic impact metric

### 2. **Influential Citation Count** ⭐
- **Semantic Scholar's proprietary algorithm** for determining high-quality citations
- Not all citations are equal - some are more impactful
- A paper cited 100 times with 50 influential citations is more significant than one cited 100 times with 5 influential citations
- This is the key differentiator for relevance

### 3. Reference Count
- Number of papers this paper cites
- Available in the data but not currently used in scoring
- Could be used for future enhancements

### 4. Recommendation Position
- Semantic Scholar's recommendation algorithm already ranks papers by relevance
- Papers appearing earlier in the list are considered more relevant

## 💡 Why This Matters

### Making Important Papers Stand Out

Instead of manually scrolling through dozens of related papers, you can now:
- **Quickly spot highly influential papers** with gold backgrounds and flame icons
- **See which citations matter most** through the influential citation badges
- **Trust Semantic Scholar's expertise** - using their battle-tested algorithms rather than custom heuristics

### Use Cases

1. **Literature Review**: Focus on highly relevant papers first (gold/yellow cards)
2. **Finding Key Papers**: Papers with many influential citations are likely seminal works
3. **Research Direction**: Recommendations at the top with high scores point to the most related work

## 🔧 Technical Details

### Backend Changes

**`backend/services/semantic_scholar.py`:**
- Added `influentialCitationCount` to `_format_related_paper()`
- Now fetches this metric for all citations and recommendations

### Frontend Changes

**`frontend/src/services/api.ts`:**
- Updated `RelatedPaper` interface with new fields

**`frontend/src/components/PaperDetail.tsx`:**
- Added `calculateRelevanceScore()` function
- Added `getRelevanceVisuals()` for color/icon mapping
- Updated Citations and Recommendations sections with:
  - Background color gradients
  - Border styling (1px or 2px)
  - Relevance icons with tooltips
  - "Influential" citation badges with explanations

### Icons

- 🔥 **Flame** (`IconFlame`): Highly Relevant (score ≥ 70)
- 📈 **Trending** (`IconTrendingUp`): Very Relevant (50-69)
- 💡 **Tooltip**: Hover over icons to see exact relevance score

## 📈 Example Scoring

### Example 1: Highly Influential Paper
```
citationCount: 500
influentialCitationCount: 250
position: 1 (recommendation)

citationScore = min(50, log10(501) × 10) = 50 (capped)
influenceScore = (250/500) × 30 = 15
positionBonus = (10-0) × 2 = 20

Total Score = 50 + 15 + 20 = 85 ✨ HIGHLY RELEVANT (Gold)
```

### Example 2: Moderately Cited Paper
```
citationCount: 50
influentialCitationCount: 10
position: 5 (recommendation)

citationScore = log10(51) × 10 = 17
influenceScore = (10/50) × 30 = 6
positionBonus = (10-4) × 2 = 12

Total Score = 17 + 6 + 12 = 35 📊 RELEVANT (Light Blue)
```

### Example 3: Lower Impact Paper
```
citationCount: 5
influentialCitationCount: 1
position: N/A (citation)

citationScore = log10(6) × 10 = 7.8
influenceScore = (1/5) × 30 = 6
positionBonus = 0

Total Score = 7.8 + 6 = 13.8 📄 RELATED (Gray)
```

## 🎨 User Experience

### Badges Displayed

Each paper card now shows:
- **Year**: Publication year
- **Citations**: Total citation count (blue badge)
- **Influential**: Influential citation count (orange badge with tooltip) ⭐ NEW
- **ArXiv ID**: If available (green badge)

### Tooltips

- Hover over 🔥/📈 icons to see the exact relevance score
- Hover over "influential" badges to see Semantic Scholar's explanation

## 🚀 Future Enhancements

Possible improvements:
1. **Sortable lists**: Allow sorting by relevance score
2. **Filter by score**: Show only papers above a certain threshold
3. **Score explanation**: Show detailed score breakdown on hover
4. **Custom weights**: Allow users to adjust the scoring formula
5. **Reference count integration**: Use reference count as an additional signal

---

**Note**: All relevance metrics are based on **Semantic Scholar's own data and algorithms**. We're leveraging their expertise rather than creating arbitrary scoring mechanisms.
