"""Shared renderability limits, separate from the director's editorial targets."""
MIN_RENDERABLE_SCENES = 2
MAX_RENDERABLE_SCENES = 24


def validate_scene_count(beats: object) -> None:
    if not isinstance(beats, list) or not MIN_RENDERABLE_SCENES <= len(beats) <= MAX_RENDERABLE_SCENES:
        raise ValueError(f'A reel needs {MIN_RENDERABLE_SCENES} to {MAX_RENDERABLE_SCENES} usable scenes.')
