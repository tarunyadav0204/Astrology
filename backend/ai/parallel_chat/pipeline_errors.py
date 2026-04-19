"""Errors for the parallel chat pipeline."""


class ParallelPipelineError(Exception):
    """Reserved for parallel pipeline failures. Branches now soft-fail to `status=unavailable` so merge can proceed."""


class ParallelPathSkipped(Exception):
    """Internal: caller should fall back to legacy (should not propagate to user)."""
