"""Opt-in cleanup for disk-constrained full scientific regression runs."""
import shutil
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption('--brace-clean-temp', action='store_true', default=False,
                     help='Remove each completed test temporary folder after its fixtures close.')


@pytest.fixture(autouse=True)
def bounded_temporary_evidence(request):
    if not request.config.getoption('--brace-clean-temp'):
        yield
        return
    temporary = request.getfixturevalue('tmp_path')
    parent = request.getfixturevalue('tmp_path_factory').getbasetemp().resolve()
    yield
    resolved = Path(temporary).resolve()
    # Never follow a replaced temporary folder outside pytest's own base directory.
    if resolved != parent and resolved.is_relative_to(parent):
        shutil.rmtree(resolved, ignore_errors=True)
