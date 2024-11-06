
//***********************************************************************************
// Audio Frequency Processed software to remote JUMA TX136/500 v1.00 - F4GCB 2021-12
// Audio Wave Length Measurement related functions by Kazuhisa "Kazu" Terasaki AG6NS 
//***********************************************************************************

#include <EEPROM.h>
#include "Wire.h"

#define CPU_CLOCK_FREQ     16000000    // 16MHz
#define ON_LED             9
#define TX_LED             8

void setup() {
  Serial.begin(115200);
  
  pinMode(ON_LED, OUTPUT);
  pinMode(TX_LED, OUTPUT);
  digitalWrite(ON_LED, LOW);       // disable ON Led 
  digitalWrite(TX_LED, LOW);       // disable TX Led

  // initialize analog comparator
  ADCSRA = 0x00;          // ADEN=0
  ADCSRB = (1 << ACME);   // enable Analog Comparator Multiplexer
  ADMUX = 0x00;           // MUX=0b0000 (ADC0)
  ACSR = (1 << ACBG) | (1 << ACI) | (1 << ACIS1) | (0 << ACIS0);   // enable Bandgap Voltage Reference, clear Analog Comparator Interrupt flag, ACIS=0b10 (Comparator Interrupt on Falling Output Edge)

  // initialize TIMER1
  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCCR1C = 0;
  TCCR1B = (1 << ICNC1) | (0 << ICES1) | (1 << CS10);// enable Input Capture Noise Canceler, Input Capture Edge Select (Falling), CS=0b001 (16MHz / 1)
  ICR1 = 0;
  ACSR |= (1 << ACIC);      // enable Analog Comparator Input Capture
  TIFR1 = 0x027;            // clear interrupt flags
  TIMSK1 |= (1 << ICIE1) | (1 << TOIE1);   // enable Input Capture Interrupt, enable Timer1 Overflow Interrupt
  interrupts();

  delay(1000); // let things settle down a bit
  digitalWrite(ON_LED, HIGH);       // enable ON Led, AFP interface is ready
  
}
    
void loop() {
  static uint16_t sPrevTimer1 = 0;
  bool processUI = false;
  if ((TCNT1 - sPrevTimer1) >= (CPU_CLOCK_FREQ / 1000)) {
      sPrevTimer1 = TCNT1;
    processUI = true;
   }
   else {
    goto SKIP_UI;
   }

  SKIP_UI:
    processAudioInput(processUI);
}

//*****************************************************
//    Audio Wave Length Measurement related functions
//    Developed by Kazuhisa "Kazu" Terasaki AG6NS
//    Add some optimizations for slow modes - F4GCB
//*****************************************************

#define MIN_INPUT_AUDIO_FREQ            190                        // minimum input audio frequency limit is 200Hz  - 5%
#define MAX_INPUT_AUDIO_FREQ            4200                       // maximum input audio frequency limit is 4000Hz + 5%
//#define UPDATE_VFO_PERIOD               (CPU_CLOCK_FREQ / 250)   // update FSK frequency 250 times/sec (every 4 ms)
#define UPDATE_VFO_PERIOD_FAST           (CPU_CLOCK_FREQ / 50)     // update JUMA TX frequency 50 times/sec (every 20 ms)
#define UPDATE_VFO_PERIOD_SLOW           (CPU_CLOCK_FREQ / 10)     // update JUMA TX frequency 10 times/sec (every 100 ms)
//#define NO_SIGNAL_PERIOD_THRESHOLD      (CPU_CLOCK_FREQ / 20)    // no signal detection threshold (50ms)
#define NO_SIGNAL_PERIOD_THRESHOLD      (CPU_CLOCK_FREQ / 5)       // no signal detection threshold (200ms)
//#define MIN_SAMPLE_COUNT_FOR_AVERAGING  2                        // minimum sample counts for averaging filter
#define MIN_SAMPLE_COUNT_FOR_AVERAGING_FAST  4                     // minimum sample counts for averaging filter
#define MIN_SAMPLE_COUNT_FOR_AVERAGING_SLOW  20                    // minimum sample counts for averaging filter
#define PLL_CALCULATION_PRECISION       4

volatile uint8_t  gMeasuredFullWaveCount = 0;
volatile uint16_t gTimer1OverflowCounter = 0;
volatile uint32_t gCurrentTimer1InputCaptureValue = 0;
volatile uint32_t gUpperHalfLenSum = 0;
volatile uint32_t gLowerHalfLenSum = 0;

inline void resetMeasuredValues(void) {
  noInterrupts();

  // reset values
  gMeasuredFullWaveCount = 0;
  gUpperHalfLenSum       = 0;
  gLowerHalfLenSum       = 0;

  interrupts();
}

