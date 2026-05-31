"""Integration tests for BuzzReach (TEST-001).

End-to-end anti-silo tests that validate cross-module contracts
by running the full scan pipeline against a real SQLite database,
then asserting the API returns the same data.
"""
