import sys
import types
import os
import warnings
import streamlit.web.bootstrap as bootstrap

# Patch to prevent Streamlit from scanning torch internals
sys.modules['torch.classes'] = types.SimpleNamespace()

# Prevent Streamlit file watcher crashes
os.environ["STREAMLIT_WATCH_USE_POLLING"] = "true"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
warnings.filterwarnings("ignore")

# Run the app in-process
print("[INFO] Launching Streamlit app (patched)...")
bootstrap.run(
    main_script_path="app.py",
    args=[],
    flag_options={},
    is_hello=False,
)
print("[SUCCESS] Streamlit app launched successfully.")