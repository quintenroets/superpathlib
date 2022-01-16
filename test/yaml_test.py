from plib import Path


def test_yaml():
    p = Path('testpath')
    d = {'hi': 'there'}
    p.save(d)
    try:
        assert d == p.load()
    finally:
        p.unlink()
