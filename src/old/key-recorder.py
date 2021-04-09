# This key-recorder only works if it is able to record your keypresses. This is unlikely to happen with the Genshin client.
# Use the key-recorder-2.py application instead, which records key preesses by screenshots

# Requirements: Python3, Tkinter, PIL, pynput
# install PIL using pip3 install pillow
# install pynput using pip3 install pynput

from multiprocessing import Process, Lock
from pynput import keyboard
import time

from tkinter import *
from tkinter import scrolledtext

KEY_LIST = [ 'Z', 'X', 'C', 'A', 'S', 'D', 'Q', 'W', 'E', 'V', 'B', 'N', 'M', 'F', 'G', 'H', 'J', 'R', 'T', 'Y', 'U' ]

class KeyRecordApplication():
    def __init__(self):
        super().__init__()
        self.root = Tk()
        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        self.root.title('Record pressed keys. You must press an arbitrary button to record the last key.')

        # create the string values for the entries that invoke an event after being changed
        self.center = Frame(self.root, bg='gray2', padx=2, pady=2)
        self.center.grid(sticky="nsew")

        text_format1 = scrolledtext.ScrolledText(self.center, wrap=WORD)
        text_format1.grid(row=0, column=0)
        text_strokes = scrolledtext.ScrolledText(self.center, wrap=WORD)
        text_strokes.grid(row=0, column=1)

        self.prev_press = -1
        self.prev_sequence = ''
        frame_time = 1000 / 30
        def current_milli_time():
            return int(time.time() * 1000)

        def append_txt(text, value):
            # Trim last character which is always \n
            value = text.get("1.0",END)[:-1] + value
            text.delete(1.0, END)
            text.insert(END, value)

        append_txt(text_format1, "Song Name\nFormat: 1\nSPEED 1.0\n")
        # Delete the persistent starting new line 
        # text_format1.delete(1.0)

        # Start keyboard listener        
        def on_press(key):
            # Key may not always have char (...Why isn't it just set to None?)
            if hasattr(key, 'char'):
                key_val = key.char.upper()
                if key_val in KEY_LIST:
                    if self.prev_press == -1:
                        self.prev_press = current_milli_time()
                        self.prev_sequence += key_val
                    else:
                        curr_time = current_milli_time()
                        time_elapsed = curr_time - self.prev_press
                        if time_elapsed >= frame_time:
                            append_txt(text_format1, "{0} {1}\n".format(self.prev_sequence, time_elapsed))
                            space = ""
                            # Use arbitrary constant to denote when to add spaces (lol)
                            # This is around 300+ms
                            if time_elapsed > frame_time * 10:
                                space = " "
                            if len(self.prev_sequence) > 1:
                                append_txt(text_strokes, "{0}({1})".format(space, self.prev_sequence))
                            else:
                                append_txt(text_strokes, "{0}{1}".format(space, self.prev_sequence))

                            self.prev_sequence = ''
                            self.prev_press = curr_time
                        self.prev_sequence += key_val
                    print(key_val, "pressed")
                    
                

        # Collect events until released
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Setup the listener stop function by setting it to stop on window exit
        def on_closing():
            listener.stop()
            self.root.destroy()

        # Since we're using a 2nd thread for keypress detection, we'll need to handle the GUI closing fx
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        self.root.mainloop()

if __name__ == "__main__":
    my_application = KeyRecordApplication()
