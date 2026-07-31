"""Shared test support package.

Some subsystem tests intentionally reuse deterministic fakes from neighboring test
modules.  Declaring the directory as a package makes that dependency independent of
the Python importer's namespace-package and environment behavior.
"""
