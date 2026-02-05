# LaTeX Math Rendering in Paper Content

## Overview

The research agent frontend now supports beautiful LaTeX math rendering using **KaTeX**, providing publication-quality mathematical typesetting in the paper viewer.

## Features

### 1. **Inline Math**
Use single dollar signs for inline equations:
```markdown
The formula $E = mc^2$ is Einstein's famous equation.
```

### 2. **Display Math (Block)**
Use double dollar signs for centered display equations:
```markdown
$$
\begin{align*}
\text{BDH-Normfree} \\
\sigma_{t,l} &= \left( \sigma_{t-1,l} + y_{t,l-1} x_{t,l}^T \right) U \\
\rho_{t,l} &= \left( \rho_{t-1,l} + \left( Ey_{t,l-1} \right) x_{t,l}^T \right) U \\
x_{t,l} &= x_{t,l-1} + \left( D_x Ey_{t,l-1} \right)^+ \\
y_{t,l} &= \left( D_y E \sigma_{t-1,l} x_{t,l} \right)^+ \odot x_{t,l}
\end{align*}
$$
```

### 3. **GitHub Flavored Markdown (GFM)**
Enhanced markdown support including:
- Tables with proper styling
- Strikethrough text
- Task lists
- Autolinks

## Styling Features

### Math Blocks
- Light background with blue left border
- Horizontal scrolling for long equations
- Proper padding and margins
- Responsive sizing

### Content Formatting
- **Headers**: Styled with bottom borders and hierarchy
- **Code Blocks**: Syntax-aware with dark background
- **Tables**: Striped rows with borders
- **Links**: Blue color with hover underline
- **Block Quotes**: Blue left border with italic text
- **Images**: Rounded corners with shadow
- **Lists**: Proper indentation and spacing

## Technical Details

### Packages Used
- `katex` (v0.16.9): Fast math rendering engine
- `remark-math` (v6.0.0): Parse LaTeX math in markdown
- `rehype-katex` (v7.0.0): Render parsed math with KaTeX
- `remark-gfm` (v4.0.0): GitHub Flavored Markdown support

### CSS Customization
Custom styles in `src/index.css`:
- Dark mode optimized colors
- Math block styling
- Responsive scrollbars
- Content hierarchy

## Examples

### Complex Equations
```latex
$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$
```

### Matrices
```latex
$$
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$
```

### Aligned Equations
```latex
$$
\begin{align*}
f(x) &= x^2 + 2x + 1 \\
     &= (x + 1)^2
\end{align*}
$$
```

### Greek Letters and Symbols
```latex
$$
\alpha, \beta, \gamma, \Delta, \Sigma, \int, \sum, \prod, \nabla, \partial
$$
```

## OCR Integration

The improved OCR parser (GLM-OCR) now:
1. **Detects** mathematical expressions in papers
2. **Converts** them to LaTeX format
3. **Preserves** equation structure and alignment
4. **Renders** beautifully in the frontend

## Browser Compatibility

KaTeX is supported in all modern browsers:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

## Performance

- **Fast Rendering**: KaTeX is much faster than MathJax
- **No Runtime**: Math is rendered at client-side instantly
- **Small Bundle**: ~200KB additional bundle size
- **Lazy Loading**: CSS loaded only when needed

## Troubleshooting

### Math Not Rendering?
1. Check if the LaTeX syntax is valid
2. Verify dollar signs are properly escaped
3. Look for browser console errors
4. Ensure KaTeX CSS is loaded

### Display Issues?
- Clear browser cache
- Check for CSS conflicts
- Verify dark mode styles are applied

### OCR Missing Math?
- Ensure OCR endpoint is running (port 8080)
- Check backend logs for OCR errors
- Verify PDF quality is sufficient

## Future Enhancements

Potential improvements:
- [ ] Equation numbering
- [ ] Copy LaTeX source button
- [ ] MathML export
- [ ] Accessibility improvements
- [ ] Custom KaTeX macros
- [ ] Chemistry equations support

## Resources

- [KaTeX Documentation](https://katex.org/)
- [Supported Functions](https://katex.org/docs/supported.html)
- [LaTeX Syntax Guide](https://www.overleaf.com/learn/latex/Mathematical_expressions)
