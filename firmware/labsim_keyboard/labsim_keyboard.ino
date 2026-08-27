 /*
 * Blue Pill (STM32F103C8T6) - Teclado USB HID
 *   - 12 botones via PCF8575 (I2C)
 *   -  2 encoders rotativos sin pulsador (interrupciones)
 *   -  2 botones fisicos de estimulo (mismo cableado que el TTP223 que reemplazan)
 *
 * Core:  STM32 MCU based boards (STMicroelectronics)
 * Board: Generic STM32F1 series -> BluePill F103C8
 * USB support .......... Human Interface Device (HID)
 * Upload method ........ STM32CubeProgrammer (Serial)   [PA9/PA10, BOOT0=1]
 *
 * ---------------------------------------------------------------
 *  CONEXIONES
 *  PCF8575 : SDA=PB7  SCL=PB6  VDD=3V3  A0/A1/A2=GND (dir 0x20)
 *            botones de P00..P07 y P10..P13 a GND
 *  Enc 1   : A=PA0  B=PA1  C=GND
 *  Enc 2   : A=PA2  B=PA3  C=GND
 *  Botones : OUT1=PB10  OUT2=PB11   VCC=3V3  (mismos cables que el TTP223)
 *  LED     : PC13 (integrado, logica invertida)
 * ---------------------------------------------------------------
 */

#include <Wire.h>
#include <Keyboard.h>
#include <EEPROM.h>

// ===============================================================
//  1) TECLAS  <-- CAMBIA AQUI Y SOLO AQUI
// ===============================================================
//  Puedes poner un caracter ('a', '7', '+') o una constante
//  especial del HID: KEY_UP_ARROW, KEY_DOWN_ARROW, KEY_LEFT_ARROW,
//  KEY_RIGHT_ARROW, KEY_RETURN, KEY_TAB, KEY_ESC, KEY_BACKSPACE,
//  KEY_F1 ... KEY_F12, KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_HOME, KEY_END.
//  Usa 0 para dejar una entrada sin asignar (no envia nada).

// --- 12 botones del PCF8575, en orden P00..P07, P10..P13 ---
const uint8_t TECLAS_BOTONES[12] = {
  '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'd', '0'
};

// --- Encoders: [0] = giro horario (CW), [1] = antihorario (CCW) ---
const uint8_t TECLAS_ENC1[2] = { 's', 'w' };   // <-- PENDIENTE
const uint8_t TECLAS_ENC2[2] = { 'i', 'k' };   // <-- PENDIENTE

// --- Tactiles TTP223 ---
const uint8_t TECLAS_TOUCH[2] = { 'v', 'b' };  // <-- PENDIENTE

// ===============================================================
//  2) COMPORTAMIENTO DE LOS TACTILES
// ===============================================================
//  MODO_UNICO    : una sola tecla por toque, aunque mantengas el dedo.
//  MODO_REPETIR  : repite la tecla mientras mantengas el dedo.
//                  La cadencia la fijas tu aqui abajo. Funciona igual
//                  en cualquier programa.
//  MODO_MANTENER : deja la tecla fisicamente pulsada hasta que sueltas.
//                  La repeticion (si la hay) la decide el sistema
//                  operativo. Es lo correcto para teclas de "sostener".
#define MODO_UNICO     0
#define MODO_REPETIR   1
#define MODO_MANTENER  2

const uint8_t MODO_TOUCH[2] = { MODO_MANTENER, MODO_MANTENER };

#define TOUCH_RETARDO_MS    400   // espera antes de empezar a repetir
#define TOUCH_INTERVALO_MS   60   // tiempo entre repeticiones (~16/s)

// Lo mismo para los 12 botones del PCF8575 (dejalo en MODO_UNICO si
// solo quieres una pulsacion por click).
#define MODO_BOTONES       MODO_UNICO
#define BTN_RETARDO_MS      400
#define BTN_INTERVALO_MS     60

// ===============================================================
//  3) Configuracion de hardware
// ===============================================================
#define PCF_ADDR          0x20   // valor de arranque, se reemplaza por la detectada/guardada
#define PCF_ADDR_MIN      0x20
#define PCF_ADDR_MAX      0x27
#define N_BOTONES         12
#define DEBOUNCE_BTN_MS   25
#define DEBOUNCE_TOUCH_MS 20

