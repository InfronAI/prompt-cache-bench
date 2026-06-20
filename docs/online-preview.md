# Online Report Preview

GitHub supports direct online preview for Markdown files. For this repository, the recommended online report entry is:

[DeepSeek V4 Flash Infron vs OpenRouter report](../experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md)

The self-contained `.html` report is useful for local viewing, but GitHub's normal file viewer displays HTML files as source code.

## Option A: Markdown Preview

Use the `.md` report as the public preview URL. Figures are referenced as repository files and render inside GitHub's Markdown viewer.

## Option B: GitHub Pages

To make the `.html` report open as a normal web page:

1. Go to repository `Settings`.
2. Open `Pages`.
3. Set source to `Deploy from a branch`.
4. Select branch `main`.
5. Select folder `/ (root)`.
6. Save.

After GitHub Pages is enabled, the HTML report URL will follow this pattern:

```text
https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html
```

