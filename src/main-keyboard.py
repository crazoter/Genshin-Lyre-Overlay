# Requirements: Python3, Tkinter, PIL
# install PIL using pip install pillow
import time
import json

from application import *
from typing import List
from tkinter import *
from PIL import ImageTk, Image

# I assume most are right handed and play 4 fingers on right side
LEFT_HAND_KEY_LIST = {
    'Q','W','E',
    'A','S','D',
    'Z','X','C'
}

class KeyboardApplication(Application):
    def __init__(self):
        super().__init__()

        self.KB_SECONDS_TO_START_ANIMATION = 10        # Number of seconds before we begin animating the circle
        self.KB_ITERATIONS_UNTIL_ANIM_OVER = self.FPS * self.KB_SECONDS_TO_START_ANIMATION
        # oops magic numbers; this is based on hardcoded height
        self.KB_DROP_RATE = 350 / self.KB_ITERATIONS_UNTIL_ANIM_OVER                  
        self.songspeed = 1
        # self.kB_drop_rate = 0

        # create the string values for the entries that invoke an event after being changed
        self.sv_speed = StringVar(self.root, value="1")

        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        # Convert white to transparent
        # self.root.wm_attributes("-transparentcolor", "white")

        label_speed = Label(self.top_frame, text='Speed Multiplier:')
        entry_speed = Entry(self.top_frame, background="lavender", textvariable=self.sv_speed)
        label_descriptlabel = Label(self.top_frame, text='Song Name', textvariable=self.sv_descriptlabel)

        # Store in list for us to enable / disable
        self.inputObjects.append(entry_speed)

        # layout the widgets in the top frame
        label_speed.grid(row=0, column=3)
        entry_speed.grid(row=0, column=4)
        label_descriptlabel.grid(row=1, column=0, columnspan=9)

        # create & layout the canvas
        self.canvas = Canvas(self.center, bg='white', height=500, width=(900))
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.create_text(10, 375,fill='black', font="Times 16 bold", text='1')
        self.canvas.create_text(10, 395,fill='black', font="Times 16 bold", text='2')
        self.canvas.create_text(10, 415,fill='black', font="Times 16 bold", text='3')

        # Draw buttons and grid
        for i in range(self.BUTTON_COLS * self.BUTTON_ROWS):
            offset = 40 + i * 40
            key = KEY_LIST[i].upper()
            colour = "#f00"
            if key in LEFT_HAND_KEY_LIST:
                colour = "#00f"

            height_offset = 375
            if key in KEYS[1]:
                height_offset = 395
            elif key in KEYS[2]:
                height_offset = 415
            self.canvas.create_rectangle(offset, 350, offset + 20, 360, outline="#fb0", fill="#fb0")
            self.canvas.create_text(offset + 12, height_offset, fill=colour, font="Times 16 bold", text=key)

    # Overriden method
    def post_play_press_pre_data_parse(self):
        self.songspeed = 1 / float(self.sv_speed.get())

    # Overriden method
    def play_char_note(self, c):
        if c in KEY_IDX_MAP:
            curr_x = 40 + KEY_IDX_MAP[c] * 40
            colour = "#f00"
            if c in LEFT_HAND_KEY_LIST:
                colour = "#00f"
            self.notes_in_animation.append(
                (0, self.canvas.create_rectangle(curr_x, 0, curr_x + 20, 14, outline=colour, fill=colour))
            )
            self.notes_in_animation.append(
                (0, self.canvas.create_text(curr_x + 10, 6, fill='yellow', font="Times 8 bold", text=c))
            )
    
    # Overriden method
    def animate_object(self, i, note_in_animation):
        # Get coords
        iterations, obj = note_in_animation
        coords = self.canvas.coords(obj)
        if len(coords) == 4:
            # Boxes have 4 coordinates
            x1, y1, x2, y2 = coords
            # Update using expansion rate
            self.canvas.coords(obj, 
                x1, y1 + self.KB_DROP_RATE, 
                x2, y2 + self.KB_DROP_RATE)
        else:
            # Text only have 2 coordinates
            x, y = coords
            # Update using expansion rate
            self.canvas.coords(obj, x, y + self.KB_DROP_RATE)
        self.notes_in_animation[i] = (iterations + 1, obj)

if __name__ == "__main__":
    my_application = KeyboardApplication()
    my_application.start()
