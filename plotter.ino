/*
 * DIYPlotterOS - G-code interpreter
 * -----------------------------------------------------
 * Reads G-code lines over USB serial and drives two
 * AFMotor (L293D shield) steppers + a pen servo.
 *
 * Supported G-code:
 *   G0 / G1 X.. Y..   -> move (linear interpolated, both used the same way here)
 *   G90               -> absolute positioning (default)
 *   G91               -> relative positioning
 *   M3                -> pen down
 *   M5                -> pen up
 *   ; or ( ... )      -> comments, ignored
 *
 * After each line is processed, sends "ok\n" back over
 * serial so the PC-side sender knows to send the next line.
 *
 * ASSUMPTIONS (check these against your hardware!):
 *   - Stepper on AFMotor port 1 = X axis
 *   - Stepper on AFMotor port 2 = Y axis
 *   - Physical motor = 48 steps/revolution (only affects speed timing)
 *   - X_STEPS / Y_STEPS in config.h = steps per millimeter
 */

#include <AFMotor.h>
#include <Servo.h>
#include "config.h"

#define STEPPER_STEPS_PER_REV 48   // adjust if your DVD stepper differs

AF_Stepper stepperX(STEPPER_STEPS_PER_REV, 2);
AF_Stepper stepperY(STEPPER_STEPS_PER_REV, 1);
Servo penServo;

float curX = 0, curY = 0;   // current position in mm
bool absoluteMode = true;
bool penIsDown = false;

int lastDirX = 0;  // 0 = unknown (no compensation yet), FORWARD, or BACKWARD
int lastDirY = 0;

unsigned long stepDelayMicros;

#define LINE_BUFFER_LENGTH 128
char lineBuffer[LINE_BUFFER_LENGTH];

void setup() {
  Serial.begin(9600);
  penServo.attach(SERVO_PIN);
  penUp();

  stepperX.setSpeed(MOTOR_SPEED);
  stepperY.setSpeed(MOTOR_SPEED);

  // microseconds per single step, derived from MOTOR_SPEED (RPM)
  stepDelayMicros = 60000000UL / ((unsigned long)MOTOR_SPEED * STEPPER_STEPS_PER_REV);

  Serial.println("DIYPlotterOS ready");
}

void loop() {
  if (readLine()) {
    processLine(lineBuffer);
    Serial.println("ok");
  }
}

// ---------- Serial line reading ----------
bool readLine() {
  static uint8_t idx = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (idx > 0) {
        lineBuffer[idx] = '\0';
        idx = 0;
        return true;
      }
    } else if (idx < LINE_BUFFER_LENGTH - 1) {
      lineBuffer[idx++] = c;
    }
  }
  return false;
}

// ---------- G-code line parsing ----------
void processLine(char* line) {
  // strip comments
  char* semi = strchr(line, ';');
  if (semi) *semi = '\0';
  char* paren = strchr(line, '(');
  if (paren) *paren = '\0';

  if (line[0] == '\0') return;

  float xVal = curX, yVal = curY;
  bool hasX = false, hasY = false;
  int gCode = -1, mCode = -1;

  char* tok = line;
  while (*tok) {
    while (*tok == ' ') tok++;
    if (*tok == '\0') break;

    char letter = toupper(*tok);
    tok++;
    float value = atof(tok);

    switch (letter) {
      case 'G': gCode = (int)value; break;
      case 'M': mCode = (int)value; break;
      case 'X': xVal = value; hasX = true; break;
      case 'Y': yVal = value; hasY = true; break;
    }
    // skip to next space
    while (*tok && *tok != ' ') tok++;
  }

  if (gCode == 90) { absoluteMode = true; return; }
  if (gCode == 91) { absoluteMode = false; return; }

  if (mCode == 3) { penDown(); return; }
  if (mCode == 5) { penUp(); return; }

  if (gCode == 0 || gCode == 1) {
    float targetX = curX;
    float targetY = curY;
    if (absoluteMode) {
      if (hasX) targetX = xVal;
      if (hasY) targetY = yVal;
    } else {
      if (hasX) targetX = curX + xVal;
      if (hasY) targetY = curY + yVal;
    }
    moveTo(targetX, targetY);
  }
}

// ---------- Pen control ----------
void penUp() {
  penServo.write(PEN_UP);
  delay(150);
  penIsDown = false;
}

void penDown() {
  penServo.write(PEN_DOWN);
  delay(150);
  penIsDown = true;
}

// ---------- Motion: Bresenham line interpolation ----------
void moveTo(float targetX, float targetY) {
  // Clamp to soft limits so we never grind the rail
  if (targetX < X_MIN) targetX = X_MIN;
  if (targetX > X_MAX) targetX = X_MAX;
  if (targetY < Y_MIN) targetY = Y_MIN;
  if (targetY > Y_MAX) targetY = Y_MAX;

  long stepsX = lround((targetX - curX) * X_STEPS);
  long stepsY = lround((targetY - curY) * Y_STEPS);

  int dirX = (stepsX >= 0) ? FORWARD : BACKWARD;
  int dirY = (stepsY >= 0) ? FORWARD : BACKWARD;

  // Backlash compensation: take up mechanical slack silently
  // before any real drawing step, whenever direction reverses.
  if (stepsX != 0 && lastDirX != 0 && dirX != lastDirX) {
    for (int i = 0; i < BACKLASH_X; i++) stepperX.onestep(dirX, STEP_STYLE);
  }
  if (stepsY != 0 && lastDirY != 0 && dirY != lastDirY) {
    for (int i = 0; i < BACKLASH_Y; i++) stepperY.onestep(dirY, STEP_STYLE);
  }
  if (stepsX != 0) lastDirX = dirX;
  if (stepsY != 0) lastDirY = dirY;

  long absX = abs(stepsX);
  long absY = abs(stepsY);
  long maxSteps = max(absX, absY);
  if (maxSteps == 0) return;

  long errX = 0, errY = 0;

  for (long i = 0; i < maxSteps; i++) {
    errX += absX;
    errY += absY;

    if (errX >= maxSteps) {
      stepperX.onestep(dirX, STEP_STYLE);
      errX -= maxSteps;
    }
    if (errY >= maxSteps) {
      stepperY.onestep(dirY, STEP_STYLE);
      errY -= maxSteps;
    }
    delayMicroseconds(stepDelayMicros);
  }

  curX += (float)stepsX / X_STEPS;
  curY += (float)stepsY / Y_STEPS;
}
