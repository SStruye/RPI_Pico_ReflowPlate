import machine
from PID import PID
from machine import Pin, PWM
import time
from ui import Gui
from thermistor import Thermistor


class Fsm:    
    START_MENU = 0
    SETUP_MENU = 1
    SOAK_TIME = 2
    PREHEAT_TEMP = 3
    REFLOW_TIME = 4
    REFLOW_TEMP = 5  
    PREHEAT = 6
    SOAK = 7
    RAMPUP = 8
    REFLOW = 9
    COOLDOWN = 10
    cooldown_temp = 45
    
    ROT_CW = 1
    ROT_CCW = -1
    SW_PRESS = 2
    RUNNING = 0
    TEMP_CHECK = 3
       
    def __init__(self):
        self.ntc = Thermistor(26, 27)
        self.led = Pin(13, Pin.OUT)
        self.led.low()
        self.gui = Gui(20, 21)
        self.pid = PID(425, 0.001, 9)
        self.pid.sample_time = 100
        self.ssr = PWM(Pin(10))
        self.ssr.freq(500)
        self.ssr.duty_u16(0)
        self.soak_time = 30
        self.preheat_temp = 50
        self.reflow_time = 30
        self.reflow_temp = 80
        self.state = 0
        self.start_time = 0
        self.start_temp = 0
        self.elapsed_time = 0
        self.running = 0
        self.timestamp = 0
        self.timestamp_btn = 0
        self.emergency_cnt = 0
        self.duty_cycle = 0
        self.maxDuty = 30000
        self.minDuty = 0
        
    def update_fsm(self, action):
        if (action == Fsm.ROT_CW) | (action == Fsm.ROT_CCW):
            if (self.state == Fsm.START_MENU) | (self.state == Fsm.SETUP_MENU):             
                self.gui.update_pos(action)
            elif (self.state >= Fsm.SOAK_TIME) & (self.state <= Fsm.REFLOW_TEMP):
                self.update_parameter(action)
        elif action == Fsm.RUNNING:        
            self.running = self.running_update_state()
        elif action == Fsm.SW_PRESS:
            if self.running:
                self.emergency_stop()
            else:
                self.running = self.setup_update_state()
        elif action == Fsm.TEMP_CHECK:
            if self.ntc.get_temp() >= Fsm.cooldown_temp:
                self.state = Fsm.COOLDOWN
                self.start_time = int(time.time())
                self.running = self.running_update_state()
        return self.running
    
    def emergency_stop(self):
        if self.emergency_cnt == 0:
            self.timestamp_btn = self.elapsed_time
            self.emergency_cnt += 1
        elif self.timestamp_btn + 2 >= self.elapsed_time:
            self.emergency_cnt += 1
        else:
            self.emergency_cnt = 0
            self.timestamp_btn = 0
        if self.emergency_cnt == 2:
            self.state = Fsm.START_MENU
            self.ssr.duty_u16(0)
            self.emergency_cnt = 0
            self.timestamp_btn = 0
            self.elapsed_time = 0
            self.running = 0
            self.led.low()
            self.gui.display_frame(self.state)       
                        
    def update_parameter(self, action):
        if self.state == Fsm.SOAK_TIME:
            self.soak_time += action
            self.gui.update_parameters(self.soak_time)
        if self.state == Fsm.PREHEAT_TEMP:
            self.preheat_temp += action
            self.gui.update_parameters(self.preheat_temp)
        if self.state == Fsm.REFLOW_TIME:
            self.reflow_time += action
            self.gui.update_parameters(self.reflow_time)
        if self.state == Fsm.REFLOW_TEMP:
            self.reflow_temp += action
            self.gui.update_parameters(self.reflow_temp)
            
    def setup_update_state(self):
        self.led.low()
        if self.state == Fsm.START_MENU:
            if(self.gui.get_pos()):
                self.state = Fsm.SETUP_MENU
            else:
                self.state = Fsm.PREHEAT
                self.start_temp = self.ntc.get_temp()
                self.start_time = int(time.time())
                return 1
        elif self.state == Fsm.SETUP_MENU:            
            pos = self.gui.get_pos()
            if pos == 0:
                self.state = Fsm.SOAK_TIME
            elif pos == 1:
                self.state = Fsm.PREHEAT_TEMP
            elif pos == 2:
                self.state = Fsm.REFLOW_TIME
            elif pos == 3:
                self.state = Fsm.REFLOW_TEMP
            elif pos == 4:
                self.state = Fsm.START_MENU
        elif (self.state >= Fsm.SOAK_TIME) & (self.state <= Fsm.REFLOW_TEMP):
            self.state = Fsm.SETUP_MENU
        self.gui.display_frame(self.state)
        return 0    
    
    def running_update_state(self):
        self.led.high()
        self.curr_temp = self.ntc.get_temp()
        if (self.elapsed_time == 0) & (self.curr_temp >= Fsm.cooldown_temp):
            self.ssr.duty_u16(0)
            self.state = Fsm.COOLDOWN
        if self.state == Fsm.PREHEAT:
            self.update_pwm()
            #self.pid.setpoint = (self.start_temp + int(self.elapsed_time))
            self.pid.setpoint = self.preheat_temp
            #self.pid.setpoint = 50
            if self.curr_temp >= self.preheat_temp:
                self.state = Fsm.SOAK
                self.timestamp = self.elapsed_time
                
        if self.state == Fsm.SOAK:
            self.update_pwm()
            self.pid.setpoint = self.preheat_temp
            if (self.elapsed_time - self.timestamp) >= self.soak_time:
                self.state = Fsm.RAMPUP
                self.timestamp = self.elapsed_time
                
        if self.state == Fsm.RAMPUP:
            self.update_pwm()
            self.pid.setpoint = self.preheat_temp + (self.elapsed_time-self.timestamp)
            if self.curr_temp >= self.reflow_temp:
                self.state = Fsm.REFLOW
                self.timestamp = self.elapsed_time
                
        if self.state == Fsm.REFLOW:
            self.update_pwm()
            self.pid.setpoint = self.reflow_temp
            if (self.elapsed_time - self.timestamp) >= self.reflow_time:
                self.state = Fsm.COOLDOWN
                
        if self.state == Fsm.COOLDOWN:
            self.ssr.duty_u16(0)
            if self.curr_temp <= Fsm.cooldown_temp:
                self.state = Fsm.START_MENU
                self.gui.display_frame(self.state)
                self.elapsed_time = 0
                self.start_temp = 0
                self.start_time = 0
                self.led.low()
                return 0
        
        if self.elapsed_time + 1  == (int(time.time()-self.start_time)):
            self.gui.display_frame(self.state)
            self.gui.display_info(self.curr_temp, self.elapsed_time)
            #print("calc: " + str((self.pid(self.curr_temp))))
            #print("set: " + str(self.pid.setpoint))
            if self.state != Fsm.COOLDOWN:        
                print("duty:" + str(self.duty_cycle))
            
        self.elapsed_time = (int(time.time()-self.start_time))                 
        return 1
    
    def update_pwm(self):
        self.duty_cycle = self.pid(self.curr_temp)       
        if self.duty_cycle > self.maxDuty:
            self.duty_cycle = self.maxDuty
        if self.duty_cycle < self.minDuty:
            self.duty_cycle = self.minDuty
        self.ssr.duty_u16(int(self.duty_cycle))
        
            
            
        
    

