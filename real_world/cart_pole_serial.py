"""Serial driver for the cart pole firmware.

send cmds to the cart pole and read its answers.
"""
import time
import numpy as np
import serial

PORT = '/dev/ttyACM0'
BAUD_RATE = 500000 # same as firmware


class CartPoleSerial:
    def __init__(self, port=PORT, baud_rate=BAUD_RATE):
        self.ser = serial.Serial(port, baud_rate, timeout=0.1)

        # lines that are not answers or states, events: eg LIMIT or WATCHDOG
        self.messages = []

        # opening the port resets the Mega, wait until the firmware sends READY
        self.wait_for('READY', timeout_s=5)

    def close(self):
        # always stop the cart before closing
        self.send('X')
        self.ser.close()

    # --- low level ---
    def send(self, cmd):
        # every cmd ends with a newline
        self.ser.write((cmd + '\n').encode())

    def read_line(self):
        # one line without the newline, or None if nothing came before the timeout
        line = self.ser.readline()
        if not line:
            return None
        return line.decode(errors='replace').strip()

    def wait_for(self, prefix, timeout_s):
        # read lines until one starts with prefix
        # ERR means the cmd failed, so raise
        # state lines are ignored, any other line is saved in messages
        end_time = time.monotonic() + timeout_s
        while time.monotonic() < end_time:
            line = self.read_line()
            if line is None:
                continue
            if line.startswith(prefix):
                return line
            if line.startswith('ERR'):
                raise RuntimeError(f"Firmware: {line}")
            if not line.startswith('S ') and not line.startswith('OK'):
                self.messages.append(line)
        raise TimeoutError(f"No '{prefix}' from firmware in {timeout_s} s")

    def pop_messages(self):
        # return saved messages and clear the list
        messages = self.messages
        self.messages = []
        return messages

    # --- cmds ---
    def home(self):
        # seek the switch, then move to the center
        self.send('H')
        self.wait_for('HOMED', timeout_s=30)

    def zero_encoder(self):
        # we should do it when the pole hangs still at the bottom
        self.send('Z')
        self.wait_for('OK Z', timeout_s=1)

    def set_watchdog(self, ms):
        # firmware stops the cart if no cmd comes for ms, 0 = off
        self.send(f'W {ms}')
        self.wait_for('OK W', timeout_s=1)

    def start_stream(self):
        self.send('G')
        self.wait_for('OK G', timeout_s=1)

    def stop(self):
        # stop the cart and the state stream
        self.send('X')
        self.wait_for('OK X', timeout_s=1)

    def send_action(self, action):
        # 0 push left, 1 push right, no answer, the next state is the answer
        self.send(f'A {int(action)}')

    # --- state ---
    def read_state(self, timeout_s=0.1):
        # wait for the next state line, returns (time_ms, [x, x_dot, theta, theta_dot])
        # if more states are already waiting the PC is behind, so keep only the newest one
        end_time = time.monotonic() + timeout_s
        state = None
        while state is None or self.ser.in_waiting > 0:
            if state is None and time.monotonic() > end_time:
                raise TimeoutError(f"No state from firmware in {timeout_s} s")

            line = self.read_line()
            if line is None:
                continue

            if line.startswith('S '):
                state = self.parse_state(line)
            elif not line.startswith('OK'):
                self.messages.append(line)

        return state

    def parse_state(self, line):
        # S <time_ms> <x> <x_dot> <theta> <theta_dot>
        # theta here is from the bottom (0 = hanging), the env converts it to gym (0 = upright)
        parts = line.split()
        time_ms = int(parts[1])
        observation = np.array([float(p) for p in parts[2:6]], dtype=np.float32)
        return time_ms, observation
