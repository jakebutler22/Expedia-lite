# Revised Assignment 2 Part 2 research

Research was completed on October 7, 2026, before production chatbot code was added. It builds on the preserved [Part 1 research](part1-location-research.md) and focuses only on decisions needed for Expedia Lite's local-hotel business-intelligence chatbot.

## Sources and findings

### OpenRouter and the class model setting

- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart) and [chat-completion API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request) document a backend `POST` to `https://openrouter.ai/api/v1/chat/completions` with bearer authorization, a model ID, messages, and supported generation parameters. Expedia Lite already has `httpx`, so the REST API needs no new SDK.
- [Free model variants](https://openrouter.ai/docs/guides/routing/model-variants/free) are separate catalog entries. A `:free` suffix is valid only when the model lists that variant; the free entry can have different availability, rate limits, context length, and endpoints.
- The live [OpenRouter Models API](https://openrouter.ai/api/v1/models) and [free-model collection](https://openrouter.ai/collections/free-models) were checked on October 7, 2026. Multiple free Nemotron entries existed, including `nvidia/nemotron-3.5-lightning:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, and `nvidia/nemotron-3-super-120b-a12b:free`. Their catalog records showed zero prompt/completion price but different context, output, and supported-parameter values. This confirms that the phrase "free Nemotron" is not enough to select one safely.
- The current [OpenRouter pricing page](https://openrouter.ai/pricing/) listed the free plan as 25+ free models, four free providers, and 50 requests per day. Free-model capacity and availability remain provider-dependent.

Official catalog snapshot on October 7, 2026 (research evidence, not a model selection):

| Free Nemotron catalog entry | Prompt/output price | Context / maximum completion | Relevant listed parameters |
| --- | --- | --- | --- |
| `nvidia/nemotron-3.5-lightning:free` | $0 / $0 | 1,000,000 / 65,536 tokens | `max_tokens`, `temperature`, `top_p`, `seed`, `reasoning`, tools |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | $0 / $0 | 1,000,000 / 65,536 tokens | the same core parameters plus `reasoning_effort` |
| `nvidia/nemotron-3-super-120b-a12b:free` | $0 / $0 | 262,144 / 235,929 tokens | the same core parameters plus `response_format` and structured outputs |

All three listed the small common subset used by this implementation: `model`, message input, `max_tokens`, and `temperature`. Availability can change independently of price, so the exact class entry still requires a live recheck immediately before the demo.

Observed weakness: the course material available in this repository, neighboring projects, Git history, and the supplied revised brief does not contain the exact model slug demonstrated in class. Choosing one of several current Nemotron variants would be a guess and could silently select the wrong class configuration.

Decision: support exactly one explicit backend `OPENROUTER_MODEL` value and one backend key. Do not provide a paid fallback, use the automatic free router, or manufacture a `:free` suffix. Until the exact class slug is supplied locally, configuration remains visibly incomplete. The backend will use only broadly supported parameters (`model`, `messages`, `temperature`, and `max_tokens`) after the configured slug is verified in the catalog.

### Geoapify location pipeline

- [Forward geocoding](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/) says postcode searches should use `type=postcode`; postcodes are unique only within a country, so a country filter is strongly recommended. Responses include `postcode`, `country_code`, `result_type`, latitude, and longitude that can be checked before accepting a center.
- [Places API](https://apidocs.geoapify.com/docs/places/) distinguishes a circle `filter`, which constrains results to the circle, from a `bias`, which only changes ranking. It accepts 1–500 results per page and defaults to 20. Expedia Lite deliberately requests at most 20 `accommodation.hotel` results inside a 5,000-metre circle.
- [Geoapify pricing](https://www.geoapify.com/pricing/) listed 3,000 credits per day and up to five requests per second for the free plan on October 7, 2026. It requires Geoapify and underlying data-source attribution near the map or supplied information; a normal geocoding or Places request generally costs one credit.

Observed weakness: a Places response describes mapped places, not live hotel inventory. It does not prove real prices, rooms, availability, or booking status. Result coverage and counts can change.

Decision: preserve the exact Part 1 postcode confirmation and hard 5 km filter. Keep all Geoapify calls and keys in FastAPI. Keep visible OpenStreetMap and Geoapify attribution. Treat provider names, addresses, IDs, and coordinates as location facts only. Label the stored October 10–14 prices and room counts as **simulated course data** everywhere, including chatbot context and answers.

### Leaflet and linked hotel selection

- [Leaflet reference](https://leafletjs.com/reference.html) documents map/marker events, bounds fitting, popups, attribution controls, and enabled keyboard navigation. Map focus supports arrows and `+`/`-`; hotel result buttons remain the clearest keyboard path for selecting a particular marker.

Observed weakness: a map alone makes comparison and screen-reader review difficult, and marker popups can be visually disconnected from a chat answer.

Decision: retain the same `place_id` dataset and selection state for list and markers, keep the visible result list beside the map, and present chatbot evidence as text links/buttons that can select the same hotel. Do not hide attribution or make the chatbot replace the structured list.

### SQLite retrieval and security

- [Python `sqlite3`](https://docs.python.org/3/library/sqlite3.html) recommends placeholders instead of string formatting for values to prevent SQL injection. Its online backup API produces a consistent copy even while another client accesses the database.
- [SQLite security guidance](https://www.sqlite.org/security.html) describes extra controls when applications accept untrusted SQL or databases, including defensive configuration, lower limits, authorizers, and `trusted_schema=OFF` for suitable threat models.

Observed weakness: model-generated SQL creates an injection and data-integrity risk, while sending the whole database would expose unrelated traveler and booking records. The revised graded benchmark nevertheless requires a model-proposed query, so merely avoiding generated SQL no longer satisfies the assignment.

Revised decision: keep retrieval-augmented generation without embeddings or a vector database, but place the required generated SQL behind several independent controls. Only one comment-free, semicolon-free `SELECT` is accepted. SQLite's authorizer denies every operation except `SELECT`, reads of `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`, and a small safe-function allowlist. A compile-only validation happens first; execution repeats the authorizer and adds VM-work, row, column, and serialized-result limits. Assignment 1 users, bookings, trips, and supplied hotels remain inaccessible. A second model request receives the exact validated SQL and exact bounded records.

### Relevant hotel/chat interaction patterns

- [Booking.com AI Trip Planner](https://news.booking.com/bookingcom-launches-new-ai-trip-planner-to-enhance-travel-planning-experience/) lets people ask broad or specific questions, refine them conversationally, and review a visual property list alongside the conversation.
- [Booking.com Smart Filter and Property Q&A](https://news.booking.com/bookingcom-enhances-travel-planning-with-new-ai-powered-features--for-easier-smarter-decisions/) show the value of natural-language questions at the point where the underlying property facts are relevant.
- [Expedia conversational trip planning](https://www.expedia.com/newsroom/expedia-launches-conversational-trip-planning-powered-by-chatgpt-to-inspire-members-to-dream-about-travel-in-new-ways/) connects chat recommendations with saved hotels instead of leaving suggestions as unstructured text.
- [Expedia Romie](https://ir.expediagroup.com/news-and-events/news/news-details/2024/Put-Your-Trip-on-Autopilot-Expedia-Group-Introduces-New-Innovations-at-EXPLORE-to-Take-the-Stress-out-of-Travel-and-Enhance-Partner-Experience/default.aspx) demonstrates progressive refinement and contextual help, but its broad planning, email, booking, and disruption capabilities are far outside this assignment.

Useful patterns: a prominent natural-language input; a short example question; immediate loading feedback; answers next to the relevant structured results; the ability to select cited hotels; and explicit boundaries when facts are unavailable.

Weaknesses to avoid: open-ended claims that are not tied to retrieved records, unclear data freshness, treating generated text as live inventory, hiding the distinction between provider and simulated fields, and promising booking or personalization capabilities the local classroom app does not have.

## Adopted design

1. Add a clearly labeled **Saved hotel insights** panel after the local hotel workflow. It asks questions only about locally saved provider hotels and their simulated October 10–14, 2026 nightly facts.
2. Request one asks the configured model for either `insufficient_data` or one SQL `SELECT`. FastAPI—not the model—decides whether that query is safe, applies work/result limits, and executes it only after validation.
3. Request two receives the original question, validated SQL, and exact retrieved JSON rows. A successful empty query still reaches request two for a `no_matches` result. Return distinct `answer`, `no_matches`, `insufficient_data`, and `rejected_query` outcomes, with stage-specific provider errors.
4. Show the proposed SQL, validation/execution decisions, whether request two was sent, and the exact rows grounding the answer. When a retrieved record includes a visible provider identity, it can reuse the existing list/map selection.
5. The LLM is instructed to ignore commands embedded in retrieved text, avoid outside knowledge, make no booking or real-inventory claims, and emit a fixed insufficient-data signal when the retrieved facts cannot answer the question.
6. OpenRouter credentials, model choice, retrieval, prompt construction, and provider calls stay in FastAPI. The frontend receives only safe status, answer, model label, and grounding facts; it never receives either provider key or the full prompt.
7. Use exactly two non-streaming requests for a successful query: SQL generation and grounded answer. Cap question length, SQL length, SQLite work, result rows/columns/bytes, completion tokens, and timeout. Do not add chat history, embeddings, a vector store, an agent framework, actual booking, or paid fallback behavior.

### Requirement-driven revision after the early mockup

The early mockup and first implementation assumed application-owned static SQL
and one model request. The later five-benchmark verification prompt explicitly
required two model requests with validated generated SQL between them. The
design therefore changed rather than pretending the earlier implementation
met the new benchmark. The visible question/answer layout stayed recognizable,
but the implemented evidence panel now exposes the proposed SQL, validator
decision, bounded execution, exact records, and second-request status. This is
the primary documented design revision for the final AI evidence log.

## Provider-setting gap

The exact class Nemotron model ID remains genuinely missing. Add the class-provided slug to `OPENROUTER_MODEL` in ignored `backend/.env` after confirming that exact catalog entry is still free. Add the OpenRouter key beside it as `OPENROUTER_API_KEY`. Do not paste either value into source control or the frontend.
