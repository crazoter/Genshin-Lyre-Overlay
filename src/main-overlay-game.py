"""
    This program contains code adapted from: Lyre Midi Player (https://github.com/3096/genshin_scripts/blob/main/midi.py) 
    which is under the GNU General Public License.
"""

# Requirements: Python3, Tkinter, PIL, pynput
# install PIL using pip3 install pillow
# install pynput using pip3 install pynput
import queue
# import keyboard  
import threading
import random
from multiprocessing import Process, Lock
from pynput.keyboard import Key, Listener
import time
import json

from application import *
from typing import List
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image

"""
def app_keyboard_loop(my_application):
    # Create another thread that monitors the keyboard
    while True:
        if not my_application.ui_enabled:
            my_application.keys_and_timings_mutex.acquire()
            if c in my_application.keys_and_timings_to_track:
                my_application.keys_and_timings_to_track[c] += 1
            else:
                my_application.keys_and_timings_to_track[c] = 1
            my_application.scoreables += 1
            my_application.keys_and_timings_mutex.release()
            if keyboard.is_pressed('esc'):
                my_application.score += 1
        time.sleep(0.1)  # seconds
"""

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
        self.keys_and_timings_to_track = {}
        self.keys_and_timings_mutex = Lock()

        self.score = 0
        self.scoreables = 0
        self.false_notes = 0

        # UI and config variables
        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        # Convert white to transparent
        self.root.wm_attributes("-transparentcolor", "white")

        # create the string values for the entries that invoke an event after being changed
        self.sv_radius = StringVar(self.root, value=str(29))
        self.sv_x_spacing = StringVar(self.root, value=str(60))
        self.sv_y_spacing = StringVar(self.root, value=str(44))
        self.sv_scorelabel = StringVar(self.root, value="Score: ")

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
        label_score = Label(top_frame, text='', textvariable=self.sv_scorelabel)

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
        label_score.grid(row=2, column=0, columnspan=9)

        # create & layout the canvas
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=1)

        r = int(self.sv_radius.get())
        x_offset = int(self.sv_x_spacing.get())
        y_offset = int(self.sv_y_spacing.get())

        self.canvas = Canvas(center, bg='white', height=((r+y_offset) * (BUTTON_ROWS + 2)), width=((r+x_offset) * (BUTTON_COLS + 2)))
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.redraw_outlines()

        # Start keyboard listener        
        def on_release(key):
            # Key may not always have char (...Why isn't it just set to None?)
            if hasattr(key, 'char'):
                key_val = key.char.upper()
                print(key_val, "released")
                if not self.ui_enabled:
                    self.keys_and_timings_mutex.acquire()
                    if key_val in self.keys_and_timings_to_track:
                        self.keys_and_timings_to_track[key_val] -= 1
                        if self.keys_and_timings_to_track[key_val] == 0:
                            del self.keys_and_timings_to_track[key_val]
                        self.score += 1
                    else:
                        self.false_notes += 1
                    self.update_score()
                    self.keys_and_timings_mutex.release()

        # Collect events until released
        listener = Listener(on_release=on_release)
        listener.start()

        # Setup the listener stop function by setting it to stop on window exit
        def on_closing():
            listener.stop()
            self.root.destroy()

        # Since we're using a 2nd thread for keypress detection, we'll need to handle the GUI closing fx
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

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
        self.songdata_idx = 0
        self.score = 0
        self.false_notes = 0
        self.scoreables = 0

    # Overriden method
    def play_char_note(self, c):
        if c in self.charmap:
            curr_x, curr_y = self.charmap[c]
            note_in_animation = (0, self.canvas.create_circle(curr_x, curr_y, 0, outline="red", width=2), c)
            self.notes_in_animation.append(note_in_animation)
    
    # Overriden method
    def delete_note(self, note):
        iterations, obj, c = note
        self.keys_and_timings_mutex.acquire()
        if c in self.keys_and_timings_to_track:
            if self.keys_and_timings_to_track[c] <= 0:
                del self.keys_and_timings_to_track[c]
            else:
                self.keys_and_timings_to_track[c] -= 1
        self.update_score()
        self.keys_and_timings_mutex.release()

    # Overriden method
    def animate_object(self, i, note_in_animation):
        # Get coords
        iterations, obj, c = note_in_animation
        x1, y1, x2, y2 = self.canvas.coords(obj)
        # Update using expansion rate
        self.canvas.coords(obj, 
            x1 - self.bbox_expansion_rate_per_frame, 
            y1 - self.bbox_expansion_rate_per_frame, 
            x2 + self.bbox_expansion_rate_per_frame, 
            y2 + self.bbox_expansion_rate_per_frame)
        self.notes_in_animation[i] = (iterations + 1, obj, c)
        if (ITERATIONS_UNTIL_ANIM_OVER - iterations == 10): # magic number here; 10 frame leeway; ~333ms
            self.keys_and_timings_mutex.acquire()
            if c in self.keys_and_timings_to_track:
                self.keys_and_timings_to_track[c] += 1
            else:
                self.keys_and_timings_to_track[c] = 1
            self.scoreables += 1
            self.keys_and_timings_mutex.release()
    
    # override
    def song_ended(self):
        final_score = (self.score - self.false_notes) / (self.scoreables * 1.0)
        print(final_score)
        venti_verdict = ""
        if final_score < 0.33:
            chars = ['Klee', 'Razor', 'Bennett', 'Mona']
            venti_verdict = (
                "Umm... You... Don't really have a sense of rhythm do you? Don't give up! "
                "Maybe I can ask {0} to coach you...\n\nRank: Musical Hobbyist"
            ).format(chars[random.randint(0,3)])
        elif final_score < 0.66:
            chars = ['Noelle', 'Lisa', 'Kaeya', 'Jean']
            venti_verdict = (
                "Not bad, not bad. You are almost as good as {0}. Keep up the good work!"
                "\n\nRank: Rising Star"
            ).format(chars[random.randint(0,3)])
        elif final_score < 0.99:
            chars = ['Albedo', 'Diluc', 'Barbara']
            venti_verdict = (
                "Wow, that must've taken a lot of practice... Or are you just talented?"
                "Would you mind playing a duet with {0} sometime? Haha..."
                "\n\nRank: Windblume Laureate"
            ).format(chars[random.randint(0,2)])
        else:
            venti_verdict = (
                "Incredible. That was perfect. I don't think I could've played much better myself!"
                "\n\nRank: Perfect, like Diluc's Dandelion Wine. Or Diona's Special. I can't decide which drink is better."
            )
        messagebox.showinfo("Venti listened to your song and gives his verdict", 
            (
                "Your score: {0}/{1} notes hit - {2} wrong notes played = {3}"
                "\n\nVenti Says:\n{4}"
            ).format(self.score, self.scoreables, self.false_notes, self.score - self.false_notes, venti_verdict)
        )

    def update_score(self):
        self.sv_scorelabel.set("Score: {0}/{1} notes hit - {2} wrong notes played = {3}".format(self.score, self.scoreables, self.false_notes, self.score - self.false_notes))

if __name__ == "__main__":
    my_application = OverlayApplication()
    # Run the app's main logic loop in a different thread
    #main_loop_thread = threading.Thread(target=app_keyboard_loop, args=(my_application, ))
    #main_loop_thread.daemon = True
    #main_loop_thread.start()
