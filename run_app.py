import subprocess
import webbrowser
import time

subprocess.Popen([
    "python",
    "-m",
    "streamlit",
    "run",
    "app.py"
])

time.sleep(3)

webbrowser.open(
    "http://localhost:8501"
)