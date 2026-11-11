"""Gym env for the real cart pole.

Same reset(), step(), action space and observation [x, x_dot, theta, theta_dot]
as gym.make("CartPole-v1"), or at least tried to make it same!

Swing up: every episode starts with the pole hanging still at the bottom,
the agent has to swing it up and keep it upright.
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from cart_pole_serial import CartPoleSerial, PORT

# episode ends when the cart is too far from center
# firmware soft limits are at +-0.27 m, end the episode before them
X_THRESHOLD = 0.25
MAX_EPISODE_STEPS = 500 # truncated after this many steps, 10 s at 50 Hz

# episode starts when the pole hangs still for STILL_TICKS
STILL_SPEED = 1.0 # rad/s, one encoder count per tick is 0.87 rad/s
STILL_TICKS = 50 # 1 s at 50 Hz

# firmware stops the cart if no action comes for this long, safety
WATCHDOG_MS = 100


def wrap_angle(angle):
    # wrap to [-pi, pi)
    return (angle + np.pi) % (2 * np.pi) - np.pi


class RealCartPoleEnv(gym.Env):
    def __init__(self, port=PORT):
        super().__init__()

        self.action_space = spaces.Discrete(2) # 0 push left, 1 push right
        # X_THRESHOLD multiply by 2 because, last observation might fall outside if not use this
        # theta is wrapped so it is always in [-pi, pi)
        high = np.array([X_THRESHOLD * 2, np.inf, np.pi, np.inf], dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        self.cart_pole = CartPoleSerial(port)
        self.cart_pole.set_watchdog(WATCHDOG_MS)

        self.num_steps = 0

    def to_observation(self, raw_observation):
        # firmware theta: 0 = hanging, gym theta: 0 = upright
        # so shift by pi and wrap, hanging becomes +-pi
        x, x_dot, theta_from_bottom, theta_dot = raw_observation
        theta = wrap_angle(theta_from_bottom - np.pi)
        return np.array([x, x_dot, theta, theta_dot], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # home every episode, moves the cart to the center and fixes skipped steps
        self.cart_pole.stop()
        self.cart_pole.home()
        self.cart_pole.start_stream()

        # wait until the pole hangs still
        print("Waiting for the pole to hang still...")
        still_ticks = 0
        while still_ticks < STILL_TICKS:
            time_ms, raw_observation = self.cart_pole.read_state()
            theta_dot = raw_observation[3]

            if abs(theta_dot) < STILL_SPEED:
                still_ticks += 1
            else:
                still_ticks = 0

        # theta = 0 when hanging, zero every episode so encoder drift never adds up
        self.cart_pole.zero_encoder()

        # first state after zeroing, gym theta = +-pi (hanging)
        time_ms, raw_observation = self.cart_pole.read_state()
        observation = self.to_observation(raw_observation)
        print("Go!")

        # events while waiting do not belong to this episode
        self.cart_pole.pop_messages()
        self.num_steps = 0
        return observation, {} # to keep structure: return observation, info

    def step(self, action):
        # send the action, then wait for the next state, the firmware sets the 50 Hz pace
        self.cart_pole.send_action(action)
        time_ms, raw_observation = self.cart_pole.read_state()
        observation = self.to_observation(raw_observation)
        self.num_steps += 1

        x, x_dot, theta, theta_dot = observation

        # any event (LIMIT, WATCHDOG, ERR) also ends the episode
        messages = self.cart_pole.pop_messages()

        terminated = bool(abs(x) > X_THRESHOLD or len(messages) > 0)
        truncated = self.num_steps >= MAX_EPISODE_STEPS

        # how upright the pole is: upright = 1, sideways = 0.5, hanging = 0
        reward = float((1 + np.cos(theta)) / 2)

        # stop the cart right away, don't wait for the next reset
        if terminated or truncated:
            self.cart_pole.stop()

        info = {'time_ms': time_ms, 'messages': messages}
        return observation, reward, terminated, truncated, info

    def close(self):
        self.cart_pole.close()
