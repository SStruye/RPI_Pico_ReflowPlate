from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import utime as time
import micropython

class Rotary:   
    ROT_CW = 1
    ROT_CCW = -1
    SW_PRESS = 2
    
    def __init__(self,dt,clk,sw):
        self.dt_pin = Pin(dt, Pin.IN)
        self.clk_pin = Pin(clk, Pin.IN)
        self.sw_pin = Pin(sw, Pin.IN)
        self.last_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        self.dt_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.clk_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.sw_pin.irq(handler=self.switch_detect, trigger=Pin.IRQ_RISING )
        self.handlers = []
        self.last_button_status = self.sw_pin.value()
        
    def rotary_change(self, pin):
        new_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        if new_status == self.last_status:
            return
        transition = (self.last_status << 2) | new_status
        if transition == 0b1110:
            try:
                micropython.schedule(self.call_handlers, Rotary.ROT_CW)
            except RuntimeError:
                return
        elif transition == 0b1101:
            try:
                micropython.schedule(self.call_handlers, Rotary.ROT_CCW)
            except RuntimeError:
                return
        self.last_status = new_status
        
    def switch_detect(self,pin):
        time.sleep(0.1)
        if self.sw_pin.value() != 0:
            micropython.schedule(self.call_handlers, Rotary.SW_PRESS)
            
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def call_handlers(self, type):
        for handler in self.handlers:
            handler(type)

class Gui:    
    FRAME 	= ['start',['setup','setStime','setStemp','setRtime','setRtemp'], ['preheat','soak','rampup','reflow'], 'cooldown']
    
    def __init__(self, sda, scl):
        self.i2c = I2C(0, sda=Pin(sda), scl=Pin(scl))
        self.display = SSD1306_I2C(128, 64, self.i2c)
        self.curr_pos = 0
        self.last_pos = 0
        self.curr_frame = STATE[0]
        
        self.soak_time	= 90
        self.preheat_temp = 120    
        self.reflow_time = 60
        self.reflow_temp = 180
        
        self.update_frame(STATE[0], 0)
        self.arrUp = [[0,0,0,1,1,0,0,0],[0,0,1,0,0,1,0,0],[0,1,0,0,0,0,1,0],[1,0,0,0,0,0,0,1]]
        self.arrDn = [[1,0,0,0,0,0,0,1],[0,1,0,0,0,0,1,0],[0,0,1,0,0,1,0,0],[0,0,0,1,1,0,0,0]]                
    
    def update_frame(self, state, pos = 0, param = 0):
'''START MENU'''
        if state == GUI.FRAME[0]:
            if self.curr_frame == state:
                self.update_pos(pos)
            else:
                self.curr_frame = state
                self.display_start_menu()                
'''SETUP MENU'''
        elif state == GUI.FRAME[1][0]:
            if self.curr_frame == state:
                self.update_pos(pos)
            else:
                self.curr_frame = state
                self.display_setup_menu()                
'''SET CURVE'''
    elif state == GUI.FRAME[1][self.last_pos]
        if self.curr_frame == state:
            self.update_parameters(param)
        else:
            self.curr_frame == state
            self.display_setup_params()
            self.update_parameters(param)
            
    
            
    def display_start_menu(self):
        self.display.text("Reflow plate v.1", 0,3,1)
        self.display.text("SET TEMP CURVE", 0,16,1)
        self.display.text("START REFLOW", 0,26,1)
        self.display.hline(0, 14, 128, 1)
        self.invert_pos(self.last_pos)
        
    def display_setup_menu(self):
        self.display.text("Reflow setup", 0,3,1)
        self.display.text("SOAK TIME", 0,16,1)
        self.display.text("PREHEAT TEMP.", 0,26,1)
        self.display.text("REFLOW TIME", 0,36,1)
        self.display.text("REFLOW TEMP.", 0,46,1)
        self.display.text("<", 0,56,1)
        self.display.hline(0, 14, 128, 1)
        self.invert_pos(self.last_pos)
        
    def display_setup_params(self):        
        if self.curr_frame == GUI.FRAME[1][1]:
            title = "Soak time(sec)"           
        if self.curr_frame == GUI.FRAME[1][2]:
            title = "Preheat temp(C)"
        if self.curr_frame == GUI.FRAME[1][3]:
            title = "Reflow time(sec)"
        if self.curr_frame == GUI.FRAME[1][4]:
            title = "Reflow temp(C)"
        self.display.fill(0)
        self.display.text(title, 0,3,1)
        self.show_arrows()
        
    def display_running_frames(self):
        self.display.fill(0)
        if self.curr_frame == Gui.PREHEAT:
            title = "Preheat"
        if self.curr_frame == Gui.SOAK:
            title = "Soak"
        if self.curr_frame == Gui.RAMPUP:
            title = "Rampup"
        if self.curr_frame == Gui.REFLOW:
            title = "Reflow"
        if self.curr_frame == Gui.COOLDOWN:
            title = "Cooldown"
        self.display.text(title, 0,3,1)
        self.display.hline(0, 14, 128, 1)
    
    def update_parameters(self, value=0):
        self.display.fill_rect(0, 39, 128, 7, 0) 
        if self.curr_frame == Gui.SOAK_TIME:
            if value == 0:
                param = self.soak_time
            else:
                param = value
                self.soak_time = param
        elif self.curr_frame == Gui.PREHEAT_TEMP:
            if value == 0:
                param = self.preheat_temp
            else:
                param = value
                self.preheat_temp = param
        elif self.curr_frame == Gui.REFLOW_TIME:
            if value == 0:
                param = self.reflow_time
            else:
                param = value
                self.reflow_time = param
        elif self.curr_frame == Gui.REFLOW_TEMP:
            if value == 0:
                param = self.reflow_temp
            else:
                param = value
                self.reflow_temp = param
        
        if param > 99:
            self.display.text(str(param), 53,39, 1)
        else:
            self.display.text(str(param), 57,39, 1)                  
        self.display.show()
        
    def update_pos(self, pos):
        self.invert_pos(self.curr_pos)
        self.invert_pos(self.last_pos)
        self.last_pos = self.curr_pos
        self.display.show()

    
    def invert_pos(self, offset):
        for x in range(127):
            for y in range((offset*10)+16, ((offset*10)+23)):
                    if self.display.pixel(x,y):
                       self.display.pixel(x,y,0)
                    else:
                        self.display.pixel(x,y,1)
                                    
    def show_arrows(self):
        for y in range(4):
            for x in range(8):
                if self.arrUp[y][x]:
                    self.display.pixel(x+61,y+26, 1)
                if self.arrDn[y][x]:
                    self.display.pixel(x+61,y+56, 1)
    
    def display_info(self, temp, time):
        self.display.fill_rect(0, 39, 128, 7, 0)
        self.display.text("Temp: "+"{:.2f}".format(temp)+ "'C", 0,19, 1)
        self.display.text("Time: "+"{0}".format(time)+"sec", 0,29, 1)
        self.display.show()
            
        
