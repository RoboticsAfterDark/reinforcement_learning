// cmds from PC:
// G: go, start sending the state every control tick (TODO control tick?)
// X: stop, stop sending the state
// Z: zero the encoder, do it when the pole hangs still at the bottom

// --- encoder ---
#define encA 2  // white pin
#define encB 3  // green pin
// counting only rising edges of A, so 360 counts per rev (1 degree per count)
#define ENCODER_COUNTS_PER_REV 360
const float RAD_PER_COUNT = 2.0 * PI / ENCODER_COUNTS_PER_REV;
volatile long encoder_count = 0;
long prev_encoder_count = 0;

// control loop timing 50 Hz
#define CONTROL_PERIOD_US 20000UL
unsigned long tick_scheduled_us = 0;  // planned tick time, +20 ms every tick, keeps 50 Hz
unsigned long prev_tick_us = 0;       // actual time of last tick, for dt

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

  Serial.begin(BAUD_RATE);
  Serial.println("READY");

  tick_scheduled_us = micros();
  prev_tick_us = tick_scheduled_us;
}

void loop() {
  // check for new cmds
  readCommand();

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

// --- control loop ---
void controlTick(unsigned long now_us) {
  long count = readEncoderCount();

  float dt = (now_us - prev_tick_us) * 1e-6;

  // check the cart pole in gym init angle I think its upright zero
  float theta = count * RAD_PER_COUNT;
  // theta_dot = change in angle / change in time
  float theta_dot = (count - prev_encoder_count) * RAD_PER_COUNT / dt;

  prev_encoder_count = count;
  prev_tick_us = now_us;

  if (sending_state) {
    sendState(now_us, theta, theta_dot);
  }
}

// --- serial communication ---
// S <time_ms> <theta> <theta_dot>
void sendState(unsigned long now_us, float theta, float theta_dot) {
  Serial.print("S ");
  Serial.print(now_us / 1000);
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
      sending_state = false;
      Serial.println("OK X");
      break;

    case 'Z':
      zeroEncoder();
      Serial.println("OK Z");
      break;

    default:
      Serial.print("ERR unknown command: ");
      Serial.println(cmd);
      break;
  }
}
