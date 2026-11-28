"""Hanmatek HM310T power supply control:

Terminal:
    .venv/bin/python real_world/power_supply.py               # status
    .venv/bin/python real_world/power_supply.py on            # output on (keeps the set voltage and current)
    .venv/bin/python real_world/power_supply.py off           # output off
    .venv/bin/python real_world/power_supply.py set 24 4      # set 24 V, 4 A limit (output stays as it is)
    .venv/bin/python real_world/power_supply.py protect 24 1.5  # over voltage 24 V, over current 1.5 A
    .venv/bin/python real_world/power_supply.py ocp on        # over current protection on (or off), like the OCP button

Experiment script:
    from power_supply import HM310T
    with HM310T(off_at_end=True) as psu:   # output goes off when the block ends, also on a crash
        psu.turn_on(voltage=24, current=3)
        print(psu.status())
"""
import sys
import time

from hm310t import IncompatibleDeviceError, PowerSupply

PORT = '/dev/ttyUSB0'

# model rating in register 0x0003: library accepts only 3010 (30 V, 10 A), ours is 3210 (32 V, 10 A), same registers
KNOWN_SPECIFICATIONS = (3010, 3210)

SETTLE_S = 0.5 # wait after switching, so the live values are real

# OCP button on/off, 1 = on, 0 = off
OCP_SWITCH = 0x0043


class HM310T(PowerSupply):
    def __init__(self, port=PORT, off_at_end=False):
        super().__init__(port)
        # the library already turns the output off on a crash, this also does it on a normal end
        self.off_at_end = off_at_end

    def _check_specification(self):
        specification = self.read_raw_register(0x0003)
        if specification not in KNOWN_SPECIFICATIONS:
            raise IncompatibleDeviceError(f"register 0x0003 reads {specification}, expected one of {KNOWN_SPECIFICATIONS}")

    def set(self, voltage, current):
        # setpoints only, does not switch the output
        self.voltage = voltage
        self.current = current

    def protect(self, ovp, ocp):
        # the supply cuts the output above these
        self.ovp = ovp
        self.ocp = ocp

    def set_ocp_on(self, on):
        # the OCP limit only works when this is on
        self._transport.write_register(OCP_SWITCH, int(on))

    def turn_on(self, voltage=None, current=None):
        if voltage is not None and current is not None:
            self.set(voltage, current)
        self.output_enabled = True
        time.sleep(SETTLE_S)

    def turn_off(self):
        self.output_enabled = False
        time.sleep(SETTLE_S)

    def status(self):
        measurement = self.read_measurement()
        return {
            'set_voltage': self.voltage,
            'set_current': self.current,
            'output_on': self.output_enabled,
            'voltage': measurement.voltage,  # live, 0 when the output is off
            'current': measurement.current,
            'power': measurement.power,
            'ovp': self.ovp,
            'ocp': self.ocp,
            'ocp_on': bool(self.read_raw_register(OCP_SWITCH)),
        }

    def __exit__(self, exc_type, *exc):
        if self.off_at_end and exc_type is None:
            self.output_enabled = False
        super().__exit__(exc_type, *exc)


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'status'
    values = [float(v) for v in sys.argv[2:]] if command in ('set', 'protect') else []

    with HM310T() as psu:
        if command == 'on':
            psu.turn_on()
        elif command == 'off':
            psu.turn_off()
        elif command == 'set':
            psu.set(*values)
        elif command == 'protect':
            psu.protect(*values)
        elif command == 'ocp' and sys.argv[2:] in (['on'], ['off']):
            psu.set_ocp_on(sys.argv[2] == 'on')
        elif command != 'status':
            sys.exit(f"unknown command '{command}', use: status, on, off, set V A, protect V A, ocp on/off")

        for name, value in psu.status().items():
            print(f"{name:12s} {value}")
