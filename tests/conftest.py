import os
import tempfile
import pytest

@pytest.fixture(autouse=True, scope="session")
def isolate_test_state():
    temp_state = tempfile.NamedTemporaryFile(prefix="ptb_pytest_", suffix=".json", delete=False)
    temp_state.close()
    old_val = os.environ.get("PTB_STATE_FILE")
    os.environ["PTB_STATE_FILE"] = temp_state.name
    yield temp_state.name
    if old_val is not None:
        os.environ["PTB_STATE_FILE"] = old_val
    else:
        os.environ.pop("PTB_STATE_FILE", None)
    if os.path.exists(temp_state.name):
        os.unlink(temp_state.name)
