#include "TFT_eSPI.h" //include TFT LCD library

#include <SPI.h>

TFT_eSPI tft; // initialize TFT LCD

#include <Seeed_FS.h>


const int EMG = A4;
const int GSR = A0;
int sensorValue = 0;
int gsr_average = 0;
int emg_value = 0;
unsigned long previousMillis, currentMillis = 0;
const int max_heartpluse_duty = 2000;
unsigned long valueHeartRate;
float heartRate;
float ohm;
float conductance;
int menuPosition = 1;

bool gsrOn, hrvOn, emgOn = false;

void setup() {

  //set joystick
  pinMode(WIO_5S_UP, INPUT_PULLUP);
  pinMode(WIO_5S_DOWN, INPUT_PULLUP);
  pinMode(WIO_5S_LEFT, INPUT_PULLUP);
  pinMode(WIO_5S_RIGHT, INPUT_PULLUP);
  pinMode(WIO_5S_PRESS, INPUT_PULLUP);

  Serial.begin(115200); // start serial connection
  tft.begin(); // start TFT LCD
  tft.setRotation(3); // set screen rotation
  tft.fillScreen(TFT_BLACK); // fill background
  tft.setTextColor(TFT_WHITE); // set text color
  tft.setTextSize(3); // set text size

  tft.fillScreen(TFT_BLACK); // fill background
  tft.drawString("GSR:", 30, 50);
  tft.drawString("EMG:", 30, 100);
  tft.drawString("HRV:", 30, 150);

  attachInterrupt(digitalPinToInterrupt(2), interrupt, RISING); // start interrupt for HR

  drawSettings(); // draw settings buttons on screen

}

void loop() {

  menu(); // get joystick movement
  currentMillis = millis();
  if (currentMillis - previousMillis > 1000) {
    
    if (gsrOn == true) {
      get_GSR_data();
    }

    if (emgOn == true) {
      get_EMG_data();
    }

    previousMillis = currentMillis;

    //write sensors data on screen
    tft.setTextSize(3); 
    tft.fillRect(100, 2, 100, 200, TFT_BLACK);
    tft.setCursor(100, 50);
    tft.print(conductance);
    tft.setCursor(100, 100);
    tft.print(emg_value);
    tft.setCursor(100, 150);
    tft.print(valueHeartRate);

    menu(); // get joystick movement

  } //END IF

} //END LOOP

/*GSR sensor reading function*/
void get_GSR_data() {

  long sum = 0;

  for (int i = 0; i < 200; i++) //Average the 200 measurements to remove the glitch
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


/*EMG sensor reading function*/
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
  delay(50);
}


/*HR sensor reading function*/
void interrupt() {
  if (hrvOn == true) {

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

}


/*draw screen function*/
void drawSettings() {

  if (gsrOn == true) {
    tft.setTextSize(1);

    tft.drawCircle(220, 60, 15, TFT_GREEN); //A black circle origin at (160, 120) 
    tft.fillCircle(220, 60, 15, TFT_GREEN);
    tft.drawString("ON ", 215, 53);

  } else if (gsrOn == false) {
    tft.setTextSize(1);
    tft.fillCircle(220, 60, 15, TFT_RED);
    tft.drawCircle(220, 60, 15, TFT_RED); //A black circle origin at (160, 120) 
    tft.drawString("OFF", 215, 53);

  }

  if (emgOn == true) {
    tft.setTextSize(1);

    tft.drawCircle(220, 110, 15, TFT_GREEN); //A black circle origin at (160, 120) 
    tft.fillCircle(220, 110, 15, TFT_GREEN);
    tft.drawString("ON ", 215, 107);

  } else if (emgOn == false) {
    tft.setTextSize(1);
    tft.fillCircle(220, 110, 15, TFT_RED);
    tft.drawCircle(220, 110, 15, TFT_RED); //A black circle origin at (160, 120) 
    tft.drawString("OFF", 215, 107);

  }

  if (hrvOn == true) {
    tft.setTextSize(1);

    tft.drawCircle(220, 160, 15, TFT_GREEN); //A black circle origin at (160, 120) 
    tft.fillCircle(220, 160, 15, TFT_GREEN);
    tft.drawString("ON ", 215, 157);

  } else if (hrvOn == false) {
    tft.setTextSize(1);
    tft.fillCircle(220, 160, 15, TFT_RED);
    tft.drawCircle(220, 160, 15, TFT_RED); //A black circle origin at (160, 120) 
    tft.drawString("OFF", 215, 157);

  }

  tft.fillRect(1, 1, 29, 250, TFT_BLACK);

  if (menuPosition == 1) {
    tft.setTextSize(3);
    tft.drawString(">", 5, 50);

  }

  if (menuPosition == 2) {
    tft.setTextSize(3);
    tft.drawString(">", 5, 100);

  }

  if (menuPosition == 3) {
    tft.setTextSize(3);
    tft.drawString(">", 5, 150);

  }

} // END DRAWSETTING


/*Get Joystick movement function*/
void menu() {

  if (digitalRead(WIO_5S_DOWN) == LOW) {
    menuPosition++;
    if (menuPosition == 4) {
      menuPosition = 1;
    }
    drawSettings();
    delay(500);
  }

  if (digitalRead(WIO_5S_UP) == LOW) {
    menuPosition--;
    if (menuPosition == 0) {
      menuPosition = 3;
    }
    drawSettings();
    delay(500);
  }

  if (digitalRead(WIO_5S_PRESS) == LOW) {
    if (menuPosition == 1) {
      gsrOn = !gsrOn;
    }
    if (menuPosition == 2) {
      emgOn = !emgOn;
    }
    if (menuPosition == 3) {
      hrvOn = !hrvOn;
    }
    drawSettings();
    delay(500);
  }

} //END MENU
