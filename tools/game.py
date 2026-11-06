"""The game being built: games/<id>/, chosen by XC3_GAME (default xc3; games/xc3 is the only one)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.environ.get('XC3_GAME', 'xc3')


def path(*parts):
    """A file of the selected game's profile folder, e.g. path('profile.json')."""
    p = os.path.join(ROOT, 'games', GAME)
    if not os.path.isdir(p):
        raise SystemExit(f'XC3_GAME={GAME}: no folder games/{GAME}')
    return os.path.join(p, *parts)
