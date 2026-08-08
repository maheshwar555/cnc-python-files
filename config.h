#ifndef CONFIG_H
#define CONFIG_H
// =====================================
// DIYPlotterOS v0.1 Configuration
// =====================================
// Motor calibration (steps per mm, measured by test move)
#define X_STEPS 9.7
#define Y_STEPS 7.1
// Servo angles
#define PEN_UP 130
#define PEN_DOWN 100
// Motor speed (RPM)
#define MOTOR_SPEED 30
// Soft travel limits (mm, relative to centered origin)
// Measured rail travel: X=36mm, Y=40mm -- kept inside a safety margin
#define X_MIN -16
#define X_MAX 16
#define Y_MIN -18
#define Y_MAX 18
// Servo pin
#define SERVO_PIN 10
// Step style
#define STEP_STYLE DOUBLE
// Backlash compensation (extra steps taken up silently on direction change)
#define BACKLASH_X 4
#define BACKLASH_Y 4
#endif
