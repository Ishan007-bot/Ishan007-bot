<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg?v=2"><img alt="Ishan Ganguly, bib 007. I build AI systems where the model proposes and deterministic code decides. CS at BITS Pilani, Bengaluru. State-level athlete. Open source: 25+ PRs merged at INNO-TECH." src="./assets/hero-light.svg?v=2" width="100%"></picture>

<p><a href="https://www.linkedin.com/in/ishanganguly01/"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-linkedin-dark.svg?v=2"><img alt="LinkedIn" src="./assets/btn-linkedin-light.svg?v=2" height="40"></picture></a>&nbsp;<a href="mailto:ishanganguly10a12@gmail.com"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-email-dark.svg?v=2"><img alt="Email" src="./assets/btn-email-light.svg?v=2" height="40"></picture></a>&nbsp;<a href="https://github.com/Ishan007-bot?tab=repositories"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-repos-dark.svg?v=2"><img alt="All repositories" src="./assets/btn-repos-light.svg?v=2" height="40"></picture></a></p>

**How I race.** The model may propose; code decides what's true. The numbers on this page come from runs I can reproduce, and when a result is only a pilot, it says so. Right now I'm building **SpotHole**, and in open source I've had **25+ PRs merged at INNO-TECH**.

<br>

<a href="https://github.com/alienx5499/Pot-Hole-Detector"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/heat-01-spothole-dark.svg?v=2"><img alt="Heat 01, SpotHole, a pothole reporting app. A report runs snap, clarity check, GPS, address, post, track; status goes pending, acknowledged, resolved." src="./assets/heat-01-spothole-light.svg?v=2" width="100%"></picture></a>

<details><summary><b>How it works</b> · <a href="https://github.com/alienx5499/Pot-Hole-Detector">SpotHole ↗</a> · <a href="https://github.com/alienx5499/Pot-Hole-Detector/releases/download/v1.1.0/SpotHole.apk">Android APK ↗</a></summary>

- React Native (Expo) on the phone, with Node.js, Express and MongoDB behind it.
- Capture: blurry or unclear photos are rejected with a prompt to retake. GPS is tagged automatically and converted to a readable address, and if location permission is denied, the address can be typed in.
- Every report becomes a Twitter post with the photo, the location and a warning message the user can customise, so the pothole is public.
- The dashboard tracks each report through pending, acknowledged and resolved. Users can report as a guest first and convert to a full account later.

</details>

<br>

<a href="https://github.com/Ishan007-bot/Bloodlink"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/heat-02-bloodlink-dark.svg?v=2"><img alt="Heat 02, Bloodlink. CI relay: lint, test, scan, trivy, ghcr, eks. PR #1 'Use O+ stock for A- patients' was disqualified at test, and no image was built. 97% coverage across 81 tests." src="./assets/heat-02-bloodlink-light.svg?v=2" width="100%"></picture></a>

<details><summary><b>How it works</b> · <a href="https://github.com/Ishan007-bot/Bloodlink">Bloodlink ↗</a> · <a href="https://drive.google.com/file/d/1ZLWjHB1ZK-ct8cg0kyptK5HpaRBfAgXC/view?usp=sharing">3½-minute demo</a></summary>

- Allocation is a pure function that takes `now` as an argument: ABO/Rh-compatible units only, exact group first, O- last, nearest expiry first (FEFO), emergencies before routine requests.
- The pipeline runs lint and tests, gitleaks, pip-audit and npm audit, IaC scans, and a Trivy gate on HIGH/CRITICAL findings before an image reaches GHCR, tagged with the commit SHA. Deploys reach EKS through GitHub OIDC with no stored keys, using `helm upgrade --wait` plus a smoke test.
- In Kubernetes, an init container runs Alembic under a Postgres advisory lock. The cluster has an HPA, a PDB, and a NetworkPolicy so only the backend reaches the DB. Pod Security is set to `restricted`, with non-root, read-only containers.
- The Trivy story: dropping `--ignore-unfixed` exposed 44 HIGH findings from 8 CVEs that had no fix yet. Moving to Alpine removed them and cut the image from 291 MB to 195 MB.

</details>

<br>

<a href="https://github.com/Ishan007-bot/Synapse"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/heat-03-synapse-dark.svg?v=2"><img alt="Heat 03, Synapse. OpenAI to Amodei to Anthropic, two hops. Multi-hop context recall 0.48 vector-only versus 0.92 graph RAG on a 4-question pilot; faithfulness 1.00 for both." src="./assets/heat-03-synapse-light.svg?v=2" width="100%"></picture></a>

<details><summary><b>How it works</b> · <a href="https://github.com/Ishan007-bot/Synapse">Synapse ↗</a></summary>

- Offline pipeline: chunk, embed locally with BGE (384-dim), extract per document into a 9-type ontology, resolve entities, then write typed edges and `:MENTIONED_IN` backlinks to Neo4j.
- Online pipeline: entity-link the question, BFS an N-hop subgraph from the seed entities, fuse the chunks those entities mention with vector top-k, and stream a cited answer over SSE.
- The first SSE event carries the subgraph, so the graph draws before the first token.
- I wrote the RAGAS-style evaluation harness myself, with four metrics. Only the retrieval method changes between the two runs. The honest caveat: it is a 4-question pilot so far.

</details>

<br>