// EEPROM emulada (flash): guarda la direccion I2C del PCF8575 una vez
// detectada, asi en el siguiente arranque no hace falta escanear el bus.
#define EEPROM_ADDR_MAGIC  0
#define EEPROM_ADDR_PCF    1
#define EEPROM_MAGIC_VALUE 0xA5

#define ENC1_A  PA0
#define ENC1_B  PA1
#define ENC2_A  PA2
#define ENC2_B  PA3

#define TOUCH1  PB10
#define TOUCH2  PB11

#define LED_PIN PC13

// Transiciones de cuadratura por cada detente (click mecanico).
// EC11 tipico = 4. Si un click te manda 2 teclas, sube a 8.
// Si hacen falta 2 clicks por tecla, baja a 2.
#define PASOS_POR_DETENTE 4

#define DEBUG_SERIAL 1     // 1 = traza por PA9/PA10 a 115200

// ===============================================================
//  4) Estado interno
// ===============================================================
uint16_t btnEstable = 0xFFFF;
uint16_t btnPrevio  = 0xFFFF;
uint32_t btnTCambio[N_BOTONES];
uint32_t btnTPulsado[N_BOTONES];
uint32_t btnTRepeticion[N_BOTONES];

bool     touchEstable[2]     = { false, false };
bool     touchPrevio[2]      = { false, false };
uint32_t touchTCambio[2]     = { 0, 0 };
uint32_t touchTPulsado[2]    = { 0, 0 };
uint32_t touchTRepeticion[2] = { 0, 0 };

// Tabla de decodificacion de cuadratura (estado anterior<<2 | actual)
const int8_t TABLA_ENC[16] = {
   0, -1,  1,  0,
   1,  0,  0, -1,
  -1,  0,  0,  1,
   0,  1, -1,  0
};

volatile uint8_t enc1Estado = 0, enc2Estado = 0;
volatile int8_t  enc1Acum   = 0, enc2Acum   = 0;   // subpasos
volatile int8_t  enc1Pasos  = 0, enc2Pasos  = 0;   // detentes pendientes

// LED no bloqueante
uint32_t ledApagarEn = 0;

uint8_t pcfAddr = PCF_ADDR;   // se resuelve en setup() via pcfInicializarDireccion()

