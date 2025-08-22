## Installation (FastAPI)

1. **Install `uv` (a fast Python package manager):**
    ```bash
    pip install uv
    ```
2. **Create a new virtual environment using `uv`:**
    ```bash
    uv venv
    ```
3. **Activate the virtual environment:**
    - On macOS/Linux:
      ```bash
      source .venv/bin/activate
      ```
    - On Windows:
      ```bash
      .venv\Scripts\activate
      ```
4. **Install project dependencies from `pyproject.toml` using `uv`:**
    ```bash
    uv sync
    ```