inline void readAndResetMeasuredValues(uint32_t *currentInputCaptureValue, uint8_t *fullWaveCount, uint32_t *upperHalfWaveLenSum, uint32_t *lowerHalfWaveLenSum) {
  noInterrupts();

  *currentInputCaptureValue = gCurrentTimer1InputCaptureValue;

  *fullWaveCount         = gMeasuredFullWaveCount;
  *upperHalfWaveLenSum   = gUpperHalfLenSum;
  *lowerHalfWaveLenSum   = gLowerHalfLenSum;

  // reset values
  gMeasuredFullWaveCount = 0;
  gUpperHalfLenSum       = 0;
  gLowerHalfLenSum       = 0;

  interrupts();
}

inline uint32_t readCurrentTimer1Value(void) {
  noInterrupts();
  uint16_t counterValue = TCNT1;
  uint32_t currentTimer1Value = ((uint32_t)gTimer1OverflowCounter << 16) | counterValue;
  if ((TIFR1 & (1 << TOV1)) && (counterValue & 0x8000) == 0x0000) {
    // timer1 overflow happened and hasn't handled it yet
    currentTimer1Value += 0x10000;
  }
  interrupts();
  return currentTimer1Value;
}

void processAudioInput(bool checkNoSignal) {
  static bool sIsTransmitting = false;

  // read the length of the last measured audio wave
  uint32_t currentInputCaptureValue;
  uint8_t  inputCaptureEvents;
  uint32_t upperWaveLenSum;
  uint32_t lowerWaveLenSum;
  readAndResetMeasuredValues(&currentInputCaptureValue, &inputCaptureEvents, &upperWaveLenSum, &lowerWaveLenSum);

  static uint32_t sLastVFOUpdatedInputCaptureValue  = 0;
  static uint16_t sCapturedWaveCount                = 0;
  static uint32_t sUpperWaveLenTotal                = 0;
  static uint32_t sLowerWaveLenTotal                = 0;
  static uint32_t sLastValidSignalInputCaptureValue = 0;
  static uint32_t previousAudioFreq = 0;    // send audio fequency only if it changed
  static uint32_t frequencyTestTime;        // frequency change test time in ms
  static uint8_t setVfoPeriod = 0;          // set VFO period 0 & 1 = FAST, 2 = SLOW
  static uint32_t vfoPeriod;                // VFO period update
  static uint16_t sampleCount;              // minimum sample counts for averaging filter

  if (inputCaptureEvents > 0) {
    sCapturedWaveCount += inputCaptureEvents;
    sUpperWaveLenTotal += upperWaveLenSum;
    sLowerWaveLenTotal += lowerWaveLenSum;

    if (sLastVFOUpdatedInputCaptureValue == 0) {
      sLastVFOUpdatedInputCaptureValue = currentInputCaptureValue;
    }

    uint32_t totalWaveLength = currentInputCaptureValue - sLastVFOUpdatedInputCaptureValue;
    
    if (setVfoPeriod == 2) {
      vfoPeriod = UPDATE_VFO_PERIOD_SLOW;
      sampleCount = MIN_SAMPLE_COUNT_FOR_AVERAGING_SLOW;
    }
    else {
      vfoPeriod = UPDATE_VFO_PERIOD_FAST;
      sampleCount = MIN_SAMPLE_COUNT_FOR_AVERAGING_FAST;
    }
     
    if (totalWaveLength >= vfoPeriod && sCapturedWaveCount >= sampleCount) {
   
      // measured audio wave length
      uint32_t averageWaveLength = ((sUpperWaveLenTotal << PLL_CALCULATION_PRECISION) + (sCapturedWaveCount / 2)) / sCapturedWaveCount +
                                   ((sLowerWaveLenTotal << PLL_CALCULATION_PRECISION) + (sCapturedWaveCount / 2)) / sCapturedWaveCount;

      // measured audio frequency 
      uint32_t audioFreq = (CPU_CLOCK_FREQ << (PLL_CALCULATION_PRECISION * 2)) / averageWaveLength;   // frequency is in 28.4 fixed point number, 0.0625Hz resolution

      if (((uint32_t)MIN_INPUT_AUDIO_FREQ << PLL_CALCULATION_PRECISION) <= audioFreq && audioFreq <= ((uint32_t)MAX_INPUT_AUDIO_FREQ << PLL_CALCULATION_PRECISION) &&
        sLowerWaveLenTotal < sUpperWaveLenTotal && sUpperWaveLenTotal < (sLowerWaveLenTotal << 1))  // sLowerWaveLenTotal < sUpperWaveLenTotal < sLowerWaveLenTotal * 2
  
      {
        // found audio signal
        sLastValidSignalInputCaptureValue = currentInputCaptureValue;
                
        if (sIsTransmitting) {
          digitalWrite(TX_LED, HIGH);      // enable TX Led

          // if no frequency change (+- 0,1875 Hz) during 1500 ms then slow mode used (FST4-300 and more)
          if (!setVfoPeriod && frequencyTestTime > millis()) {
            if (previousAudioFreq && (audioFreq < previousAudioFreq - 3 || audioFreq > previousAudioFreq + 3))
              setVfoPeriod = 1;      // confirm FAST vfo update
          }
          else if (setVfoPeriod == 0)
            setVfoPeriod = 2;        // turn to SLOW vfo update

          // send audio frequency only if change
          if (audioFreq != previousAudioFreq) {
            previousAudioFreq = audioFreq;
            audioFreq = ((float)audioFreq / 16) * 1000;   // audio frequency in mHz
            Serial.print("T");                            // send TX on command
            Serial.println(audioFreq);                    // send audio frequency
          }
        }
        else frequencyTestTime = millis() + 1500;  // set the frequency change test time to 1500 ms
        
        sIsTransmitting = true;     // set this flag at here so we can ignore the first detected frequency which might include some error
      }

      sLastVFOUpdatedInputCaptureValue = currentInputCaptureValue;
      sCapturedWaveCount = 0;
      sUpperWaveLenTotal = 0;
      sLowerWaveLenTotal = 0;
    }
  }

  if (checkNoSignal && sIsTransmitting) {
    uint32_t currentTimer1Value = readCurrentTimer1Value();
    uint32_t noSignalPeriod = currentTimer1Value - sLastValidSignalInputCaptureValue;
    if (noSignalPeriod > NO_SIGNAL_PERIOD_THRESHOLD) {
      // detected no signal period
      sLastVFOUpdatedInputCaptureValue = 0;
      sCapturedWaveCount = 0;
      sUpperWaveLenTotal = 0;
      sLowerWaveLenTotal = 0;

      resetMeasuredValues();

      digitalWrite(TX_LED, LOW);         // disable TX Led
      Serial.println("R");               // TX off command
      
      sIsTransmitting = false;
      previousAudioFreq = 0;
      setVfoPeriod = 0;
    }
  }
}   

