import machine
from machine import Pin, ADC
import math as m

Rvd = 100000
K = 273.15
SHA = 0.000730820298298
SHB = 0.00020812771309
SHC = 6.442514744118 * pow(10,-7)
SHD = 9.524809435247 * pow(10,-8)

class Thermistor:
    
    def __init__(self, pin1, pin2):
        self.ntc1 = ADC(pin1)
        self.ntc2 = ADC(pin2)
        self.count = 0
        self.number_of_samples = 50
        self.samples = []        
        for i in range(self.number_of_samples+1):
            self.samples.append(0)
        
        
    def get_temp_deg(self):
        samplessum = 0
        
        Rt1 = Rvd*((65536/self.ntc1.read_u16())-1)
        Rt2 = Rvd*((65536/self.ntc2.read_u16())-1)
        T1 = (1/(SHA + SHB*m.log(Rt1) + SHC*m.pow(m.log(Rt1),2) + SHD*pow(m.log(Rt1), 3))) - K
        T2 = (1/(SHA + SHB*m.log(Rt2) + SHC*m.pow(m.log(Rt2),2) + SHD*pow(m.log(Rt2), 3))) - K
        T = (T1 + T2)/2           
        
        self.samples[self.count] = T
        
        if self.count == self.number_of_samples:
            self.count = 0
        else:
            self.count += 1
                   
        for x in range(self.number_of_samples):
            samplessum = samplessum + self.samples[x]
            
        return samplessum/self.number_of_samples
        
        
