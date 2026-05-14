#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Configuración de la pantalla, para los metodos prueba
#define SCREEN_WIDTH 128 
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1 // Reset compartido con el Arduino
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
const int pinBuzzer = 8; 

void downDisplay() {
  // 1. .begin() - Inicializar pantalla
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("SSD1306 no encontrado"));
    for(;;);
  }

  // 2. .clearDisplay() - Limpiar el buffer inicial
  display.clearDisplay();
  display.display();
}

void downBuzzer() {
  pinMode(pinBuzzer, OUTPUT);
  noTone(pinBuzzer);     
}

void setup() {
  Serial.begin(9600);
  downDisplay();
  downBuzzer();
}

void loop() {
}
