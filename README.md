# Reinforcement Learning

Let's learn RL!

## Installation

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and its dependencies.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Check installation by playing pendulum yourself
sudo .venv/bin/python 01_pendulum/00_play.py
```

## Environments and Methods

- **[Frozen Lake](00_frozen_lake/)**
  - [Value Iteration](00_frozen_lake/01_value_iteration.ipynb)
- **[Pendulum](01_pendulum/)**
  - [Play it yourself](01_pendulum/00_play.py)
  - [Value Iteration](01_pendulum/01_value_iteration.ipynb)