inline uint32_t readTimer1InputCaptureValue(void)
{
  uint16_t counterValue = ICR1;
  uint32_t currentTimer1Value = ((uint32_t)gTimer1OverflowCounter << 16) | counterValue;
  if ((TIFR1 & (1 << TOV1)) && (counterValue & 0x8000) == 0x0000) {
    // timer1 overflow happened and hasn't handled it yet
    currentTimer1Value += 0x10000;
  }
  return currentTimer1Value;
}

// ISR priority 11
ISR(TIMER1_CAPT_vect) {
  static uint32_t sPrevInputCaptureValue;
  static uint32_t sUpperWaveLen;

  uint32_t currentInputCaptureValue = readTimer1InputCaptureValue();
  uint32_t halfWaveLen = currentInputCaptureValue - sPrevInputCaptureValue;

  uint8_t currTCCR1B = TCCR1B;
  if (currTCCR1B & (1 << ICES1)) {
    // detected Falling Audio Signal Edge (Rising Input Capture Edge)
    static uint32_t sAveUpperHalfWaveLen = 0;
    sAveUpperHalfWaveLen = (sAveUpperHalfWaveLen + sAveUpperHalfWaveLen + sAveUpperHalfWaveLen + halfWaveLen) >> 2;  // (sAveUpperHalfWaveLen * 3 + halfWaveLen) / 4;
    if (halfWaveLen < ((sAveUpperHalfWaveLen >> 2) + (sAveUpperHalfWaveLen >> 4))) {    // (sAveUpperHalfWaveLen * 0.3125)
      // ignore ripple
      return;
    }

    sUpperWaveLen = halfWaveLen;
  }
  else {
    // detected Rising Audio Signal Edge (Falling Input Capture Edge)
    static uint32_t sAveLowerHalfWaveLen = 0;
    sAveLowerHalfWaveLen = (sAveLowerHalfWaveLen + sAveLowerHalfWaveLen + sAveLowerHalfWaveLen + halfWaveLen) >> 2;  // (sAveLowerHalfWaveLen * 3 + halfWaveLen) / 4;
    if (halfWaveLen < ((sAveLowerHalfWaveLen >> 2) + (sAveLowerHalfWaveLen >> 4))) {    // (sAveLowerHalfWaveLen * 0.3125)
      // ignore ripple
      return;
    }

    gUpperHalfLenSum += sUpperWaveLen;
    gLowerHalfLenSum += halfWaveLen;
    gCurrentTimer1InputCaptureValue = currentInputCaptureValue;
    gMeasuredFullWaveCount++;
  }
  sPrevInputCaptureValue = currentInputCaptureValue;

  TCCR1B = currTCCR1B ^ (1 << ICES1);     // flip edge selection
  TIFR1 = (1 << ICF1);                    // clear Input Capture interrupt Flag (flipping the edge selection causes the unwanted interrupt)
}

// ISR priority 14
ISR(TIMER1_OVF_vect) {
  gTimer1OverflowCounter++;
}

//*****************************************************
