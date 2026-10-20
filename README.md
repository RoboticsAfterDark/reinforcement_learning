# Reinforcement Learning

Let's learn RL!

We will be following these lectures:

- [David Silver (DeepMind)](https://youtube.com/playlist?list=PLqYmG7hTraZDM-OYHWgPebj2MfCFzFObQ)
- [Sergey Levine (UC Berkeley)](https://youtube.com/playlist?list=PLKq1TCpsv3Y4)
- [Russ Tedrake (MIT)](https://youtube.com/playlist?list=PLkx8KyIQkMfU5szP43GlE_S1QGSPQfL9s)

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
  - [Monte Carlo Control](00_frozen_lake/02_monte_carlo_control.ipynb)
  - [TD Control or SARSA](00_frozen_lake/03_TD_control_or_SARSA.ipynb)
- **[Pendulum](01_pendulum/)**
  - [Play it yourself](01_pendulum/00_play.py)
  - [Value Iteration](01_pendulum/01_value_iteration.ipynb)
  - [Monte Carlo Control](01_pendulum/03_monte_carlo_control.ipynb)
  - [TD Control or SARSA](01_pendulum/04_TD_control_or_SARSA.ipynb)
- **[Cart Pole](02_cart_pole/)**
  - [Play it yourself](02_cart_pole/00_play.py)
