import machine
from machine import Pin
import time
from ui import Rotary
from FSM import Fsm

rotary = Rotary(3,2,4)
fsm = Fsm()

#force power supply in PWM mode (fixes false inputs from rotary caused by power supply noise)
Pin(23, Pin.IN).high()

flag = False
running = False
action = 0
test = 0
TEMP_CHECK = 3

def rotary_changed(change):
    global flag, action
    flag = True
    action = change
      
rotary.add_handler(rotary_changed)

while True:   
    if running & (action == 0):
       time.sleep(0.01)
     
    if flag | running:
        running = fsm.update_fsm(action)
        action = 0
        flag = False
    else:
        running = fsm.update_fsm(TEMP_CHECK)
        time.sleep(0.2)

