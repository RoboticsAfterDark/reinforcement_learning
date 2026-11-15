"""Play the real cart pole using the keyboard.

Same env, same 3 actions and same reward the RL agent gets, to see how hard the task is.
Every episode starts with the pole hanging still, swing it up and keep it upright.
Controls: LEFT / RIGHT arrow keys push the cart, no key keeps the speed, 'q' quits.

Usage (needs root because the `keyboard` library reads raw key events on Linux):
    sudo .venv/bin/python real_world/00_play.py
"""
import keyboard
from real_cart_pole_env import RealCartPoleEnv, MAX_EPISODE_STEPS

def get_action_from_keyboard():
    # 0 push left, 1 push right, 2 no push
    if keyboard.is_pressed('left'):
        return 0
    if keyboard.is_pressed('right'):
        return 1
    return 2


def play():
    env = RealCartPoleEnv()

    print("--- Real Cart Pole Game ---")
    print("LEFT / RIGHT arrow keys push the cart, no key keeps the speed, 'q' quits.")
    print(f"Goal: swing up and keep the pole upright, reward per step is 1 upright and 0 hanging (max {MAX_EPISODE_STEPS})")

    best_reward = 0
    try:
        while True:
            state, info = env.reset()
            terminated = False
            truncated = False
            episode_reward = 0

            while (not terminated and not truncated):
                action = get_action_from_keyboard()
                state, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward

                # check for quit key
                if keyboard.is_pressed('q'):
                    print("quitting the game.")
                    return

            # truncated = survived all steps, terminated = x limit or firmware event
            end_reason = "time up" if truncated else f"cart limit {info['messages']}"
            best_reward = max(best_reward, episode_reward)
            print(f"Episode reward: {episode_reward:.1f} ({end_reason}), best: {best_reward:.1f}")

    except KeyboardInterrupt:
        print("\nGame interrupted.")

    finally:
        # stops the cart and frees the port
        env.close()
        print(f"Game Over! Best episode reward: {best_reward:.1f}")


if __name__ == '__main__':
    play()
