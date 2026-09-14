import json
import io
import sys
import os
import base64
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

NB_PATH = ROOT / "notebooks" / "01_reproducible_pipeline.ipynb"

def run_notebook():
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Shared execution context for the notebook session
    exec_globals = {
        "__name__": "__main__",
        "__file__": str(NB_PATH)
    }

    execution_count = 1
    total_code_cells = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    print(f"Executing {total_code_cells} code cells in {NB_PATH.name}...")

    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue

        code_text = "".join(cell["source"])
        print(f"[{execution_count}/{total_code_cells}] Running cell {i+1}...")

        # Setup stdout redirection
        stdout_buf = io.StringIO()
        orig_stdout = sys.stdout
        sys.stdout = stdout_buf

        cell_outputs = []
        plt.close('all')

        try:
            exec(code_text, exec_globals)
        except Exception as e:
            sys.stdout = orig_stdout
            err_msg = f"Cell execution error: {e}"
            print(f"ERROR in cell {i+1}: {e}")
            cell_outputs.append({
                "output_type": "error",
                "ename": type(e).__name__,
                "evalue": str(e),
                "traceback": [err_msg]
            })
        finally:
            sys.stdout = orig_stdout

        # Capture text output
        captured_text = stdout_buf.getvalue()
        if captured_text:
            cell_outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": [line + "\n" for line in captured_text.splitlines()]
            })

        # Capture any open matplotlib figures
        fig_nums = plt.get_fignums()
        for fignum in fig_nums:
            fig = plt.figure(fignum)
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150)
            img_buf.seek(0)
            b64_data = base64.b64encode(img_buf.read()).decode("utf-8")
            cell_outputs.append({
                "output_type": "display_data",
                "data": {
                    "image/png": b64_data,
                    "text/plain": [f"<Figure size {fig.get_size_inches()[0]*150:.0f}x{fig.get_size_inches()[1]*150:.0f} with {len(fig.axes)} Axes>"]
                },
                "metadata": {}
            })
            plt.close(fig)

        cell["execution_count"] = execution_count
        cell["outputs"] = cell_outputs
        execution_count += 1

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

    print(f"Successfully executed and saved notebook to {NB_PATH} with all outputs!")

if __name__ == "__main__":
    run_notebook()
