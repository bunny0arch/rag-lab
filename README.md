# RAG Lab

RAG Lab is a no-auth educational workbench for comparing Traditional Search and Retrieval-Augmented Generation over the same document collection. It is intentionally transparent: BM25 results are shown as evidence only, vector retrieval is implemented with local TF-IDF cosine similarity, hybrid retrieval fuses sparse and dense rankings, and generation is only attempted when `OPENAI_API_KEY` is configured.

## Run locally

The project uses Python's standard library and does not require Node. From the project root:

```powershell
$env:RAG_PORT=3000
python server.py
```

Open `http://127.0.0.1:3000`. If you want grounded LLM answers, copy `.env.example` values into the environment before starting. Without a key the app remains fully searchable and labels generation as unavailable; it never displays a fabricated answer.

The built-in corpus contains nine small Markdown-style sources. Upload TXT, Markdown, or HTML files from the interface. PDF and DOCX are accepted by the file picker but clearly report that optional server-side extractors are not configured in this minimal prototype. Uploaded browser-readable sources persist in localStorage and can be reset to the sample corpus.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Design notes

The visual system follows a Motion.dev-inspired interaction language: short, purposeful transitions, panel lift on hover, visible stage progression, and reduced-motion-safe CSS. It borrows MotionSites.ai's editorial dark canvas, layered cards, neon signal accent, and strong categorization while keeping the product shaped as a workbench rather than a marketing page. Apple HIG motion guidance informed the choice to keep animations brief and never use motion as the only status signal.
