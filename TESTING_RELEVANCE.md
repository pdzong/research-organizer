# Testing the Relevance Scoring Feature

## 🔍 Quick Test Steps

### Step 1: Check for the Info Banner

1. Open any paper in your list
2. Scroll down to **"Papers Citing This Work"** or **"Recommended Related Papers"**
3. **Look for a blue info banner** that says: *"New Feature Available - Click 'Reload' above to see relevance-based color highlighting for these papers!"*

**If you see this banner:** Your cached metadata doesn't have the new fields yet. Click the **"Reload"** button at the top of the metadata section.

### Step 2: Reload Metadata

1. Click the **"Reload"** button next to "Paper Metadata"
2. Wait for the metadata to reload (this fetches fresh data from Semantic Scholar)
3. The citations and recommendations will now have the new `influentialCitationCount` field

### Step 3: Check Browser Console

1. Open your browser's Developer Tools (F12)
2. Go to the **Console** tab
3. Look for debug messages like:
   ```
   Citation example: {
     title: "...",
     citationCount: 100,
     influentialCount: 25,
     relevanceScore: 65,
     visuals: { bgColor: "rgba(255, 245, 204, 0.2)", borderColor: "#ffe066", label: "Very Relevant" }
   }
   ```

This shows you exactly what data is being used and what styling should apply.

### Step 4: Look for Visual Indicators

After reloading metadata, you should see:

1. **Background Colors**:
   - Gold/yellow tinted backgrounds on high-relevance papers
   - Light blue on moderate relevance
   - Default white/gray on lower relevance

2. **Icons**:
   - 🔥 **Flame icon** (gold background) = Score 70-100
   - 📈 **Trending icon** (yellow background) = Score 50-69
   - No icon for scores below 50

3. **Borders**:
   - **Thicker borders (2px)** on papers with score ≥50
   - Regular borders on others

4. **"Influential" Badges**:
   - Orange badges showing influential citation counts
   - Tooltip explains "Citations deemed influential by Semantic Scholar's algorithm"

## 🐛 Troubleshooting

### "I still don't see any colors"

**Possible reasons:**

1. **The papers have low citation counts** - Papers with very few citations will have low relevance scores
   - Try a highly-cited paper like "Attention Is All You Need" (ArXiv: 1706.03762)
   - This paper should have many citations with high influential counts

2. **Cached data** - Make sure you clicked "Reload" after updating the code

3. **Check console for errors** - Look for any red errors in the browser console (F12)

### "The info banner appears but won't go away"

This means the data still doesn't have the new fields. Try:
1. Clear your browser cache (Ctrl+Shift+Delete)
2. Restart the backend server
3. Click "Reload" again

### "All papers look the same"

If a paper doesn't have many highly-cited citing papers, they might all have similar low scores. Try:
1. Select a very famous paper (BERT, GPT, Transformer, ResNet)
2. These will have more diverse citations with varying impact levels

## 📊 Example Papers to Test

Try these famous papers to see the color gradients:

1. **"Attention Is All You Need"** (ArXiv: 1706.03762)
   - Thousands of citations
   - Many influential citations
   - Should show clear color gradients

2. **"BERT"** (ArXiv: 1810.04805)
   - Similar high-impact paper
   - Should have gold/yellow highlighted papers

3. **"GPT-2"** or **"GPT-3"** papers
   - Recent, highly-cited works
   - Good variety in citation impact

## 🎯 What Success Looks Like

When working correctly, you should see:
- A mix of gold, yellow, and blue/gray papers in the citations list
- Icons (🔥 or 📈) on some papers
- Hovering over icons shows relevance scores
- Orange "influential" badges on papers with high-quality citations
- The most important papers stand out visually

## 💬 Still Having Issues?

If you still don't see any difference:
1. Share the console output (F12 → Console tab)
2. Take a screenshot of what you're seeing
3. Try with a different paper (preferably a highly-cited one)

The debug logging in the console will show exactly what's happening with the scoring and styling!
