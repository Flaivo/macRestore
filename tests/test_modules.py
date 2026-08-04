from audit.modules.obsidian import ignore_bloat


def test_obsidian_ignores_runtime_files():
    names = ["SingletonSocket", "SingletonCookie", "SingletonLock", "obsidian.json"]

    ignored = ignore_bloat(None, names)

    assert set(ignored) == {"SingletonSocket", "SingletonCookie", "SingletonLock"}
