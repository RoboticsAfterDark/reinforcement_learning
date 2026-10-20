"""Play CartPole-v1 using the keyboard.

Move the cart left and right to keep the pole balanced upright, to see how hard the task is.
Controls: LEFT / RIGHT arrow keys push the cart, 'q' quits.
With no key pressed the cart is pushed left and right in turn (CartPole has no "do nothing" action).

Usage (needs root because the `keyboard` library reads raw key events on Linux):
    sudo .venv/bin/python 02_cart_pole/00_play.py
"""
import gymnasium as gym 
import keyboard
import numpy as np
movement = 0

def get_action_from_keyboard():
    
    global movement
    if movement == 0:
        movement = 1
    else:
        movement = 0

    if keyboard.is_pressed('left'):
        movement = 0

    elif keyboard.is_pressed('right'):
        movement = 1

    return np.array(movement)

def play():
    env = gym.make("CartPole-v1", render_mode="human")

    state, info = env.reset()
    total_reward = 0

    print("--- Cart Pole Game ---")
    print("Use LEFT arrow key for negative movement.")
    print("Use RIGHT arrow key for positive movement.")
    print("If no key is pressed, movement will be zero.")
    print("Press 'q' to quit.")
    print("Goal: Swing up and balance the pendulum at the top (angle 0).")
   
    try:
        while True:
            env.render()

            #get action from keyboard
            action = get_action_from_keyboard()

            #take a step in env
            state, reward, done, truncated, info = env.step(action)

            total_reward += reward

            #check for quit key
            if keyboard.is_pressed('q'):
                print("quitting the game.")
                break

    except KeyboardInterrupt:
        print("\nGame interrupted.")

    finally:
        env.close()
        print(f"Game Over! Total Reward: {total_reward:.2f}")

if __name__=='__main__':
    play()
