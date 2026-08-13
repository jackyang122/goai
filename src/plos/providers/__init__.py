"""Provider seams — the ONLY components that call external services.

Each seam has an ABC, a real implementation, and a zero-dependency stub. The registry
selects per ``Settings`` and gracefully degrades to a stub (with a warning) when the real
dependency is missing or unconfigured. Domain code depends only on the ABCs.
"""
