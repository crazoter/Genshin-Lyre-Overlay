"""
    This program contains code adapted from: Lyre Midi Player (https://github.com/3096/genshin_scripts/blob/main/midi.py) 
    which is under the GNU General Public License.
"""

# Requirements: Python3, Tkinter, PIL
# install PIL using pip install pillow
import time
import json

from application import *
from typing import List
from tkinter import *
from PIL import ImageTk, Image

DROP_RATE = 350 / ITERATIONS_UNTIL_ANIM_OVER                  # oops magic numbers; this is based on hardcoded height

# I assume most are right handed and play 4 fingers on right side
LEFT_HAND_KEY_LIST = {
    'Q','W','E',
    'A','S','D',
    'Z','X','C'
}

class KeyboardApplication(Application):
    def __init__(self):
        super().__init__()

        self.songspeed = 1
        self.drop_rate = 0

        # create the string values for the entries that invoke an event after being changed
        self.sv_speed = StringVar(self.root, value="1")

        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        # Convert white to transparent
        # self.root.wm_attributes("-transparentcolor", "white")

        # create all of the main containers
        top_frame = Frame(self.root)
        top_frame.pack(anchor=N, expand=True, fill=X)
        center = Frame(self.root, bg='gray2', padx=2, pady=2)

        # layout all of the main containers
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        top_frame.grid(row=0, sticky="ew")
        center.grid(row=1, sticky="nsew")

        # create the widgets for the top frame
        label_file = Label(top_frame, text='Filepath:')
        entry_file = Entry(top_frame, background="lavender", textvariable=self.sv_filename)
        label_speed = Label(top_frame, text='Speed Multiplier:')
        entry_speed = Entry(top_frame, background="lavender", textvariable=self.sv_speed)
        button_play = Button(top_frame, text='Play', background="red", command=self.play_btn_press)
        label_descriptlabel = Label(top_frame, text='Song Name', textvariable=self.sv_descriptlabel)

        # Store in list for us to enable / disable
        self.inputObjects.append(entry_file)
        self.inputObjects.append(entry_speed)
        self.inputObjects.append(button_play)

        # layout the widgets in the top frame
        label_file.grid(row=0, column=0)
        entry_file.grid(row=0, column=1)
        button_play.grid(row=0, column=2)
        label_speed.grid(row=0, column=3)
        entry_speed.grid(row=0, column=4)
        label_descriptlabel.grid(row=1, column=0, columnspan=9)

        # create & layout the canvas
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=1)
        self.canvas = Canvas(center, bg='white', height=500, width=(900))
        self.canvas.create_text(10, 375,fill='black', font="Times 16 bold", text='1')
        self.canvas.create_text(10, 395,fill='black', font="Times 16 bold", text='2')
        self.canvas.create_text(10, 415,fill='black', font="Times 16 bold", text='3')

        # Draw buttons and grid
        for i in range(BUTTON_COLS * BUTTON_ROWS):
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

        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.root.mainloop()

    # Overriden method
    def post_play_press_pre_data_parse(self):
        self.songdata_idx = 1
        self.songspeed = 1 / float(self.sv_speed.get())

    # Overriden method
    def play_char_note(self, c):
        if c in KEY_IDX_MAP:
            curr_x = 40 + KEY_IDX_MAP[c] * 40
            colour = "#f00"
            if c in LEFT_HAND_KEY_LIST:
                colour = "#00f"
            self.notes_in_animation.append(
                (0, self.canvas.create_rectangle(curr_x, 0, curr_x + 20, 10, outline=colour, fill=colour))
            )
    
    # Overriden method
    def animate_object(self, i, iterations, obj):
        # Get coords
        x1, y1, x2, y2 = self.canvas.coords(obj)
        # Update using expansion rate
        self.canvas.coords(obj, 
            x1, y1 + DROP_RATE, 
            x2, y2 + DROP_RATE)
        self.notes_in_animation[i] = (iterations + 1, obj)

if __name__ == "__main__":
    my_application = KeyboardApplication()
