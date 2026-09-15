# Prompt 03: Part 2 SQLite foundation

> Add a framework-free SQLite persistence layer for hotels, trips, users, and bookings. Keep the supplied text IDs, enforce the declared foreign keys on every connection, and keep the database outside version control. Seed all four instructor CSV files exactly once by recording completion in a marker table. Prove with fresh temporary databases that a second initialization neither duplicates starter data nor restores deleted rows nor erases or resets user-created and cancelled bookings.

Outcome: introduced the SQLite schema, per-connection foreign-key enforcement, transactional one-time seeding, persistent booking-ID sequence, ignored runtime database, and focused seed/persistence tests.
