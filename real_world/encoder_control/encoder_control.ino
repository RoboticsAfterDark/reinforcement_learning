#define encA_W 2
#define encB_G 3 

volatile int temp, counter = 0;

void setup() {
  // I was unable to find the datasheet
  // Taiss/AB 2 phase Incremental Rotary Encoder 360P/R DC 5-24v Wide Voltage Power Supply 6mm Shaft 360P/R 
  // It can only pull low so need to add pull up resistor
  pinMode(encA_W, INPUT);
  pinMode(encB_G, INPUT);

  Serial.begin(500000);

  // Using encA rissing edge check encB value
  attachInterrupt(digitalPinToInterrupt(encA_W), count, RISING);
}

void loop() {
  if (counter != temp){
    Serial.print("Counter: ");
    Serial.println(counter);
    temp = counter;
  }

}

void count(){
  if (digitalRead(encB_G)==LOW){
    counter++;
  }
  else{
    counter--;
  }
}