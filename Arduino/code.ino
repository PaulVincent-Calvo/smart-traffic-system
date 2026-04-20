const int redPin = 8;
const int yellowPin = 9;
const int greenPin = 10;

String command = "";

void setup() {
  pinMode(redPin, OUTPUT);
  pinMode(yellowPin, OUTPUT);
  pinMode(greenPin, OUTPUT);

  Serial.begin(9600);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      processCommand(command);
      command = "";
    } else {
      command += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();

  if (cmd == "R") {
    setLights(HIGH, LOW, LOW);
  }
  else if (cmd == "G") {
    setLights(LOW, LOW, HIGH);
  }
  else if (cmd == "Y") {
    setLights(LOW, HIGH, LOW);
  }
  else {
    setLights(LOW, LOW, LOW);
  }
}

void setLights(int r, int y, int g) {
  digitalWrite(redPin, r);
  digitalWrite(yellowPin, y);
  digitalWrite(greenPin, g);
}