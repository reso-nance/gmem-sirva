// Arduino Beat Detector By Damian Peckett 2015
// License: Public Domain.
//https://create.arduino.cc/projecthub/Joao_Claro/arduino-beat-detector-d0a21f

// Our Global Sample Rate, 5000hz
#define SAMPLEPERIODUS 200
#define AUDIO_INPUT 0
#define THREESHOLD_POT 1
#define DURATION_POT 2
#define SOLENOID_PIN 3
#define SOLENOID_MAX_DURATION 500

// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

const int minDelay = 1000;
const int maxDelay = 1000;
unsigned long solenoidOFFtimer = 0;
bool solenoidON = false;

void setup() {
    // Set ADC to 77khz, max for 10bit
    sbi(ADCSRA,ADPS2);
    cbi(ADCSRA,ADPS1);
    cbi(ADCSRA,ADPS0);

    //The pin with the LED
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(SOLENOID_PIN, OUTPUT);
    digitalWrite(SOLENOID_PIN, LOW);
    digitalWrite(LED_BUILTIN, LOW);
    Serial.begin(115200);
}

// 20 - 200hz Single Pole Bandpass IIR Filter
float bassFilter(float sample) {
    static float xv[3] = {0,0,0}, yv[3] = {0,0,0};
    xv[0] = xv[1]; xv[1] = xv[2]; 
    xv[2] = (sample) / 4.f; // change here to values close to 2, to adapt for stronger or weeker sources of line level audio  
    

    yv[0] = yv[1]; yv[1] = yv[2]; 
    yv[2] = (xv[2] - xv[0])
        + (-0.7960060012f * yv[0]) + (1.7903124146f * yv[1]);
    return yv[2];
}

// 10hz Single Pole Lowpass IIR Filter
float envelopeFilter(float sample) { //10hz low pass
    static float xv[2] = {0,0}, yv[2] = {0,0};
    xv[0] = xv[1]; 
    xv[1] = sample / 50.f;
    yv[0] = yv[1]; 
    yv[1] = (xv[0] + xv[1]) + (0.9875119299f * yv[0]);
    return yv[1];
}

// 1.7 - 3.0hz Single Pole Bandpass IIR Filter
float beatFilter(float sample) {
    static float xv[3] = {0,0,0}, yv[3] = {0,0,0};
    xv[0] = xv[1]; xv[1] = xv[2]; 
    xv[2] = sample / 2.7f;
    yv[0] = yv[1]; yv[1] = yv[2]; 
    yv[2] = (xv[2] - xv[0])
        + (-0.7169861741f * yv[0]) + (1.4453653501f * yv[1]);
    return yv[2];
}



void loop() {
    unsigned long time = micros(); // Used to track rate
    float sample, value, envelope, beat, thresh;
    unsigned char i;
    
    if (solenoidON && millis() >= solenoidOFFtimer) 
    {
      digitalWrite(SOLENOID_PIN, LOW);
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("coucou");
      solenoidON = false;
    }

    for(i = 0;;++i){
        // Read ADC and center so +-512
        value = analogRead(AUDIO_INPUT);
        sample = (float)value-503.f;

        // Filter only bass component
        value = bassFilter(sample);

        // Take signal amplitude and filter
        if(value < 0)value=-value;
        envelope = envelopeFilter(value);
        //Serial.print("average : ");Serial.println(average);

        // Every 200 samples (25hz) filter the envelope 
        if(i == 200) {
                // Filter out repeating bass sounds 100 - 180bpm
                beat = beatFilter(envelope);

                // Threshold it based on potentiometer on AN1
                thresh = 0.02f * (float)(analogRead(THREESHOLD_POT)+400);
                unsigned long currentTime = millis();
                if(beat > thresh) {
                  //digitalWrite(LED_BUILTIN, HIGH);
                  Serial.print("detect : "); Serial.print(beat);Serial.print(", thresh : "); Serial.print(thresh); Serial.print(", diff : ");Serial.print(beat-thresh);
                  Serial.print(", pot : "); Serial.println((float)analogRead(DURATION_POT));
                  unsigned int duration = abs(beat-thresh * ((float)analogRead(DURATION_POT)/100));
                  pulseSolenoid(duration);
                }

                //Reset sample counter
                i = 0;
        }

        // Consume excess clock cycles, to keep at 5000 hz
        for(unsigned long up = time+SAMPLEPERIODUS; time > 20 && time < up; time = micros());
    }  
}

void pulseSolenoid(int duration){
  solenoidOFFtimer = millis() + duration;
  digitalWrite(SOLENOID_PIN, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
  solenoidON = true;
  Serial.print("activating solenoid for "); Serial.print(duration); Serial.println(" ms");
}
