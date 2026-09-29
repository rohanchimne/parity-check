# parity-check

During a warehouse migration, the old and new systems run side by side for weeks. Before anything cuts over, someone has to prove the new one returns the same answers as the old one.

The check most people write first, a total row count, is close to useless here. The most common defects move rows to the wrong day instead of losing them, so totals match while the daily numbers are wrong.

parity-check compares two database engines partition by partition, on row counts, schema and business metrics, and drills down to the exact rows when they disagree.

**Status:** work in progress.