// ===============================================================
//  5) PCF8575
// ===============================================================
bool pcfPing(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

// Unico dispositivo I2C en el bus: la primera direccion que responda es
// el PCF8575 (el rango 0x20-0x27 cubre las 8 combinaciones de A0/A1/A2).
uint8_t pcfBuscarDireccion() {
  for (uint8_t addr = PCF_ADDR_MIN; addr <= PCF_ADDR_MAX; addr++) {
    if (pcfPing(addr)) return addr;
  }
  return 0;   // no encontrado
}

void pcfInicializarDireccion() {
  uint8_t magic = EEPROM.read(EEPROM_ADDR_MAGIC);
  uint8_t guardada = EEPROM.read(EEPROM_ADDR_PCF);

  if (magic == EEPROM_MAGIC_VALUE && pcfPing(guardada)) {
    pcfAddr = guardada;
#if DEBUG_SERIAL
    Serial.print(F("PCF8575: direccion guardada 0x"));
    Serial.println(pcfAddr, HEX);
#endif
    return;
  }

  uint8_t encontrada = pcfBuscarDireccion();
  if (encontrada) {
    pcfAddr = encontrada;
    EEPROM.write(EEPROM_ADDR_MAGIC, EEPROM_MAGIC_VALUE);
    EEPROM.write(EEPROM_ADDR_PCF, pcfAddr);
#if DEBUG_SERIAL
    Serial.print(F("PCF8575: detectado y guardado 0x"));
    Serial.println(pcfAddr, HEX);
#endif
  } else {
    pcfAddr = PCF_ADDR;   // fallback: sigue intentando con el default
#if DEBUG_SERIAL
    Serial.println(F("PCF8575: no responde en 0x20-0x27"));
#endif
  }
}

void pcfEscribir(uint16_t valor) {
  Wire.beginTransmission(pcfAddr);
  Wire.write((uint8_t)(valor & 0xFF));
  Wire.write((uint8_t)(valor >> 8));
  Wire.endTransmission();
}

bool pcfLeer(uint16_t &valor) {
  if (Wire.requestFrom((uint8_t)pcfAddr, (uint8_t)2) != 2) return false;
  uint8_t lo = Wire.read();
  uint8_t hi = Wire.read();
  valor = ((uint16_t)hi << 8) | lo;
  return true;
}

// ===============================================================
//  6) ISR de los encoders  (cortas: solo acumulan)
// ===============================================================
void isrEnc1() {
  uint8_t ab = (digitalRead(ENC1_A) << 1) | digitalRead(ENC1_B);
  enc1Estado = ((enc1Estado << 2) | ab) & 0x0F;
  enc1Acum  += TABLA_ENC[enc1Estado];

  if (enc1Acum >= PASOS_POR_DETENTE)       { enc1Pasos++; enc1Acum = 0; }
  else if (enc1Acum <= -PASOS_POR_DETENTE) { enc1Pasos--; enc1Acum = 0; }
}

void isrEnc2() {
  uint8_t ab = (digitalRead(ENC2_A) << 1) | digitalRead(ENC2_B);
  enc2Estado = ((enc2Estado << 2) | ab) & 0x0F;
  enc2Acum  += TABLA_ENC[enc2Estado];

  if (enc2Acum >= PASOS_POR_DETENTE)       { enc2Pasos++; enc2Acum = 0; }
  else if (enc2Acum <= -PASOS_POR_DETENTE) { enc2Pasos--; enc2Acum = 0; }
}

// ===============================================================
//  7) Utilidades
// ===============================================================
void enviarTecla(uint8_t k) {
  if (k == 0) return;
  Keyboard.write(k);
}

void pulsarTecla(uint8_t k) {
  if (k == 0) return;
  Keyboard.press(k);
}

void soltarTecla(uint8_t k) {
  if (k == 0) return;
  Keyboard.release(k);
}

// Parpadeo sin delay(), para no estropear la cadencia de repeticion
void destello(uint32_t ahora) {
  digitalWrite(LED_PIN, LOW);
  ledApagarEn = ahora + 15;
}

void atenderLed(uint32_t ahora) {
  if (ledApagarEn && ahora >= ledApagarEn) {
    digitalWrite(LED_PIN, HIGH);
    ledApagarEn = 0;
  }
}

// ===============================================================
//  8) Setup
// ===============================================================
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

#if DEBUG_SERIAL
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("=== Teclado HID: PCF8575 + 2 encoders + 2 touch ==="));
#endif

  // --- I2C ---
  Wire.setSDA(PB7);
  Wire.setSCL(PB6);
  Wire.begin();
  Wire.setClock(100000);
  pcfInicializarDireccion();
  pcfEscribir(0xFFFF);        // pines como entrada (pull-up interno)

  // --- Encoders ---
  pinMode(ENC1_A, INPUT_PULLUP);
  pinMode(ENC1_B, INPUT_PULLUP);
  pinMode(ENC2_A, INPUT_PULLUP);
  pinMode(ENC2_B, INPUT_PULLUP);

  enc1Estado = (digitalRead(ENC1_A) << 1) | digitalRead(ENC1_B);
  enc2Estado = (digitalRead(ENC2_A) << 1) | digitalRead(ENC2_B);

  attachInterrupt(digitalPinToInterrupt(ENC1_A), isrEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC1_B), isrEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC2_A), isrEnc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC2_B), isrEnc2, CHANGE);

  // --- Tactiles (TTP223 salida activa en alto, push-pull) ---
  pinMode(TOUCH1, INPUT_PULLDOWN);
  pinMode(TOUCH2, INPUT_PULLDOWN);

  Keyboard.begin();

  uint32_t ahora = millis();
  for (uint8_t i = 0; i < N_BOTONES; i++) {
    btnTCambio[i]     = ahora;
    btnTPulsado[i]    = ahora;
    btnTRepeticion[i] = ahora;
  }
  touchTCambio[0] = touchTCambio[1] = ahora;

#if DEBUG_SERIAL
  Serial.println(F("Listo."));
#endif
  delay(300);
}

