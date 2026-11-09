#define dirPin 5
#define stepPin 4

// I have confirmed this, still download datasheet
// R100 resister = 0.1 ohm, I_max = 1.0A 
// so Vref = I_max * (8 * 0.1) = 0.64V (between tiny nob and gnd)
const int STEPS_PER_REV = 200;

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  Serial.begin(500000);
}

void loop() {
  digitalWrite(dirPin, HIGH);

  // Spin motor one rotation slowly
  for(int x = 0; x < STEPS_PER_REV; x++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(2000);
  }

  delay(1000);
  Serial.println("Its running");
  digitalWrite(dirPin, LOW);

  // Spin motor two rotation fast
  for(int x = 0; x < STEPS_PER_REV * 2; x++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(1000);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(1000);
  }
}
