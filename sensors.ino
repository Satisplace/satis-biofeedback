#include "TFT_eSPI.h" //include TFT LCD library

#include <SPI.h>

TFT_eSPI tft; // initialize TFT LCD
#include <Wire.h>

#include <Seeed_FS.h>


#define EMG A4
const int GSR = A0;
int sensorValue = 0;
int gsr_average = 0;
long timeNow;
long timeBefore = 0;
int countSample = 0;
int emg_value = 0;
unsigned long millisecToWait;
unsigned long previousMillis, currentMillis = 0;
const int max_heartpluse_duty = 2000;
unsigned long valueHeartRate;
float heartRate;
float ohm;
float conductance;

void setup() {
  Serial.begin(115200);
  tft.begin(); // start TFT LCD
  tft.setRotation(3); // set screen rotation
  tft.fillScreen(TFT_BLACK); // fill background
  tft.setTextColor(TFT_WHITE); // set text color
  tft.setTextSize(5); // set text size

  attachInterrupt(digitalPinToInterrupt(2), interrupt, RISING); // start interrupt for HR

}

void loop() {

  currentMillis = millis();
  if (currentMillis - previousMillis > 1000) {
    get_GSR_data();
    get_EMG_data();
    previousMillis = currentMillis;

    tft.setCursor(5, 2);
    tft.fillScreen(TFT_BLACK); // fill background
    tft.print(conductance);
    tft.setCursor(5, 50);
    tft.print(emg_value);
    tft.setCursor(5, 100);
    tft.print(valueHeartRate);

  }

}

void get_GSR_data() {

  long sum = 0;

  for (int i = 0; i < 200; i++) //Average the 10 measurements to remove the glitch
  {
    sensorValue = analogRead(GSR);
    sum += sensorValue;

  }
  gsr_average = sum / 200;
  ohm = ((1024.0 + (2.0 * gsr_average)) * 10000.0) / (512.0 - gsr_average);
  conductance = 1000000 / ohm;
  Serial.print("G-");
  Serial.println(conductance);

}

void get_EMG_data() {
  long sum = 0;
  // Evaluate the summation of the last 32 EMG sensor measurements.
  for (int i = 0; i < 32; i++) {
    sum += analogRead(EMG);
  }
  // Shift the summation by five with the right shift operator (>>) to obtain the EMG value.  
  emg_value = sum / 32;
  Serial.print("E-");
  Serial.println(emg_value);
  delay(10);
}

void interrupt() {
  static unsigned long previousInterruptMillis = 0;
  unsigned long currentInterruptMillis = millis();
  if (currentInterruptMillis - previousInterruptMillis >= max_heartpluse_duty) {

    previousInterruptMillis = currentInterruptMillis;
  } else {

    valueHeartRate = currentInterruptMillis - previousInterruptMillis;
    previousInterruptMillis = currentInterruptMillis;

    Serial.print("H-");
    Serial.println(valueHeartRate);

  }

}
