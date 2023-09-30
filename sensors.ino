
#include "TFT_eSPI.h" //include TFT LCD library
#include <SPI.h>
TFT_eSPI tft; // initialize TFT LCD
#include <Wire.h>
#include <Seeed_FS.h>

#define EMG A2

const int GSR=A0;
int sensorValue=0;
int gsr_average=0;
long timeNow;
long timeBefore = 0;
int printMillis,printSample,countSample=0;
int emg_value=0;
unsigned long hz=1;
unsigned long millisecToWait;
unsigned long previousMillis, currentMillis = 0;
bool reStart = true; 
float ohm;
float conductance;

const int max_heartpluse_duty = 2000;
unsigned long valueHeartRate;
float heartRate;

void setup(){
  Serial.begin(115200);
  tft.begin(); // start TFT LCD
  tft.setRotation(3); // set screen rotation
  tft.fillScreen(TFT_BLACK); // fill background
  tft.setTextColor(TFT_WHITE); // set text color
  tft.setTextSize(5); // set text size
  //Wire.begin();

  attachInterrupt(digitalPinToInterrupt(2), interrupt, RISING); // start interrupt for HR
  
}




void loop(){
  
  
  
while (currentMillis - previousMillis < 1000) //
  {  
  if (reStart == true)
  {
  for(int a=0;a<hz;a++)           //Average the 10 measurements to remove the glitch
    {
    countSample++;  
    
    //sensorValue=analogRead(GSR);
    
    
    long sum = 0;
    for (int i = 0; i < 200; i++) // Average the 300 measurements to remove the glitch
    {
      sensorValue = analogRead(GSR);
      sum += sensorValue;

    }
    gsr_average = sum / 200;
    ohm = ((1024.0 + (2.0 * gsr_average)) * 10000.0) / (512.0 - gsr_average);
    conductance = 1000000 / ohm;
    
    
    ohm = ((1024.0 + (2.0 * sensorValue)) * 10000.0) / (512.0 - sensorValue);
    conductance = 1000000 / ohm;
       
   
    Serial.print("G-");Serial.println(conductance);
    }
    reStart= false;
  }  
    currentMillis = millis(); 
printSample=countSample;    
countSample=0;

   }
printMillis = currentMillis - previousMillis;
previousMillis = currentMillis; 
reStart = true;  
  
  
  tft.setCursor(5, 2);
  tft.fillScreen(TFT_BLACK); // fill background
  tft.print(printSample);
  tft.setCursor(150, 2);tft.print(printMillis);

  tft.setCursor(5, 100);
  tft.print(valueHeartRate);
   

}





  void interrupt() {
  static unsigned long previousInterruptMillis = 0;
  unsigned long currentInterruptMillis = millis();
  if (currentInterruptMillis - previousInterruptMillis >= max_heartpluse_duty) {

    previousInterruptMillis = currentInterruptMillis;
  } else {
   
    valueHeartRate = currentInterruptMillis - previousInterruptMillis;
    previousInterruptMillis = currentInterruptMillis;
   

           
      Serial.print("H-");Serial.println(valueHeartRate);

    }

   

    }

  
