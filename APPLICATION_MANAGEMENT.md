# Application Management System

## Overview

This document describes the new application management feature that allows you to save real-world applications from paper analyses along with the current paper and all recommended related papers.

## Features

### 1. Add to List Button for Applications

- Each application in the "Real-World Applications" section now has an "Add to List" button
- Clicking the button saves the application data to `applications.json` in the cache directory

### 2. Data Storage Structure

Applications are stored in `backend/data/cache/applications.json` with the following structure:

```json
[
  {
    "id": "2026-02-03T12:34:56.789Z",
    "application": {
      "domain": "Enterprise tool agents / API orchestration",
      "specific_utility": "Improves multi-turn business workflow automation by synthesizing tool-call trajectories from an organization's API topology and then hardening behavior via verifiable RL in executable arenas."
    },
    "current_paper": {
      "title": "ASTRA: Automated Synthesis of agentic Trajectories and Reinforcement Arenas",
      "authors": ["Xiaoyu Tian", "Haotian Wang", "Shuaiting Chen", "Hao Zhou", "Kaichi Yu"],
      "arxiv_id": "2601.21558"
    },
    "related_papers": [
      {
        "title": "Related Paper Title 1",
        "authors": ["Author 1", "Author 2"],
        "arxiv_id": "1234.56789"
      },
      {
        "title": "Related Paper Title 2",
        "authors": ["Author 3", "Author 4"],
        "arxiv_id": "9876.54321"
      }
    ],
    "added_at": "2026-02-03T12:34:56.789Z"
  }
]
```

### 3. What Gets Saved

When you click "Add to List" on an application, the system saves:

1. **Application Data**:
   - `domain`: The domain/category of the application
   - `specific_utility`: Detailed description of the specific utility

2. **Current Paper**: Simple view containing:
   - Title
   - Authors
   - ArXiv ID (if available)

3. **Related Papers**: All papers from the "Recommended Related Papers" section, each containing:
   - Title
   - Authors
   - ArXiv ID (if available)

4. **Metadata**:
   - Unique ID (timestamp-based)
   - Added timestamp

## Backend Changes

### New Files/Modifications

1. **`backend/routers/papers.py`**
   - Added `SimplePaperInfo` model
   - Added `AddApplicationRequest` model
   - Added `AddApplicationResponse` model
   - Added `POST /applications/add` endpoint

2. **`backend/services/cache_service.py`**
   - Added `APPLICATIONS_FILE` constant
   - Added `save_application()` function to manage applications.json

## Frontend Changes

### New Files/Modifications

1. **`web_ui/src/services/api.ts`**
   - Added `SimplePaperInfo` interface
   - Added `AddApplicationRequest` interface
   - Added `AddApplicationResponse` interface
   - Added `addApplication()` API function

2. **`web_ui/src/App.tsx`**
   - Added `handleAddApplication()` handler
   - Passes `onAddApplication` prop to `PaperDetail` component

3. **`web_ui/src/components/PaperDetail.tsx`**
   - Added `onAddApplication` to component props
   - Added "Add to List" button for each application
   - Automatically collects all recommended related papers when adding an application

## Usage

1. **Navigate to a paper** in the Research Agent UI
2. **Load Paper Content** and **Analyze Paper** to see the analysis
3. **Scroll to "Real-World Applications"** section
4. **Click "Add to List"** next to any application you want to save
5. **Success notification** will appear confirming the application was saved
6. **Check** `backend/data/cache/applications.json` to see the saved applications

## API Endpoint Details

### POST `/api/applications/add`

**Request Body:**
```json
{
  "application": {
    "domain": "string",
    "specific_utility": "string"
  },
  "current_paper": {
    "title": "string",
    "authors": ["string"],
    "arxiv_id": "string (optional)"
  },
  "related_papers": [
    {
      "title": "string",
      "authors": ["string"],
      "arxiv_id": "string (optional)"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Application 'domain name' saved successfully",
  "error": null
}
```

## Future Enhancements

Potential improvements that could be added:

1. **View Applications Page**: Create a dedicated UI to browse saved applications
2. **Search & Filter**: Search applications by domain or keywords
3. **Export**: Export applications to various formats (CSV, PDF, etc.)
4. **Edit/Delete**: Allow editing or deleting saved applications
5. **Grouping**: Group applications by domain or paper
6. **Tags**: Add custom tags to applications for better organization
