// -------------------------------
// Spiderbot Arduino Control Sketch
// -------------------------------

const int motorLeftForward = 2;
const int motorLeftBackward = 3;
const int motorRightForward = 4;
const int motorRightBackward = 5;

// Adjust delays for movement duration
const int moveDuration = 500; // milliseconds

void setup() {
  Serial.begin(9600);  // Match baud rate with Raspberry Pi
  pinMode(motorLeftForward, OUTPUT);
  pinMode(motorLeftBackward, OUTPUT);
  pinMode(motorRightForward, OUTPUT);
  pinMode(motorRightBackward, OUTPUT);

  Serial.println("Arduino Spiderbot ready!");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    Serial.print("Received command: ");
    Serial.println(cmd);

    switch(cmd) {
      case 'A': // LEFT
        moveLeft();
        break;
      case 'B': // RIGHT
        moveRight();
        break;
      case 'C': // FRONT
        moveForward();
        break;
      case 'D': // BACK
        moveBackward();
        break;
      default:
        Serial.println("Unknown command!");
    }
  }
}

// -------------------------------
// Movement Functions
// -------------------------------
void moveLeft() {
  Serial.println("Moving LEFT");
  digitalWrite(motorLeftBackward, HIGH);
  digitalWrite(motorRightForward, HIGH);
  delay(moveDuration);
  stopMotors();
}

void moveRight() {
  Serial.println("Moving RIGHT");
  digitalWrite(motorLeftForward, HIGH);
  digitalWrite(motorRightBackward, HIGH);
  delay(moveDuration);
  stopMotors();
}

void moveForward() {
  Serial.println("Moving FORWARD");
  digitalWrite(motorLeftForward, HIGH);
  digitalWrite(motorRightForward, HIGH);
  delay(moveDuration);
  stopMotors();
}

void moveBackward() {
  Serial.println("Moving BACKWARD");
  digitalWrite(motorLeftBackward, HIGH);
  digitalWrite(motorRightBackward, HIGH);
  delay(moveDuration);
  stopMotors();
}

void stopMotors() {
  digitalWrite(motorLeftForward, LOW);
  digitalWrite(motorLeftBackward, LOW);
  digitalWrite(motorRightForward, LOW);
  digitalWrite(motorRightBackward, LOW);
}
void setup() {
  // put your setup code here, to run once:

}

void loop() {
  // put your main code here, to run repeatedly:

}
