# Visa Agent

AI-powered Visa Application Assistant built with LangGraph.

## Installation

```bash
pip install -e .
```

## Usage

```bash
cd visa_agent
python main.py
```

## Project Structure

```
visa_agent/
├── main.py              # Entry point
├── state.py             # State definition
├── pyproject.toml       # Project configuration
├── nodes/               # Individual node functions
│   ├── intent_analyzer.py
│   ├── greetings.py
│   ├── general_enquiry.py
│   └── visa_application.py
├── graph/               # Graph construction
│   └── builder.py
├── config/              # Configuration
│   └── settings.py
└── utils/               # Utilities
    └── prompts.py
```
