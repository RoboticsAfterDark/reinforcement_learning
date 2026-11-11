// cmds from PC:
// G: go, start sending the state every control tick (TODO control tick?)
// X: stop, stop the cart and stop sending the state
// Z: zero the encoder, do it when the pole hangs still at the bottom
// H: home, find the limit switch then move the cart to the center (x = 0)
// A <action>: action, 0 push left, 1 push right
// one A = one env step, changes the cart speed by one push action only works after homing

#include <AccelStepper.h>

// --- encoder ---
#define encA 2  // white pin
#define encB 3  // green pin
// counting only rising edges of A, so 360 counts per rev (1 degree per count)
#define ENCODER_COUNTS_PER_REV 360
const float RAD_PER_COUNT = 2.0 * PI / ENCODER_COUNTS_PER_REV;
volatile long encoder_count = 0;
long prev_encoder_count = 0;

// --- stepper ---
#define dirPin 5
#define stepPin 4

// stepper
#define STEPS_PER_REV 200    // full step mode so 200 steps per rev
#define METERS_PER_REV 0.04  // belt with 20 tooth pulley so 40 mm per rev
const float METERS_PER_STEP = METERS_PER_REV / STEPS_PER_REV;
// TODO(abhi): adjest if needed
#define MAX_STEPS_PER_S 1000
long prev_cart_steps = 0;

// AccelStepper::DRIVER because we are using stepper driver
// need to specify dir and step pins
AccelStepper stepper(AccelStepper::DRIVER, stepPin, dirPin);

// track
#define TRACK_LENGTH_M 0.40       // meters
#define SOFT_LIMIT_MARGIN_M 0.03  // soft limits stop the cart before it reaches the ends

// homing
#define HOMING_SPEED 200  // slow
// if the switch is not found after this many steps something is wrong
const long HOMING_MAX_STEPS = 1.2 * TRACK_LENGTH_M / METERS_PER_STEP;
long homing_start_steps = 0;

// x = 0 is the center of the track so the switch is at -TRACK_LENGTH_M / 2
const long HOME_STEPS = -(TRACK_LENGTH_M / 2) / METERS_PER_STEP;
const long SOFT_LIMIT_STEPS = (TRACK_LENGTH_M / 2 - SOFT_LIMIT_MARGIN_M) / METERS_PER_STEP;

// control loop timing 50 Hz
#define CONTROL_PERIOD_US 20000UL
unsigned long tick_scheduled_us = 0;  // planned tick time, +20 ms every tick, keeps 50 Hz
unsigned long prev_tick_us = 0;       // actual time of last tick, for dt

// action
// one action changes the speed by CART_ACCEL_MPS2 for one control period
// 2 m/s^2 * 0.02 s / (0.0002 m/step) = 200 steps/s per action
#define CART_ACCEL_MPS2 2.0
const float SPEED_CHANGE_PER_ACTION = CART_ACCEL_MPS2 * (CONTROL_PERIOD_US * 1e-6) / METERS_PER_STEP;

// what the cart is doing right now
// NOT_HOMED: position unknown, actions are not allowed
// HOMING: moving slowly towards the limit switch
// MOVING_TO_CENTER: switch found, moving to x = 0
// READY: position known, actions are allowed, soft limits are on
enum Mode { NOT_HOMED, HOMING, MOVING_TO_CENTER, READY };
Mode mode = NOT_HOMED;

// --- limit switch ---
#define limitPin 6

// --- serial ---
#define BAUD_RATE 500000

#define CMD_BUFFER_SIZE 32
char cmd_buffer[CMD_BUFFER_SIZE];
byte cmd_length = 0;  // number of characters in cmd_buffer so far
bool sending_state = false;

void setup() {
  // use external 5k pullup resistor
  pinMode(encA, INPUT);
  pinMode(encB, INPUT);

  // using encA rising edge check encB value
  attachInterrupt(digitalPinToInterrupt(encA), encoderISR, RISING);

  stepper.setMaxSpeed(MAX_STEPS_PER_S);
  stepper.setSpeed(0);

  // use external 5k pullup resistor
  pinMode(limitPin, INPUT);

  Serial.begin(BAUD_RATE);
  Serial.println("READY");

  tick_scheduled_us = micros();
  prev_tick_us = tick_scheduled_us;
}

void loop() {
  // one step if a step interval (1 / speed) has passed, else returns right away
  // keeps a constant speed, so loop must never block
  stepper.runSpeed();

  // check for new cmds
  readCommand();

  // safety and homing run every loop.
  checkSafety();
  updateHoming();

  // run controlTick once every control period
  unsigned long now_us = micros();
  if (now_us - tick_scheduled_us >= CONTROL_PERIOD_US) {
    tick_scheduled_us += CONTROL_PERIOD_US;
    controlTick(now_us);
  }
}

// --- encoder ---
void encoderISR() {
  if (digitalRead(encB) == LOW) {
    encoder_count++;
  } else {
    encoder_count--;
  }
}

// the Mega is 8-bit, so a long is read in 4 parts, don't want the interrupt to
// change it in between
long readEncoderCount() {
  noInterrupts();
  long count = encoder_count;
  interrupts();
  return count;
}

// zero the encoder count
// disable the interrupts just in case
void zeroEncoder() {
  noInterrupts();
  encoder_count = 0;
  interrupts();

  // need reset previous count too!
  prev_encoder_count = 0;
}

// --- stepper ---
void stopCart() {
  stepper.setSpeed(0);
}