<a href="https://github.com/Ishan007-bot/VoxField"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/heat-04-voxfield-dark.svg?v=2"><img alt="Heat 04, VoxField. Speech, extraction, saving and lookup each fall back one layer at a time: Cloud STT to Web Speech, Vertex AI to AI Studio to rules, API to an IndexedDB queue, asset code to fuzzy match." src="./assets/heat-04-voxfield-light.svg?v=2" width="100%"></picture></a>

<details><summary><b>How it works</b> · <a href="https://github.com/Ishan007-bot/VoxField">VoxField ↗</a> · <a href="https://vox-field.vercel.app/">live ↗</a></summary>

- Hybrid speech: online, Google Cloud STT uses vocabulary biasing toward asset codes; offline, the browser's Web Speech takes over. Both push-to-talk and continuous mode (with silence segmentation) are supported.
- Gemini extracts 6 work-order fields, each with its own confidence score, and asks for a re-recording when confidence is low.
- Extraction degrades from Vertex AI to an AI Studio key to a rule-based extractor. Unsent work orders wait in an IndexedDB queue and sync in order, with retries, when the connection returns.
- Lookups match the asset code exactly first, then fall back to rapidfuzz. Queries typically take 1–2 s against a 3 s target. The app covers 40 assets across 11 types, works in English, Hindi and Spanish, and has 51 passing tests.

</details>

<br>

<a href="https://github.com/Ishan007-bot/Search_Typehead_Engine"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/heat-05-typeahead-dark.svg?v=2"><img alt="Heat 05, Typeahead Engine. A consistent-hash ring drawn as a running track with three Redis nodes; the trie sits in the infield. About 6.5 ms p95, 97% cache hits, 99.6% fewer DB writes." src="./assets/heat-05-typeahead-light.svg?v=2" width="100%"></picture></a>

<details><summary><b>How it works</b> · <a href="https://github.com/Ishan007-bot/Search_Typehead_Engine">Search_Typehead_Engine ↗</a></summary>

- Data: 18.8 million real Bing query-click records (ORCAS), aggregated to 200,000 queries.
- The trie precomputes the top-10 at every node, so a lookup is a walk to the prefix node.
- I wrote the consistent-hash ring myself (md5, virtual nodes). It routes each prefix to one of 3 real Redis nodes; Redis only stores the data, and the app decides who owns each key. Adding or removing a node remaps about 1/N of the keys.
- The batch writer buffers searches, merges duplicates and flushes in a single SQLite transaction, either on size or on a 2 s timer. Trending ranking blends all-time counts with time-decayed recent buckets.

</details>

<br>

<details><summary><b>The rest of the field</b> · everything else worth a look</summary>

<br>

| Line | Project | What it is |
|---|---|---|
| Agents | [Balancera](https://github.com/Ishan007-bot/Balancera) | Reconciles bank credits against orders. Deterministic stages do the matching; an LLM sees only what's left, and a gate that imports nothing from the LLM rechecks every amount. 100.0% precision and 0 forced matches on 418 records. |
| Agents | [Procurement Copilot](https://github.com/Ishan007-bot/AI_Procurement_Request_Copilot) | Three architectures compared over 144 runs. A plain workflow with one LLM call beat both agents (15.67 of 16 cases, 2.9 s median). |
| Protocols | [Binary-HTTP](https://github.com/Ishan007-bot/Binary-HTTP) | A binary framing protocol for HTTP with an 8-byte header. The server and client share no code and are tested against a two-page spec (55 tests). |
| Data | [SilentDelay](https://github.com/Ishan007-bot/Schoolbus_notification_pipeline) | Monthly vendor scorecards from 162,766 NYC school-bus incidents: 13 validation rules, a DuckDB star schema, and reruns that produce byte-identical output. |
| Retrieval | [ReadIt](https://github.com/Ishan007-bot/READ_IT) | Chat with one PDF. Hybrid FAISS + BM25 fused with RRF (k=60). An answer with no `[p. N]` citation gets one re-prompt, then a hard refusal. [Live](https://readit-8n9hjsoiczfjqjiuwbcdtw.streamlit.app/) |
| Retrieval | [NotebookRAG](https://github.com/Ishan007-bot/NoteBookLLM_RAG) | NotebookLM-style document chat on Qdrant, with per-chunk error isolation so one bad chunk can't kill an upload. [Live](https://note-book-llm-rag-ebon.vercel.app/) |
| Agents | [Auto_Agent](https://github.com/Ishan007-bot/Auto_Agent) | Browser agent with set-of-marks perception. `task_complete` is accepted only after a check against the live page. |
| Evaluation | [EVAL_FRONTIER](https://github.com/Ishan007-bot/EVAL_FRONTIER_Assistant) | One assistant on two model tiers: hallucination rate 10% vs 0%, content safety 62% vs 100%. |
| Protocols | [HTTP/1.1 Calculator](https://github.com/Ishan007-bot/HTTP-1.1_CALCULATOR_SERVER) | Raw sockets with keep-alive and pipelining. A framing error closes the connection; a semantic error keeps it open. |
| Systems | [RouteForge](https://github.com/Ishan007-bot/RouteForge) | OpenStreetMap routing with Dijkstra, A*, bidirectional search and Contraction Hierarchies. In progress. |

</details>

<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/off-keyboard-dark.svg?v=2"><img alt="Off the keyboard: state-level cricketer, state-level footballer, state-level track and field athlete. Paints. Watches films." src="./assets/off-keyboard-light.svg?v=2" width="100%"></picture>

<sub>Every image here is drawn by <code>tools/build.py</code>: one geometry, two inks, no third-party widgets. Type: Barlow and IBM Plex Mono, SIL Open Font License.</sub>
