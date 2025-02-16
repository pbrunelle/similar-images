import os
import shutil
import tempfile

import pytest


@pytest.fixture
def home_tmp_dir():
    d = tempfile.mkdtemp(dir=os.environ["HOME"])
    yield d
    shutil.rmtree(d)
