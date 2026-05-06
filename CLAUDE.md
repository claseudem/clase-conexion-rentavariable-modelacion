# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This project connects modeling and variable income (equity) coursework. It is a Python 3.12 project managed with `pyproject.toml` (PEP 517/518 layout, no build backend configured yet).

## Commands

```bash
# Install dependencies
uv add <package>

# Run the comparador (2 tickers requeridos)
uv run python main.py AAPL TSLA
uv run python main.py AAPL TSLA --period 2y   # períodos: 1mo 3mo 6mo 1y 2y 5y
```

## Project structure

The project is at an early scaffold stage:
- `main.py` — current entry point
- `pyproject.toml` — project metadata, Python ≥3.12 required, no dependencies declared yet
- `.python-version` — pins Python 3.12 (used by pyenv/mise)
