# Prompt 04: Part 2 SQLite search and booking API

> Move every application read and write to SQLite after seeding. Keep calculation and data rules framework-free. Search one joined query by partial hotel name or exact city, both trimmed and case-insensitive. Add traveler booking history and create, cancel, and delete operations with collision-free IDs that are never reused. Expose each operation through FastAPI with appropriate HTTP methods and useful errors, then test the complete lifecycle and the Part 1 search behaviors against temporary databases.

Outcome: separated domain rules and data access from FastAPI, migrated search to SQLite, added booking CRUD endpoints and persistent sequence-based IDs, and expanded the backend suite to 23 tests.
