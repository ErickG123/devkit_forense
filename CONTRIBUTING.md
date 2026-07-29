# Contributing to ForenseLab

First off, thank you for considering contributing to ForenseLab! 

## Architecture Overview

ForenseLab is a full-stack digital forensics application composed of two main layers:
1. **Back-end (Python & FastAPI/Typer):** Located in `src/`. The application uses a feature-based architecture (e.g., `network`, `browser`, `mail`) and provides both a CLI interface and a REST API.
2. **Front-end (Angular):** Located in `forenselab-ui/`. The UI is built with Angular 17+ using a standalone, feature-based architecture and styled with TailwindCSS.

## Setting Up Your Local Environment

### 1. Back-end (Python)
- Ensure you have Python 3.11 or newer.
- Create a virtual environment: `python -m venv venv`
- Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
- Install dependencies: `pip install -e .`
- Format and lint your code using `ruff`: `ruff format src/` and `ruff check src/ --fix`.

### 2. Front-end (Angular)
- Ensure you have Node.js (version 20+) installed.
- Navigate to the UI directory: `cd forenselab-ui`
- Install dependencies: `npm install`
- Start the development server: `npm start`

## Submitting a Pull Request
- Create a branch for your feature or bug fix.
- Follow the Pull Request template provided.
- Ensure all tests and GitHub Actions pipelines pass.
