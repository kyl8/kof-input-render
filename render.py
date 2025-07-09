import ctypes
import ctypes.wintypes
import time
import logging
import keyboard
import os
from pyvjoystick import vjoy


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SW_RESTORE = 9  # restore the window if minimized
SW_SHOW = 5  # show the window if it is not visible
HWND_TOPMOST = -1  # set the window to be topmost
HWND_NOTOPMOST = -2  # remove the topmost status

# defining ctypes prototypes for windows api functions
user32 = ctypes.windll.user32
FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
FindWindowW.restype = ctypes.wintypes.HWND

ShowWindow = user32.ShowWindow
ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
ShowWindow.restype = ctypes.wintypes.BOOL

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
SetForegroundWindow.restype = ctypes.wintypes.BOOL

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.wintypes.HWND

#TODO: BIND "KL" TYPE INPUTS: B+C
#TODO: "HOLDING" DIRECTIONAL FUNCTION
class ControllerBindings():
    def __init__(self, device_id=1, fps=60, window_title="Fightcade FBNeo v0.2.97.44-55"):
        self.j = vjoy.VJoyDevice(device_id)
        self.UP = 0x8000
        self.DOWN = 0x1
        self.LEFT = 0x1
        self.RIGHT = 0x8000
        self.NEUTRAL = 16384
        self.screen_width = 40
        self.screen_height = 20

        #sleep
        self.fps = fps 
        self.init = time.time()
        self.last_frame =  self.init
        self.frame_counter = 0

        # window
        self.window_title = window_title
        self.last_focus_time = 0
        self.focus_cooldown = 10
        self.joystick_data = self.j._data

        # directional bindings
        self.directional_bindings_x = {
            'a': self.LEFT,
            'd': self.RIGHT,
        }

        self.directional_bindings_y = {
            'w': self.UP,
            's': self.DOWN
        }

        # attack bindings
        self.attack_bindings = {
            'j': 1,  # Light Punch #A
            'k': 2,  # Heavy Punch #C
            'l': 3,  # Light Kick  #B
            'm': 4  # Heavy Kick  #D
        }

        # current state
        self.current_x = self.NEUTRAL
        self.current_y = self.NEUTRAL
        self.fps = 1/60
        self.current_frame = 0 
        self.button_states = {btn: 0 for btn in self.attack_bindings.values()}

    def sleep(self, delay, unit='seconds'):
        """frame based "sleep" function, it actually dont works very well cuz sleep is a threading blocking function"""
        if unit == 'frames':
            seconds = delay * (1.0 / self.fps)
        elif unit == 'seconds':
            seconds = delay
        else:
            seconds = 0

        time.sleep(seconds)

        self.frame_counter += delay

    
    def time_in_seconds(self):
        return time.time() - self.init

    def frames_passed(self):
        return self.frame_counter
    
    def force_window_focus(self, max_attempts=3) -> bool:
        """search for game window and focus it"""
        attempt = 0
        hwnd = None

        current_time = time.time()
        if current_time - self.last_focus_time < self.focus_cooldown:
            return True

        while attempt < max_attempts:
            try:
                hwnd = FindWindowW(None, self.window_title)
                if not hwnd:
                    logging.warning(f"Window '{self.window_title}' not found (attempt {attempt + 1}/{max_attempts})")
                    attempt += 1
                    time.sleep(1)
                    continue

                ShowWindow(hwnd, SW_RESTORE)
                SetForegroundWindow(hwnd)
                self.last_focus_time = time.time()
                logging.info(f"Window found: '{self.window_title}'")
                return True

            except Exception as e:
                logging.error(f"Focus error: {str(e)}")
                attempt += 1
                time.sleep(1)
        return False
        
    def update_joystick(self, button: str, duration=0.05):
        """joystick render"""
        self.j.reset_povs()
        if button in self.directional_bindings_x:
            self.j.set_axis(vjoy.HID_USAGE.X, self.directional_bindings_x[button])
            self.current_x = self.directional_bindings_x[button]
        elif button in self.directional_bindings_y:
            self.j.set_axis(vjoy.HID_USAGE.Y, self.directional_bindings_y[button])
            self.current_y = self.directional_bindings_y[button]
        else:
            # return to neutral if button is not a direction
            self.j.set_axis(vjoy.HID_USAGE.X, self.NEUTRAL)
            self.j.set_axis(vjoy.HID_USAGE.Y, self.NEUTRAL)
            self.current_x = self.NEUTRAL
            self.current_y = self.NEUTRAL
        
        self.j.update()
        
        # return to neutral after duration
        self.j.set_axis(vjoy.HID_USAGE.X, self.NEUTRAL)
        self.j.set_axis(vjoy.HID_USAGE.Y, self.NEUTRAL)
        self.current_x = self.NEUTRAL
        self.current_y = self.NEUTRAL
        self.j.update()

    def update_button(self, button: str, duration=0.05):
        """button render"""
        try:
            btn_num = self.attack_bindings.get(button)
            if btn_num is None:
                logging.error(f"Button {button} not mapped!")
                return

            self.j.set_button(btn_num, 1)
            self.button_states[btn_num] = 1

            self.j.set_button(btn_num, 0)
            self.button_states[btn_num] = 0
            self.j.update()
            
            logging.debug(f"Pressed button {button} (ID: {btn_num}) for {duration}s")
        except Exception as e:
            logging.error(f"vJoy error on button {button}: {str(e)}")

    def update_button2(self, button: str, duration=0.05):
        """button render"""
        try:
            # pyvjoy wrapper doesn't use "True" or "False" for button state, it uses 1 or 0
            self.j.set_button(self.attack_bindings[button], 1)
            self.button_states[self.attack_bindings[button]] = 1
            self.j.update()
            # releasing the button is essential to avoid stuck inputs
            self.j.set_button(self.attack_bindings[button], 0)
            self.button_states[self.attack_bindings[button]] = 0
            self.j.update()
            logging.debug(f"Pressed button {button} for {duration}s")
        except Exception as e:
            logging.error(f"vJoy error: {str(e)}")
    
    def combo(self, buttons: list, delays: list, unit='seconds'):
        """Execute a sequence of buttons with delays between them"""
        for button, delay in zip(buttons, delays):
            if button in self.directional_bindings_x or button in self.directional_bindings_y:
                self.update_joystick(button)
            elif button in self.attack_bindings:
                self.update_button2(button)
                
            else:
                logging.error(f"{button} is not binded or doesn't exist")
            self.sleep(delay, unit=unit)


if __name__ == "__main__":
    controller = ControllerBindings()
    while True:
        controller.combo(buttons=["j", "k", "l"], delays=[0, 0, 0], unit='0') 


