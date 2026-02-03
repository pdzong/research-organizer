# Applications View - Complete Guide

## Overview

The Research Agent now has a **dedicated Applications View** where you can browse, manage, and explore all saved applications. This view provides an organized way to see applications alongside their source papers and related research.

## Features

### 🔀 View Switching

At the top of the page, you'll see a segmented control to switch between views:

```
┌─────────────────────────────────────────┐
│  📄 Papers  |  💡 Applications         │
└─────────────────────────────────────────┘
```

- **Papers View**: Browse and analyze research papers
- **Applications View**: Browse and explore saved applications

### 📋 Applications List

When you switch to the Applications view, you'll see a list of all saved applications:

```
┌─────────────────────────────────────────────────────┐
│ Saved Applications                                  │
│ 3 applications saved                                │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 💡 Enterprise tool agents    Jan 15, 2026   │   │
│ │                                             │   │
│ │ Improves multi-turn business workflow       │   │
│ │ automation by synthesizing...               │   │
│ │                                             │   │
│ │ 📄 ASTRA: Automated Synthesis...            │   │
│ │ 🔵 10 related papers                        │   │
│ │                                             │   │
│ │           [View Details]                    │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

Each card shows:
- **Domain badge** (cyan color with bulb icon)
- **Date added**
- **Brief description** (first 2 lines)
- **Source paper** (truncated title)
- **Number of related papers**
- **View Details button**

### 🔍 Application Detail View

Click on any application or "View Details" to see the full details:

#### 1. Application Header
```
┌─────────────────────────────────────────────────────┐
│ 💡 Enterprise tool agents     Added Jan 15, 2026   │
│                                                     │
│ Application Description                             │
│ Improves multi-turn business workflow automation    │
│ by synthesizing tool-call trajectories from an      │
│ organization's API topology and then hardening      │
│ behavior via verifiable RL in executable arenas.    │
└─────────────────────────────────────────────────────┘
```

#### 2. Source Paper Section
Shows the paper where this application came from:

```
┌─────────────────────────────────────────────────────┐
│ 📄 Source Paper                                     │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ ASTRA: Automated Synthesis of agentic       │   │
│ │ Trajectories and Reinforcement Arenas       │   │
│ │                                             │   │
│ │ 👥 Xiaoyu Tian, Haotian Wang, Shuaiting... │   │
│ │                                             │   │
│ │ 📋 ArXiv: 2601.21558  [View on ArXiv →]    │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### 3. Related Papers Section
Shows all recommended papers that were saved with this application:

```
┌─────────────────────────────────────────────────────┐
│ 📄 Related Papers                    10 papers     │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 1. AutoTool: Dynamic Tool Selection and     │   │
│ │    Integration for Agentic Reasoning        │   │
│ │ 👥 Jiaru Zou, Ling Yang, Yunzhe Qi...      │   │
│ │ 📋 ArXiv: 2512.13278         [View →]      │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 2. Close the Loop: Synthesizing Infinite... │   │
│ │ 👥 Yuwen Li, Wei Zhang, Ze-Jun Huang...    │   │
│ │ 📋 ArXiv: 2512.23611         [View →]      │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### 4. Metadata Footer
Shows additional metadata:
- Application ID (timestamp)
- Total papers referenced (source + related)

## Usage Workflow

### Step 1: Save an Application
1. Navigate to **Papers View**
2. Select and analyze a paper
3. Click **"Add to List"** on any application
4. Application is saved with current paper + all related papers

### Step 2: Browse Applications
1. Click the **"Applications"** tab at the top
2. See all saved applications in a card layout
3. Each card shows key info at a glance

### Step 3: View Details
1. Click on any application card or "View Details"
2. See complete information including:
   - Full application description
   - Source paper details with ArXiv link
   - All related papers with ArXiv links
   - Metadata and timestamps

### Step 4: Navigate
- Click **"Back to Applications"** to return to the list
- Switch to **"Papers"** tab to go back to papers view
- All state is preserved when switching views

## UI Components Breakdown

### ApplicationList Component
- **Empty State**: Shows when no applications saved yet
- **Card Grid**: Displays applications in a clean card layout
- **Selection Highlight**: Selected card has blue border
- **Click-to-View**: Click anywhere on card to view details

### ApplicationDetail Component
- **Back Button**: Returns to applications list
- **Structured Layout**: Clear sections for each type of info
- **External Links**: Direct links to ArXiv for all papers
- **Author Display**: Shows all authors with icons
- **Metadata Panel**: Summary info at the bottom

### Layout Component
- **View Toggle**: Segmented control with icons
- **Persistent Header**: Always visible navigation
- **Smooth Transitions**: Clean switching between views

## Color Scheme

- **Cyan/Blue**: Application badges and primary actions
- **Gray**: Metadata and secondary info
- **Light Blue**: Background highlights for papers
- **Light Gray**: Related paper cards

## Icons Used

- 💡 **IconBulb**: Applications and domain badges
- 📄 **IconFileText**: Papers and documents
- 👥 **IconUsers**: Authors
- 📅 **IconCalendar**: Dates
- ↖ **IconArrowLeft**: Back navigation
- 🔗 **IconExternalLink**: External links to ArXiv

## Data Structure

Each application entry contains:

```typescript
{
  id: string;              // Unique timestamp-based ID
  application: {
    domain: string;        // Application domain/category
    specific_utility: string; // Detailed description
  };
  current_paper: {
    title: string;
    authors: string[];
    arxiv_id?: string;
  };
  related_papers: [{
    title: string;
    authors: string[];
    arxiv_id?: string;
  }];
  added_at: string;        // ISO timestamp
}
```

## API Endpoints

### GET `/api/applications`
Fetches all saved applications

**Response:**
```json
{
  "success": true,
  "applications": [/* array of ApplicationEntry */],
  "error": null
}
```

## Keyboard & Navigation

- Click application cards to view details
- Click "Back to Applications" to return to list
- Switch views using the segmented control
- External links open in new tabs (ArXiv)

## Tips & Best Practices

✅ **Save Related Applications**: Save multiple applications from the same paper to compare use cases

✅ **Use Descriptive Domains**: The domain badge is the main identifier in the list view

✅ **Browse Related Papers**: Click ArXiv links to explore related research

✅ **Track by Date**: Use the "Added" date to see when you saved each application

✅ **Empty State Guidance**: If no applications saved yet, the UI guides you to add some from papers

## Future Enhancements (Planned)

- 🔍 Search and filter applications by domain or keywords
- 🏷️ Add custom tags to applications
- 📊 Group applications by domain or paper
- 📤 Export applications to various formats (CSV, JSON, PDF)
- ✏️ Edit application descriptions
- 🗑️ Delete unwanted applications
- 📈 Analytics: most common domains, paper references, etc.
- 🔗 Quick navigation from application back to source paper

## Technical Details

### Frontend Components
- `ApplicationList.tsx`: List view component
- `ApplicationDetail.tsx`: Detail view component
- `Layout.tsx`: Updated with view switcher
- `App.tsx`: View state management

### Backend Services
- `GET /api/applications`: Fetch all applications
- `cache_service.load_applications()`: Load from JSON file
- Data stored in: `backend/data/cache/applications.json`

### State Management
- `currentView`: 'papers' | 'applications'
- `selectedApplication`: Currently viewed application
- `applications`: Array of all applications
- Automatic state reset when switching views