// 0 push left, 1 push right
void applyAction(int action) {
  float speed = stepper.speed();
  if (action == 1) {
    speed += SPEED_CHANGE_PER_ACTION;
  } else {
    speed -= SPEED_CHANGE_PER_ACTION;
  }

  // at a soft limit don't speed up further out
  long cart_steps = stepper.currentPosition();
  if ((cart_steps >= SOFT_LIMIT_STEPS && speed > 0) || (cart_steps <= -SOFT_LIMIT_STEPS && speed < 0)) {
    speed = 0;
  }

  // AccelStepper limits it to MAX_STEPS_PER_S
  stepper.setSpeed(speed);
}

// --- control loop ---
void controlTick(unsigned long now_us) {
  long count = readEncoderCount();
  long cart_steps = stepper.currentPosition();

  float dt = (now_us - prev_tick_us) * 1e-6;

  // x = 0 at the center of the track after homing
  float x = cart_steps * METERS_PER_STEP;
  float x_dot = (cart_steps - prev_cart_steps) * METERS_PER_STEP / dt;

  // check the cart pole in gym init angle I think its upright zero
  float theta = count * RAD_PER_COUNT;
  // theta_dot = change in angle / change in time
  float theta_dot = (count - prev_encoder_count) * RAD_PER_COUNT / dt;

  prev_encoder_count = count;
  prev_cart_steps = cart_steps;
  prev_tick_us = now_us;

  if (sending_state) {
    sendState(now_us, x, x_dot, theta, theta_dot);
  }
}

// --- limit switch and homing ---
bool limitPressed() {
  return digitalRead(limitPin) == LOW;
}

void startHoming() {
  if (limitPressed()) {
    Serial.println("ERR limit switch already pressed, move the cart away by hand or check wiring");
    return;
  }

  homing_start_steps = stepper.currentPosition();
  stepper.setSpeed(-HOMING_SPEED);
  mode = HOMING;
  Serial.println("OK H");
}

void updateHoming() {
  if (mode == HOMING) {
    if (limitPressed()) {
      // found the switch
      stepper.setCurrentPosition(HOME_STEPS);
      prev_cart_steps = HOME_STEPS;

      stepper.setSpeed(HOMING_SPEED);
      mode = MOVING_TO_CENTER;
    }
    else if (homing_start_steps - stepper.currentPosition() > HOMING_MAX_STEPS) {
      stopCart();
      mode = NOT_HOMED;
      Serial.println("ERR limit switch not found");
    }
  }
  else if (mode == MOVING_TO_CENTER) {
    if (stepper.currentPosition() >= 0) {
      stopCart();
      mode = READY;
      Serial.println("HOMED");
    }
  }
}

// safety check
void checkSafety() {
  // switch hit while moving towards it after homing means steps were skipped
  // so the position is wrong
  if (mode != HOMING && stepper.speed() < 0 && limitPressed()) {
    stopCart();
    mode = NOT_HOMED;
    Serial.println("ERR limit switch hit, position lost, home again with H");
  }

  // soft limits, only stop if moving further out, moving back in is allowed
  if (mode == READY) {
    long cart_steps = stepper.currentPosition();
    if ((cart_steps >= SOFT_LIMIT_STEPS && stepper.speed() > 0) ||
        (cart_steps <= -SOFT_LIMIT_STEPS && stepper.speed() < 0)) {
      stopCart();
      Serial.println("LIMIT soft limit reached, cart stopped");
    }
  }
}

// --- serial communication ---
// S <time_ms> <x> <x_dot> <theta> <theta_dot>
void sendState(unsigned long now_us, float x, float x_dot, float theta, float theta_dot) {
  Serial.print("S ");
  Serial.print(now_us / 1000);
  Serial.print(' ');
  Serial.print(x, 4);
  Serial.print(' ');
  Serial.print(x_dot, 4);
  Serial.print(' ');
  Serial.print(theta, 4);
  Serial.print(' ');
  Serial.println(theta_dot, 4);
}

// collect characters until a newline, then handle the cmd
void readCommand() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      cmd_buffer[cmd_length] = '\0';  // end of string
      handleCommand(cmd_buffer);
      cmd_length = 0;
    } else if (cmd_length < CMD_BUFFER_SIZE - 1) {
      cmd_buffer[cmd_length] = c;
      cmd_length++;
    }
  }
}

// function to handle the cmds
void handleCommand(char *cmd) {
  if (cmd[0] == '\0') {
    return;  // empty line
  }

  switch (cmd[0]) {
    case 'G':
      sending_state = true;
      Serial.println("OK G");
      break;

    case 'X':
      stopCart();
      sending_state = false;
      if (mode == HOMING) {
        mode = NOT_HOMED;
      }
      else if (mode == MOVING_TO_CENTER) {
        mode = NOT_HOMED;
      }
      Serial.println("OK X");
      break;

    case 'Z':
      zeroEncoder();
      Serial.println("OK Z");
      break;

    case 'H':
      startHoming();
      break;

    case 'A':
      {
        if (mode != READY) {
          Serial.println("ERR not ready, send H first");
          break;
        }
        int action = atoi(cmd + 1);  // atoi: string to int
        if (action != 0 && action != 1) {
          Serial.print("ERR action must be 0 or 1: ");
          Serial.println(cmd);
          break;
        }
        applyAction(action);
        break;
      }

    default:
      Serial.print("ERR unknown command: ");
      Serial.println(cmd);
      break;
  }
}
