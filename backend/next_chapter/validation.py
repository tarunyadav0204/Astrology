"""Task-local editorial diagnostics; never rewrite model-authored content."""
from contextvars import ContextVar
from functools import wraps

warning_sink = ContextVar('chapter_validation_warning_sink', default=None)


def warn(message):
    sink = warning_sink.get()
    if sink is None:
        raise ValueError(message)
    sink(str(message))


def advisory(check):
    @wraps(check)
    def wrapped(*args, **kwargs):
        try:
            return check(*args, **kwargs)
        except ValueError as exc:
            warn(exc)
            return args[0] if args else None
    return wrapped


def log_warning(message):
    """Optional editor/reviewer diagnostics never abort customer delivery."""
    import logging
    logging.getLogger(__name__).warning('NEXT_CHAPTER_VALIDATION %s', message)
    sink = warning_sink.get()
    if sink is not None:
        sink(str(message))
