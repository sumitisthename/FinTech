import subprocess
import os
import sys
import types

# Step 0: Patch to avoid Streamlit crash (torch.classes)
sys.modules['torch.classes'] = types.SimpleNamespace()
os.environ["STREAMLIT_WATCH_USE_POLLING"] = "true"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def run_script(script_name):
    print(f"\n[🔄] Running {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[❌] {script_name} failed:\n{result.stderr}")
        sys.exit(1)
    else:
        print(f"[✅] {script_name} completed successfully.")

# 1. Fetch News
run_script("news_fetcher.py")

# 2. Summarize Articles
run_script("summarize_articles.py")

# 3. Build Vector Store
run_script("vector_store.py")

# 4. Launch App In-Process
print("\n🚀 Launching Streamlit App...")
import streamlit.web.bootstrap as bootstrap
import warnings
warnings.filterwarnings("ignore")

bootstrap.run(
    main_script_path="app.py",
    #command_line=None,
    args=[],
    flag_options={},
    is_hello=False
)
print("[✅] Streamlit app launched successfully.")
# Note: The app will run in the same process, so you can interact with it directly.