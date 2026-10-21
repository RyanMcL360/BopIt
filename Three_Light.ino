// Three light blink
// Hold the button, LEDs on pins 8, 9, 10 light one after another, repeating.
// Release the button, the current cycle finishes, then all LEDs stay off until pressed again.
// Button wired between pin 2 and GND

const int BUTTON_PIN = 2;
const int LED_PINS[] = {8, 9, 10};
const int NUM_LEDS = 3;
const int STEP_MS = 300;

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
}

void loop() {
  // The button is only checked here, between cycles, so a full
  // cycle always completes even if the button is released partway through.
  if (digitalRead(BUTTON_PIN) == LOW) {
    for (int i = 0; i < NUM_LEDS; i++) {
      digitalWrite(LED_PINS[i], HIGH);
      delay(STEP_MS);
      digitalWrite(LED_PINS[i], LOW);
    }
  }
}
