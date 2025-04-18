# `integrations/` — Internal Low-Level Connectors

This folder contains **internal adapters, API clients, and service wrappers** that support the QuackVerse ecosystem but are not meant to be used directly by most QuackTools or end users.

## Purpose
- Serve as the low-level interface layer to third-party services (APIs, SDKs, CLIs)
- Provide isolated, reusable implementations for integration logic
- Keep core logic out of `quackcore/` and themed modules like `quackmedia/`

## When to Use
You should add logic to `integrations/` if:
- It is experimental, low-level, or untested
- It wraps a 3rd-party service SDK or shell tool
- It provides a shared adapter or base utility for a high-level module

## When *Not* to Use
Avoid putting code here if:
- It belongs to a published or user-facing tool (put that in `src/quackmedia`, `src/quackcloud`, etc.)
- It is core infrastructure (that belongs in `quackcore.integrations.core`)

## Example Layout
```
integrations/
├── ffmpeg/                  # Raw ffmpeg command builders and subprocess logic
├── googleapi/               # Shared Google API setup/utilities
├── openai/                  # Shared OpenAI utilities (token management, etc.)
├── base.py                  # Optional base classes used across adapters
```

## Usage
All reusable logic should:
- Avoid side effects
- Be tested using mocks
- Remain decoupled from QuackTool UX or CLI logic

High-level functions built on top of these live in their respective `src/quack*` modules.

---

> This directory is for internal logic only. Production-facing APIs should always go through a `quack*` namespace.