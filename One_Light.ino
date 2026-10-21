// One light blink
// Hold the button, LED on pin 8 blinks. Release the button, LED turns off.
// Button wired between pin 2 and GND 

const int BUTTON_PIN = 2;
const int LED_PIN = 8;
const int BLINK_MS = 250;  // short delay so the LED reacts quickly to release

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {   // button is pressed
    digitalWrite(LED_PIN, HIGH);
    delay(BLINK_MS);
    digitalWrite(LED_PIN, LOW);
    delay(BLINK_MS);
  } else {                                // button released
    digitalWrite(LED_PIN, LOW);
  }
}
