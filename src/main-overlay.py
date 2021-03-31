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

# Helper functions
def radius_to_bounding_box(x, y, r):
    return (x-r, y-r, x+r, y+r)

def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
Canvas.create_circle = _create_circle

def _update_object(self, obj, x, y, r):
    return self.coords(obj, x-r, y-r, x+r, y+r)
Canvas.update_object = _update_object

class OverlayApplication(Application):
    def __init__(self):
        super().__init__()
        
        self.notes_in_animation = []
        # Precomputed value, we will add this expansion rate to expand the bounding box with every animation tick
        self.bbox_expansion_rate_per_frame = 0
        # Also another precomputed value
        self.charmap = {}

        # UI and config variables
        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        # Convert white to transparent
        self.root.wm_attributes("-transparentcolor", "white")

        # create the string values for the entries that invoke an event after being changed
        self.sv_radius = StringVar(self.root, value=str(29))
        self.sv_x_spacing = StringVar(self.root, value=str(60))
        self.sv_y_spacing = StringVar(self.root, value=str(44))

        # create all of the main containers
        top_frame = Frame(self.root)
        top_frame.pack(anchor=N, expand=True, fill=X)
        center = Frame(self.root, bg='gray2', padx=2, pady=2)

        # layout all of the main containers
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        top_frame.grid(row=0, sticky="ew")
        center.grid(row=1, sticky="nsew")

        # Make write callbacks whenever the SVs are modified; this allows us to update the outlines as needed
        self.sv_radius.trace_add("write", lambda name, index, mode, sv=self.sv_radius: self.reformat_outlines_callback(self.sv_radius))
        self.sv_y_spacing.trace_add("write", lambda name, index, mode, sv=self.sv_y_spacing: self.reformat_outlines_callback(self.sv_y_spacing))
        self.sv_x_spacing.trace_add("write", lambda name, index, mode, sv=self.sv_x_spacing: self.reformat_outlines_callback(self.sv_x_spacing))

        # create the widgets for the top frame
        label_file = Label(top_frame, text='Filepath:')
        entry_file = Entry(top_frame, background="lavender", textvariable=self.sv_filename)
        label_radius = Label(top_frame, text='Circle radius')
        entry_radius = Entry(top_frame, background="lavender", textvariable=self.sv_radius)
        label_x_spacing = Label(top_frame, text='Circle x spacing')
        entry_x_spacing = Entry(top_frame, background="lavender", textvariable=self.sv_x_spacing)
        label_y_spacing = Label(top_frame, text='Circle y spacing')
        entry_y_spacing = Entry(top_frame, background="lavender", textvariable=self.sv_y_spacing)
        button_play = Button(top_frame, text='Play', background="red", command=self.play_btn_press)
        label_descriptlabel = Label(top_frame, text='Song Name', textvariable=self.sv_descriptlabel)

        # Store in list for us to enable / disable
        self.inputObjects.append(entry_file)
        self.inputObjects.append(entry_radius)
        self.inputObjects.append(entry_x_spacing)
        self.inputObjects.append(entry_y_spacing)
        self.inputObjects.append(button_play)

        # layout the widgets in the top frame
        label_file.grid(row=0, column=0)
        entry_file.grid(row=0, column=1)
        button_play.grid(row=0, column=2)
        label_radius.grid(row=0, column=3)
        entry_radius.grid(row=0, column=4)
        label_x_spacing.grid(row=0, column=5)
        entry_x_spacing.grid(row=0, column=6)
        label_y_spacing.grid(row=0, column=7)
        entry_y_spacing.grid(row=0, column=8)
        label_descriptlabel.grid(row=1, column=0, columnspan=9)

        # create & layout the canvas
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=1)

        r = int(self.sv_radius.get())
        x_offset = int(self.sv_x_spacing.get())
        y_offset = int(self.sv_y_spacing.get())

        self.canvas = Canvas(center, bg='white', height=((r+y_offset) * (BUTTON_ROWS + 2)), width=((r+x_offset) * (BUTTON_COLS + 2)))
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.redraw_outlines()

        self.root.mainloop()

    def reformat_outlines_callback(self, sv):
        if (sv.get().isdigit()):
            self.redraw_outlines()
            return True
        return False
        
    def redraw_outlines(self):
        self.canvas.delete("all")
        r = int(self.sv_radius.get())
        x_offset = int(self.sv_x_spacing.get())
        y_offset = int(self.sv_y_spacing.get())

        curr_x = r + x_offset
        curr_y = r + y_offset
        
        for i in range(BUTTON_ROWS):
            for j in range(BUTTON_COLS):
                self.keyboard_outline_objs.append(self.canvas.create_circle(curr_x, curr_y, r, outline="red", width=3))
                self.keyboard_outline_objs.append(self.canvas.create_circle(curr_x, curr_y, 11, outline="#FFF9EF", fill="#FFF9EF"))
                self.keyboard_outline_objs.append(self.canvas.create_text(curr_x, curr_y,fill="black",font="Times 14 bold", text=KEYS[i][j]))
                curr_x += r + x_offset
            curr_x = r + x_offset
            curr_y += r + y_offset

    def set_bbox_expansion_rate_per_frame(self):
        bounding_box_width = int(self.sv_radius.get())
        self.bbox_expansion_rate_per_frame = bounding_box_width / 1000.0 * FRAME_RATE / (SECONDS_TO_START_ANIMATION * 1.0)

    def set_charmap(self):
        r = int(self.sv_radius.get())
        x_offset = int(self.sv_x_spacing.get())
        y_offset = int(self.sv_y_spacing.get())

        curr_x = r + x_offset
        curr_y = r + y_offset

        for row in KEYS:
            for k in row:
                self.charmap[k] = (curr_x, curr_y)
                curr_x += r + x_offset
            curr_x = r + x_offset
            curr_y += r + y_offset

    # Overriden method
    def post_play_press_pre_data_parse(self):
        self.set_bbox_expansion_rate_per_frame()
        self.set_charmap()
        self.songdata_idx = 1

    # Overriden method
    def play_char_note(self, c):
        if c in self.charmap:
            curr_x, curr_y = self.charmap[c]
            self.notes_in_animation.append((0, self.canvas.create_circle(curr_x, curr_y, 0, outline="blue", width=2)))
    
    # Overriden method
    def animate_object(self, i, iterations, obj):
        # Get coords
        x1, y1, x2, y2 = self.canvas.coords(obj)
        # Update using expansion rate
        self.canvas.coords(obj, 
            x1 - self.bbox_expansion_rate_per_frame, 
            y1 - self.bbox_expansion_rate_per_frame, 
            x2 + self.bbox_expansion_rate_per_frame, 
            y2 + self.bbox_expansion_rate_per_frame)
        self.notes_in_animation[i] = (iterations + 1, obj)

if __name__ == "__main__":
    my_application = OverlayApplication()