// ===============================================================
//  9) Loop
// ===============================================================
void loop() {
  uint32_t ahora = millis();
  atenderLed(ahora);

  // ---------- Botones del PCF8575 ----------
  uint16_t lectura;
  if (pcfLeer(lectura)) {
    for (uint8_t i = 0; i < N_BOTONES; i++) {
      bool nivel   = (lectura    >> i) & 1;   // 0 = pulsado
      bool previo  = (btnPrevio  >> i) & 1;
      bool estable = (btnEstable >> i) & 1;

      if (nivel != previo) {
        btnTCambio[i] = ahora;
      }
      else if (nivel != estable && (ahora - btnTCambio[i]) >= DEBOUNCE_BTN_MS) {
        if (nivel) btnEstable |=  (1u << i);
        else       btnEstable &= ~(1u << i);

        if (!nivel) {                          // se acaba de pulsar
          btnTPulsado[i]    = ahora;
          btnTRepeticion[i] = ahora;
#if MODO_BOTONES == MODO_MANTENER
          pulsarTecla(TECLAS_BOTONES[i]);
#else
          enviarTecla(TECLAS_BOTONES[i]);
#endif
          destello(ahora);
#if DEBUG_SERIAL
          Serial.print(F("BTN ")); Serial.println(i);
#endif
        } else {                               // se acaba de soltar
#if MODO_BOTONES == MODO_MANTENER
          soltarTecla(TECLAS_BOTONES[i]);
#endif
        }
      }

#if MODO_BOTONES == MODO_REPETIR
      // Repeticion mientras siga pulsado
      if (!((btnEstable >> i) & 1)) {
        if ((ahora - btnTPulsado[i])    >= BTN_RETARDO_MS &&
            (ahora - btnTRepeticion[i]) >= BTN_INTERVALO_MS) {
          btnTRepeticion[i] = ahora;
          enviarTecla(TECLAS_BOTONES[i]);
        }
      }
#endif
    }
    btnPrevio = lectura;
  }
#if DEBUG_SERIAL
  else {
    static uint32_t tErr = 0;
    if (ahora - tErr > 2000) { tErr = ahora; Serial.println(F("I2C sin respuesta")); }
  }
#endif

  // ---------- Encoders ----------
  noInterrupts();
  int8_t p1 = enc1Pasos; enc1Pasos = 0;
  int8_t p2 = enc2Pasos; enc2Pasos = 0;
  interrupts();

  while (p1 != 0) {
    if (p1 > 0) { enviarTecla(TECLAS_ENC1[0]); p1--; }
    else        { enviarTecla(TECLAS_ENC1[1]); p1++; }
#if DEBUG_SERIAL
    Serial.println(F("ENC1"));
#endif
  }

  while (p2 != 0) {
    if (p2 > 0) { enviarTecla(TECLAS_ENC2[0]); p2--; }
    else        { enviarTecla(TECLAS_ENC2[1]); p2++; }
#if DEBUG_SERIAL
    Serial.println(F("ENC2"));
#endif
  }

  // ---------- Tactiles TTP223 ----------
  const uint8_t pinesTouch[2] = { TOUCH1, TOUCH2 };

  for (uint8_t i = 0; i < 2; i++) {
    bool nivel = digitalRead(pinesTouch[i]);   // HIGH = tocado

    // --- Antirrebote y deteccion de flancos ---
    if (nivel != touchPrevio[i]) {
      touchTCambio[i] = ahora;
      touchPrevio[i]  = nivel;
    }
    else if (nivel != touchEstable[i] && (ahora - touchTCambio[i]) >= DEBOUNCE_TOUCH_MS) {
      touchEstable[i] = nivel;

      if (nivel) {                              // dedo puesto
        touchTPulsado[i]    = ahora;
        touchTRepeticion[i] = ahora;

        if (MODO_TOUCH[i] == MODO_MANTENER) pulsarTecla(TECLAS_TOUCH[i]);
        else                                enviarTecla(TECLAS_TOUCH[i]);

        destello(ahora);
#if DEBUG_SERIAL
        Serial.print(F("TOUCH ")); Serial.print(i + 1); Serial.println(F(" ON"));
#endif
      } else {                                  // dedo retirado
        if (MODO_TOUCH[i] == MODO_MANTENER) soltarTecla(TECLAS_TOUCH[i]);
#if DEBUG_SERIAL
        Serial.print(F("TOUCH ")); Serial.print(i + 1); Serial.println(F(" OFF"));
#endif
      }
    }

    // --- Repeticion automatica mientras se mantiene el dedo ---
    if (touchEstable[i] && MODO_TOUCH[i] == MODO_REPETIR) {
      if ((ahora - touchTPulsado[i])    >= TOUCH_RETARDO_MS &&
          (ahora - touchTRepeticion[i]) >= TOUCH_INTERVALO_MS) {
        touchTRepeticion[i] = ahora;
        enviarTecla(TECLAS_TOUCH[i]);
      }
    }
  }

  delay(2);
}
