# RAG Lab implementation plan

## Product shape
RAG Lab is a no-auth educational developer tool: one shared question, one document collection, two honest pipelines. The first slice runs locally with a Python standard-library server and a static browser client so it works without a Node toolchain. The server owns sample-corpus search and the optional LLM boundary; the browser owns uploads, collection state, comparison controls, and inspection.

## Architecture
- `server.py`: HTTP server, sample corpus loading, BM25 lexical retrieval, TF-IDF vector retrieval, hybrid fusion, measured timings, and optional OpenAI-compatible `/api/rag` generation. When no API key is configured, the app returns an explicit unavailable state rather than fabricating an answer.
- `public/index.html`: single comparison workspace with document library, settings, demos, pipeline inspector, and side-by-side results.
- `public/app.js`: upload parsing for text/Markdown/HTML, client document state, query orchestration, timing display, evidence expansion, citations, and localStorage persistence.
- `public/styles.css`: dark editorial developer-tool visual system.
- `public/sample_docs.json`: internally consistent sample corpus with source metadata.
- `tests/test_app.py`: critical endpoint tests for BM25, vector retrieval, hybrid retrieval, unsupported questions, and no-key RAG honesty.

## Design direction
Inspired by Motion.dev's purposeful spring/gesture language and MotionSites.ai's editorial, premium visual presentation. The UI uses an ink-black canvas with layered graphite panels and one ownable mint accent (`#b8ff6a`) to make retrieval states feel observable, not decorative. The layout is a split workbench rather than a centered landing page: navigation rail, comparison canvas, and inspector rail.

Core principles: evidence first; controlled density; motion as feedback; visible system state. Signature elements are a thin mint signal line, animated stage dots, and soft radial ambient gradients. Motion is brief and cancelable: panel lift on hover, staged fades, progress shimmer only while work is real, and `prefers-reduced-motion` support. Typography pairs Space Grotesk for product/UI labels with IBM Plex Mono for metrics, source IDs, and pipeline trace. Brand essence: “A transparent lab bench for seeing how retrieval becomes an answer.” Personality: precise, curious, candid. Voice examples: “Same evidence. Different behavior.” and “No model configured — retrieval still works.” The wordmark is a compact `RAG / LAB` lockup with a mint slash mark.

## Workflow
1. Seed and inspect the local corpus.
2. Implement and test retrieval endpoints.
3. Implement comparison workspace and document library.
4. Add optional grounded generation boundary and citation validation.
5. Run the server, verify route manifest and smoke tests, then iterate on defects.

References: [Motion.dev](https://motion.dev/) emphasizes native gestures, layout animation, spring physics, staged sequences, and performance; [Motion UI](https://motion.dev/ui) shows focused headless components such as typewriter, ticker, and animated numbers; [MotionSites.ai](https://motionsites.ai/) demonstrates editorial categories, dark premium presentation, animated backgrounds, and strong card previews; [Apple HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion) reinforces purposeful, brief, optional feedback motion.
