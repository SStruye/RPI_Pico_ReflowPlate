import machine
from PID import PID
from machine import Pin, PWM
import time
from ui import Gui
from thermistor import Thermistor

class FSM:    
    STATE 	= ['start',['setup','setStime','setStemp','setRtime','setRtemp'], ['preheat','soak','rampup','reflow'], 'cooldown']
   
    R_CW = 1
    R_CC = -1
    R_SW = 2
   
    sTIME	= 30
    sTEMP	= 100
    rTIME	= 30
    rTEMP	= 180
    cdTEMP	= 40
    
    def __init__(self):
        self.curr_state = 0
        self.position 	= 0
        self.curve		= [FSM.sTIME, FSM.sTEMP, FSM.rTIME, FSM.rTEMP]
               
        self.ntc 		= Thermistor(26, 27)
        self.curr_temp 	= 0
        
        self.gui 		= GUI(20, 21)
        
    def update_fsm(self, action):
        
        self.curr_temp = self.ntc.get_temp()
        
        if self.curr_temp >= FSM.cdTEMP:
            self.curr_state = FSM.STATE[3]
        
        if action == 0:
            if any(self.curr_state in i for i in FSM.STATE[:2]):		# No action	--> no update if state is menu or setup
                return 0
        
#START MENU
        if self.curr_state == FSM.STATE[0]:	                       
            if action == R_SW:						# if button	-> update state
                if self.position == 0:
                    self.curr_state = FSM.STATE[1][0]
                else:
                    self.curr_state = FSM.STATE[2][0]                                
            else:									# if rotate	-> update pos
                self.position + action
                if self.position > 1: self.position = 0
                if self.position < 0: self.position = 1
#SETUP MENU                
        elif self.curr_state == FSM.STATE[1][0]:
            if action == FSM.R_SW:					# if button	-> update state
                if self.position == 4:
                    self.curr_state = FSM.STATE[0]
                    self.position = 0
                else:
                    self.curr_state == FSM.STATE[1][self.position]
            else:									# if rotate	-> update pos
                self.position + action
                if self.position > 4: self.position = 0
                if self.position < 0: self.position = 4
#SET CURVE                
        elif self.curr_state == FSM.STATE[1][self.position]:
            if action == FSM.R_SW:					# if button	-> update state
                self.curr_state = FSM.STATE[0]
            else:									# if rotate	-> update curve value
                self.curve[self.position] += action
                gui.update_value(self.curr_state, self.curve[self.position])
'''PREHEAT'''           
        elif self.curr_state == FSM.STATE[2][0]:        
            #
'''SOAK'''
        elif self.curr_state == FSM.STATE[2][1]:
            #
'''RAMPUP'''
        elif self.curr_state == FSM.STATE[2][2]:
            #
'''REFLOW'''
        elif self.curr_state == FSM.STATE[2][3]:
            #
'''COOLDOWN'''
        elif self.curr_state == FSM.STATE[3]:
            if self.curr_temp <= FSM.cdTEMP:
                self.curr_state = FSM.STATE[0]
 
'''UPDATE FRAME'''
        gui.update_frame(self.curr_state, self.position, self.curve[self.position])
        return 0
            
        
            
            
        
    
