"""Exact astronomical contacts and house occupancy inside each PD.

Six-hour screening is refined to one second. Stations split the search so a
retrograde loop may produce multiple crossings, including two within one step.
The orb is a declared interpretive convention, not a probability of an event.
"""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from itertools import pairwise

from prediction_engine.transit_returns import (
    _angular_distance, _crosses_target, _refine_crossing, _refine_station,
    _strict_planet_state,
)
from .evidence import aspect_houses, aspect_numbers

SLOW_PLANETS = ('Jupiter', 'Saturn', 'Rahu', 'Ketu')
SCREEN_STEP = timedelta(hours=6)


def utc(value):
    parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    if parsed.tzinfo is None:
        raise ValueError('Transit boundaries require a timezone')
    return parsed.astimezone(timezone.utc)


def make_state_reader():
    # Shared per request across all PDs/targets, never shared between users.
    return lru_cache(maxsize=150000)(_strict_planet_state)


def samples_for(planet, start, end, state_at):
    times = [start]
    while times[-1] + SCREEN_STEP < end:
        times.append(times[-1] + SCREEN_STEP)
    times.append(end)
    rows = [(time, *state_at(time, planet)) for time in times]
    stations = []
    for lo, hi in pairwise(rows):
        if lo[2] * hi[2] < 0:
            at = _refine_station(lo[0], hi[0], planet, state_at)
            if lo[0] < at < hi[0]:
                stations.append((at, *state_at(at, planet)))
    return sorted(rows + stations)


def crossings(planet, target, samples, state_at):
    found = []
    for lo, hi in pairwise(samples):
        if not _crosses_target(lo[1], hi[1], target):
            continue
        if _angular_distance(lo[1], target) < 1e-9:
            at = lo[0]
        else:
            at = _refine_crossing(lo[0], hi[0], planet, target, state_at)
        if not found or abs(at - found[-1]) > timedelta(seconds=2):
            found.append(at)
    return found


def contact_windows(planet, target, start, end, state_at, *, orb=1.0, samples=None):
    """Include in-orb approaches with no exact crossing; mark clipped boundaries."""
    samples = samples or samples_for(planet, start, end, state_at)
    exact = [at for at in crossings(planet, target, samples, state_at) if start <= at < end]
    edges = {start, end}
    for boundary in ((target - orb) % 360, (target + orb) % 360):
        edges.update(at for at in crossings(planet, boundary, samples, state_at) if start < at < end)
    windows = []
    for left, right in pairwise(sorted(edges)):
        midpoint = left + (right - left) / 2
        if _angular_distance(state_at(midpoint, planet)[0], target) > orb:
            continue
        if windows and windows[-1][1] == left:
            windows[-1] = (windows[-1][0], right)
        else:
            windows.append((left, right))
    return [{'start_at': left.isoformat(), 'end_at': right.isoformat(),
        'clipped_start': left == start, 'clipped_end': right == end,
        'exact_passes': [{'at': at.isoformat(),
            'motion': 'retrograde' if state_at(at, planet)[1] < 0 else 'direct',
            'error_degrees': round(_angular_distance(state_at(at, planet)[0], target), 7)}
            for at in exact if left <= at < right],
        'orb_degrees': orb} for left, right in windows]


def occupancy_segments(planet, start, end, chart, targets, state_at, samples):
    edges = {start, end}
    # Refine both sign and nakshatra boundaries; neither is assumed from a month sample.
    for target in sorted({i * 30.0 for i in range(12)} | {i * (360 / 27) for i in range(27)}):
        edges.update(at for at in crossings(planet, target, samples, state_at) if start < at < end)
    asc = int(chart['ascendant'] / 30)
    rows = []
    for left, right in pairwise(sorted(edges)):
        longitude, speed = state_at(left + (right - left) / 2, planet)
        sign = int(longitude / 30)
        house = ((sign - asc) % 12) + 1
        nak = int(longitude / (360 / 27)) + 1
        aspects = aspect_houses(planet, house)
        relations = []
        for target in sorted(targets):
            natal = chart['planets'][target]
            kinds = []
            if sign == natal['sign']: kinds.append('same_natal_sign')
            if nak == int(natal['longitude'] / (360 / 27)) + 1: kinds.append('same_natal_nakshatra')
            if natal['house'] in aspects: kinds.append('whole_sign_aspect_to_natal_position')
            if kinds: relations.append({'natal_planet': target, 'relations': kinds})
        rows.append({'start_at': left.isoformat(), 'end_at': right.isoformat(),
            'transiting_planet': planet, 'sign_number': sign + 1,
            'natal_house': house, 'aspected_natal_houses': aspects,
            'nakshatra_number': nak, 'relations_to_natal': relations,
            'motion_at_midpoint': 'retrograde' if speed < 0 else 'direct'})
    return rows


def reinforcement_windows(contacts):
    edges = sorted({utc(row[key]) for row in contacts for key in ('start_at', 'end_at')})
    windows = []
    for left, right in pairwise(edges):
        active = [row for row in contacts if utc(row['start_at']) <= left and utc(row['end_at']) >= right]
        # Multiple aspects from one transit planet are not independent timing votes.
        movers = sorted({row['transiting_planet'] for row in active})
        if len(movers) < 2:
            continue
        windows.append({'start_at': left.isoformat(), 'end_at': right.isoformat(),
            'transiting_planets': movers, 'contact_ids': [row['id'] for row in active]})
    return windows


def build_pd_transits(chart, pd, levels, state_at, *, orb=1.0):
    start, end = utc(pd['start_at']), utc(pd['end_at'])
    targets = set(levels.values())
    movers = sorted(targets | set(SLOW_PLANETS) | {'Sun'})
    contacts, occupancy = [], []
    for planet in movers:
        samples = samples_for(planet, start, end, state_at)
        occupancy.extend(occupancy_segments(planet, start, end, chart, targets, state_at, samples))
        for target in sorted(targets):
            natal_longitude = chart['planets'][target]['longitude']
            for aspect in aspect_numbers(planet):
                target_longitude = (natal_longitude - (aspect - 1) * 30) % 360
                for window in contact_windows(planet, target_longitude, start, end, state_at, orb=orb, samples=samples):
                    contacts.append({**window, 'transiting_planet': planet, 'natal_planet': target,
                        'natal_levels': [level for level, name in levels.items() if name == target],
                        'natal_longitude': natal_longitude, 'aspect_from_planet': aspect,
                        'relationship': 'conjunction' if aspect == 1 else 'graha_drishti',
                        'is_own_natal_return': planet == target and aspect == 1,
                        'is_sun_trigger': planet == 'Sun'})
    contacts.sort(key=lambda row: (row['start_at'], row['transiting_planet'], row['natal_planet'], row['aspect_from_planet']))
    for index, row in enumerate(contacts):
        row['id'] = f"{pd['id']}_contact_{index + 1}"
    return {'contacts': contacts, 'house_occupancy': occupancy,
        'reinforcement_windows': reinforcement_windows(contacts),
        'conventions': {'orb_degrees': orb, 'screening_hours': 6,
            'root_precision_seconds': 1, 'ayanamsha': 'lahiri', 'node_type': 'mean',
            'aspects': 'Classical planet graha drishti; nodes 7 only, conjunction separate; node 5/9 excluded.',
            'note': 'Degree contacts refine timing; whole-sign aspects and house occupancy are broader evidence. Neither guarantees an event.'}}
