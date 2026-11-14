"""Schutz gegen versteckte Werte: Jedes Ergebnis geht hier durch, bevor es die Oberfläche erreicht.

CA, PA, Persönlichkeit und versteckte Attribute dürfen nur intern gerechnet werden. Trainerbewertungen und
Tendenzen erscheinen nur als Text, nie als Zahl.
"""
from .extract import ATTR_KEYS, HIDDEN

FORBIDDEN_KEYS = {'ca', 'pa', 'pers', 'cons', 'dirt', 'impm', 'injpr', 'vers', '_w', 'q'}
PUBLIC_ATTRS = frozenset(ATTR_KEYS) - HIDDEN


class HiddenValueError(Exception):
    """Im Ergebnis steht ein Wert, der die Oberfläche nicht erreichen darf."""


def assert_public(data):
    """Prüft data rekursiv und gibt es unverändert zurück; wirft HiddenValueError mit dem Pfad des Verstoßes."""
    _check(data, '')
    for group in ('squad', 'pool'):
        for i, player in enumerate(data.get(group) or []):
            attrs = player.get('a') if isinstance(player, dict) else None
            for key in attrs or {}:
                if key not in PUBLIC_ATTRS:
                    raise HiddenValueError(f'Unbekanntes Attribut: {group}[{i}].a.{key}')
    coach = data.get('coach') or {}
    for part in ('coaching', 'mental'):
        for key, value in (coach.get(part) or {}).items():
            if not isinstance(value, str):
                raise HiddenValueError(f'Trainerbewertung ist kein Text: coach.{part}.{key}')
    return data


def _check(node, path):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f'{path}.{key}' if path else str(key)
            if str(key).lower() in FORBIDDEN_KEYS:
                raise HiddenValueError(f'Versteckter Wert: {here}')
            if key == 'tendencies' and not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
                raise HiddenValueError(f'Tendenzen sind keine Textliste: {here}')
            _check(value, here)
    elif isinstance(node, (list, tuple)):
        for i, value in enumerate(node):
            _check(value, f'{path}[{i}]')
