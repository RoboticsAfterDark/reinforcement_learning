"""Gym env for a sim cart pole that behaves like the real one (real_world/real_cart_pole_env.py).

TODO(abhi): claude generated read if needed
Gym's CartPole-v1 physics (masses, 1 m pole, 10 N push, 0.02 s step, 2.4 m track) with the real env's rules:
1. 3 actions: 0 push left, 1 push right, 2 no push
2. reward: the real env's compute_reward(), imported so both always match
3. swing up: every episode starts with the pole hanging at the bottom (gym's 12 deg end is removed)
4. spinning faster than the real env's MAX_THETA_DOT ends the episode, like on the real cart
5. info['messages'] like the real env ('SPIN ...')
"""
import os
import sys

import numpy as np
from gymnasium import spaces
from gymnasium.envs.classic_control.cartpole import CartPoleEnv

# use the real env's reward and spin limit, so sim and real always give the same reward
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'real_world'))
from real_cart_pole_env import MAX_THETA_DOT, compute_reward, wrap_angle  # noqa: E402


class SimCartPoleEnv(CartPoleEnv):
    def __init__(self, render_mode=None):
        # gym's CartPoleEnv sets the physics: masses, pole length, force, 0.02 s step, 2.4 m track
        super().__init__(render_mode=render_mode)

        self.action_space = spaces.Discrete(3) # 0 push left, 1 push right, 2 no push
        # X threshold multiply by 2 because, last observation might fall outside if not use this
        # theta is wrapped so it is always in [-pi, pi)
        high = np.array([self.x_threshold * 2, np.inf, np.pi, np.inf], dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        # gym's reset: small random numbers around 0 for all 4 states (pole upright)
        super().reset(seed=seed, options=options)

        # swing up: add pi to theta so the pole hangs, gym theta = +-pi (hanging)
        x, x_dot, theta, theta_dot = self.state
        self.state = np.array([x, x_dot, wrap_angle(theta + np.pi), theta_dot])
        return np.array(self.state, dtype=np.float32), {} # to keep structure: return observation, info

    def step(self, action):
        x, x_dot, theta, theta_dot = self.state

        # 0 push left, 1 push right, 2 no push = no force
        if action == 1:
            force = self.force_mag
        elif action == 0:
            force = -self.force_mag
        else:
            force = 0.0

        # gym's physics, same as CartPoleEnv.step
        costheta = np.cos(theta)
        sintheta = np.sin(theta)
        temp = (force + self.polemass_length * np.square(theta_dot) * sintheta) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta * temp) / (
            self.length * (4.0 / 3.0 - self.masspole * np.square(costheta) / self.total_mass))
        xacc = temp - self.polemass_length * thetaacc * costheta / self.total_mass

        x = x + self.tau * x_dot
        x_dot = x_dot + self.tau * xacc
        theta = theta + self.tau * theta_dot
        theta_dot = theta_dot + self.tau * thetaacc

        # wrap theta so hanging stays +-pi, like the real env
        theta = wrap_angle(theta)
        self.state = np.array([x, x_dot, theta, theta_dot])
        observation = np.array(self.state, dtype=np.float32)

        # spinning too fast ends the episode, like the real env
        messages = []
        if abs(theta_dot) > MAX_THETA_DOT:
            messages.append(f'SPIN theta_dot {theta_dot:.1f} rad/s')

        # the cart leaving the track or spinning ends the episode, no 12 deg end (pole starts hanging)
        terminated = bool(abs(x) > self.x_threshold or len(messages) > 0)

        reward = compute_reward(theta, theta_dot)

        if self.render_mode == "human":
            self.render()

        # truncation is done by the TimeLimit wrapper, like gym.make does
        info = {'messages': messages}
        return observation, reward, terminated, False, info
