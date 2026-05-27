# Copilot Custom Instructions for This Project

## 1. Use Python Virtual Environment (venv)

- Always use a Python virtual environment for running, testing, and installing dependencies in this project.

- To create a venv (if not present):

  ```sh
  python3 -m venv venv
  ```

- To activate the venv (macOS/Linux):

  ```sh
  source venv/bin/activate
  ```

- To install dependencies:

  ```sh
  pip install -r requirements.txt
  ```

- All terminal commands for Python should assume the venv is activated.

## 2. Project Structure

- Main entry point: `run.py`
- App code: `app/`
- Utilities: `app/utils/`
- Configurations: `app/config.py`, `instance/`
- Templates: `app/templates/`
- Static files: `app/static/`

## 3. Configuration

- Use `instance/config.py` for local overrides. Prefer development environment settings.
- Default config: `app/default_config.py`

## 4. Testing & Linting

- Use `pytest` for tests (if tests are added).
- Use `flake8` or `black` for linting/formatting (if desired, add to requirements.txt).

## 5. Environment Variables

- Sensitive or environment-specific settings should be set via environment variables or in `instance/config.py` (not committed).

## 6. General

- Do not commit `venv/`, `__pycache__/`, or any secrets.
- Update `requirements.txt` after installing new packages:

  ```sh
  pip freeze > requirements.txt
  ```
