import os

import pytest

DEFAULT_SAVE = os.path.join(os.path.expanduser("~"), "Documents", "Sports Interactive", "Football Manager 26",
                            "games", "Haribaert Kachinski – Ravenna.fm")


@pytest.fixture(scope="session")
def ravenna_save():
    path = os.environ.get("COTRAINER_TEST_SAVE") or DEFAULT_SAVE
    if not os.path.isfile(path):
        pytest.skip(f"Testspielstand fehlt: {path}")
    return path


@pytest.fixture(scope="session")
def ravenna_data(ravenna_save):
    from cotrainer import extract
    return extract.analyse(ravenna_save)


@pytest.fixture(scope="session")
def osijek_save():
    path = os.environ.get("COTRAINER_TEST_SAVE_OSIJEK") or os.path.join(
        os.path.dirname(DEFAULT_SAVE), "Ivan Kurasic – NK Osijek.fm")
    if not os.path.isfile(path):
        pytest.skip(f"Testspielstand fehlt: {path}")
    return path
