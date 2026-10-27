"""The game being built: games/<id>/, chosen by XCDE_GAME (default xc3; xcde is the original Monado target)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.environ.get('XCDE_GAME', 'xc3')


def path(*parts):
    """A file of the selected game's profile folder, e.g. path('profile.json')."""
    p = os.path.join(ROOT, 'games', GAME)
    if not os.path.isdir(p):
        raise SystemExit(f'XCDE_GAME={GAME}: no folder games/{GAME}')
    return os.path.join(p, *parts)
