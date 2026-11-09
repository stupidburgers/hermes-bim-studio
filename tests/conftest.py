"""Test-time isolation: confine every generated file to a throwaway Hermes home.

The plugin writes all output under <HERMES_HOME>/plugin-data/hermes-bim-studio/.
Setting HERMES_HOME here (at collection/import time) keeps the test run from
touching the real user home and works for both pytest-style and
unittest.TestCase test methods, before any test module is imported.
"""
import atexit
import os
import shutil
import tempfile

_TEST_HERMES_HOME = tempfile.mkdtemp(prefix="bim-test-hermes-home-")
os.environ["HERMES_HOME"] = _TEST_HERMES_HOME


def _cleanup():
    shutil.rmtree(_TEST_HERMES_HOME, ignore_errors=True)


atexit.register(_cleanup)
