# Selected prompt — Revised Assignment 2 Part 2 RAG and LLM

## Purpose

Continue the existing Expedia Lite Vue, FastAPI, and SQLite project for the revised Business Intelligence with RAG and an LLM assignment while preserving the working Part 1 and local-storage foundations.

## Supplied constraints

- Research official OpenRouter, Geoapify, Leaflet, Python SQLite, and SQLite security guidance before chatbot implementation.
- Preserve a pre-implementation chatbot mockup with question, loading, answer, no-match, insufficient-data, and error states.
- Use the exact free Nemotron model through OpenRouter demonstrated in class; do not guess the model ID, append an unsupported suffix, or silently switch to paid inference.
- Keep model/key configuration and requests in FastAPI and keep `.env` ignored.
- Retrieve from the saved-hotel SQLite foundation while preserving all original Assignment 1 records and existing Part 1 behavior.
- Do not add a vector database, embeddings, agent framework, Figma project, deployment, payment processing, or actual booking.
- Follow CHECK → TAKE ACTION → VERIFY and request approval before any dependency installation.

## Recorded outcome

CHECK confirmed the existing standard library and `httpx` were sufficient, so no dependency was installed. Research and the early mockup were saved before production chatbot code. The implementation added deterministic parameterized retrieval from only the three saved-hotel tables, one backend OpenRouter boundary, a grounded Vue answer/evidence panel, distinct honest states, and visible Geoapify attribution. Automated checks passed with 91 backend tests, 17 frontend tests, and a production build. An isolated actual-application browser smoke run confirmed loading, answer, insufficient-data, no-match, failure, keyboard submission, evidence/list/map synchronization, and a clean console.

The exact class model slug was absent from all available project/course material. It remains an explicit blank local setting rather than a guessed value. The browser smoke used a clearly documented process-local provider stub and is not claimed as live OpenRouter evidence.

## Required AI evidence — failed and revised approach

The first new security test hard-coded an expectation of nine bookings because the canonical working database contains nine preserved current rows. The test actually runs on a fresh temporary database seeded from the immutable CSV files, where six booking rows are correct. Two tests failed for this reason even though the query text had not executed and no data had changed.

The approach was revised to capture the temporary database's user and booking counts immediately before the hostile-looking question, then compare every count afterward. This tests the real invariant—no SQL-looking user or provider text changes protected data—without conflating canonical user history with the isolated seed fixture. The focused rerun passed 23 tests and the full backend suite passed 91 tests.
