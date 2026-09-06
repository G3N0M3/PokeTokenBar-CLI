import os
import tempfile

# Automatic fallback sandbox when tests are loaded via unittest or direct import
if "PTB_STATE_FILE" not in os.environ:
    _auto_test_file = tempfile.NamedTemporaryFile(prefix="ptb_unittest_", suffix=".json", delete=False)
    _auto_test_file.close()
    os.environ["PTB_STATE_FILE"] = _auto_test_file.name
