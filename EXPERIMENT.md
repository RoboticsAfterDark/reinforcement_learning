# Experiments

| Experiment | Date | Commit |
|---|---|---|
| [experiment001](#experiment001) | 2026-11-23 | [`b214432`](https://github.com/abhismirai42/reinforcement_learning/commit/b214432fc912ab377c2dd5ef3b18633a6a940876) |

---

## experiment001

**Question:** How good is our discrete SAC implementation compared to an SB3 SAC on the same env?

**Setup**
- Env: gym CartPole-v1.
- Ours: `02_cart_pole/06_Soft_Actor_Critic.ipynb`: 1 critic, hard target copy every 500 steps, alpha 0.2 fixed, lr 1e-3, batch 64, nets 64 x 64, replay 100 000.
- SB3: `02_cart_pole/06_Soft_Actor_Critic_sb3.ipynb`: stable-baselines3 2.9.2 SAC defaults: 2 critics, soft target tau 0.005, automatic alpha, lr 3e-4, batch 256, nets 256 x 256, replay 1 000 000. Its continuous action a maps to left (a < 0) or right (a >= 0), so the physics are the same.
- Both: 1 gradient step per env step, 2500 episodes x 3 runs, checkpoint every 500 episodes.

**Procedure:** Ran each notebook's 3 runs from scratch. Ours ~15 to 20 min per run, SB3 ~2 h per run. Plotted the 50 episode moving average of every run.

![our SAC vs SB3 SAC](experiments/experiment001/our_sac_vs_sb3_sac.png)

**Observations**
- **O1** All 6 runs reach a 50 episode average of 400.
- **O2** SB3 reaches 400 around episode 250 (2 of 3 runs); ours around episode 400 to 500.
- **O3** After learning, SB3 stays near 500 with short dips (lowest ~230). Ours keeps crashing and recovering, run 1 down to ~20, several times.
- **O4** Episode 1250 to 2500 mean: ours 216, 397, 356; SB3 480, 498, 470.

**Questions & next**
- Same algorithm family and env, so is the crashing (O3) caused by one of the differences in Setup? They all change at once here (e.g. 1 vs 2 critics, hard vs soft target update, fixed vs automatic alpha, lr 1e-3 vs 3e-4), so this experiment cannot tell which.
- Next: add them to ours one at a time
