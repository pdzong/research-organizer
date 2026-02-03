# Application Management UI Guide

## How to Use the New "Add to List" Feature

### Step-by-Step Guide

1. **Open the Research Agent UI** at http://localhost:5173/

2. **Select a paper** from the list

3. **Load the paper content** by clicking "Load Paper Content"

4. **Analyze the paper** by clicking "Analyze Paper"

5. **Scroll down** to the "Paper Summary" section with the blue background

6. **Find "Real-World Applications"** - this section shows all the applications from the paper

7. **Each application now has an "Add to List" button** in the top-right corner:

```
┌─────────────────────────────────────────────────────────┐
│ Paper Summary                                           │
│                                                         │
│ Real-World Applications                                 │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 💡 Enterprise tool agents   [Add to List] ←──── │   │
│ │                                                 │   │
│ │ Improves multi-turn business workflow          │   │
│ │ automation by synthesizing tool-call           │   │
│ │ trajectories from an organization's API...     │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 💡 Customer support        [Add to List] ←──── │   │
│ │                                                 │   │
│ │ Enables robust multi-turn resolution by...     │   │
│ └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

8. **Click "Add to List"** on any application you want to save

9. **Success notification** will appear in the top-right corner confirming the application was saved

### What Happens When You Click "Add to List"

The system automatically:

✅ Saves the **application data** (domain + specific utility)
✅ Saves the **current paper** info (title, authors, ArXiv ID)
✅ Saves **all papers** from "Recommended Related Papers" section
✅ Stores everything in `backend/data/cache/applications.json`

### Viewing Saved Applications

The applications are saved in JSON format at:
```
backend/data/cache/applications.json
```

You can open this file to see all your saved applications. Each entry includes:
- Application domain and utility
- The paper it came from
- All related papers that were recommended

### Example Saved Entry

```json
{
  "id": "2026-02-03T14:30:00.123Z",
  "application": {
    "domain": "Enterprise tool agents / API orchestration",
    "specific_utility": "Improves multi-turn business workflow automation..."
  },
  "current_paper": {
    "title": "ASTRA: Automated Synthesis of agentic Trajectories...",
    "authors": ["Xiaoyu Tian", "Haotian Wang", "..."],
    "arxiv_id": "2601.21558"
  },
  "related_papers": [
    {
      "title": "Related Paper 1",
      "authors": ["Author A", "Author B"],
      "arxiv_id": "1234.56789"
    }
  ],
  "added_at": "2026-02-03T14:30:00.123Z"
}
```

## Tips

- 💡 The button only appears for **structured applications** (domain + specific_utility format)
- 💡 Old-style string applications won't have the button (backward compatibility)
- 💡 Make sure to **load metadata** first by selecting a paper - this ensures related papers are available
- 💡 The system automatically includes **all** recommended papers from Semantic Scholar

## Button Styling

- **Color**: Cyan (matches the application badge color)
- **Size**: Extra small (xs) to fit nicely in the corner
- **Icon**: Plus icon (IconPlus) indicating "add" action
- **Variant**: Light (subtle, not overwhelming)

## Success Notification

After clicking "Add to List", you'll see:

```
┌─────────────────────────────────────┐
│ ✓ Success                           │
│                                     │
│ Application 'Enterprise tool        │
│ agents / API orchestration'         │
│ saved successfully                  │
└─────────────────────────────────────┘
```

## Future View Applications Feature (Coming Soon)

The saved applications can be used to build:
- An "Applications Library" page
- Search and filter by domain
- Group applications by use case
- Export to different formats
- Link back to source papers
