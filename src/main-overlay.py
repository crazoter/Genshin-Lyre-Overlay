"""
    This program contains code adapted from: Lyre Midi Player (https://github.com/3096/genshin_scripts/blob/main/midi.py) 
    which is under the GNU General Public License.
"""

# Requirements: Python3, Tkinter, PIL
# install PIL using pip install pillow
import time
import json

from typing import List
from tkinter import *
from PIL import ImageTk, Image

# Resources:
# Making the window transparent in other OS
# https://stackoverflow.com/questions/19080499/transparent-background-in-a-tkinter-window
# Crash course into layouts for Tkinter
# https://stackoverflow.com/questions/34276663/tkinter-gui-layout-using-frames-and-grid

# Constants
BUTTON_ROWS = 3
BUTTON_COLS = 7
SECONDS_TO_START_ANIMATION = 2        # Number of seconds before we begin animating the circle
FPS = 30.0
ITERATIONS_UNTIL_ANIM_OVER = FPS * SECONDS_TO_START_ANIMATION
FRAME_RATE = 1000/FPS                # This will also affect the accuracy of your songs
DELAY_AFTER_PLAY_PRESSED = 2000

HELP_STRING = "Configure the circles to fit your notes by modifying the values in the textboxes (current values are for 1280x720). Then, input the correct filename & hit play :)"

KEYS = [['Q','W','E','R','T','Y','U'],
    ['A','S','D','F','G','H','J'],
    ['Z','X','C','V','B','N','M']]

# Contribution by Ghostlium
SKY_JSON_NOTE_MAP = {
  "1Key0": 'Z',# "A1"
  "1Key1": 'X',# "A2"
  "1Key2": 'C',# "A3"
  "1Key3": 'V',# "A4"
  "1Key4": 'B',# "A5"
  "1Key5": 'N',# "A6"
  "1Key6": 'M',# "A7"
  "1Key7": 'A',# "B1"
  "1Key8": 'S',# "B2"
  "1Key9": 'D',# "B3"
  "1Key10": 'F',# "B4"
  "1Key11": 'G',# "B5"
  "1Key12": 'H',# "B6"
  "1Key13": 'J',# "B7"
  "1Key14": 'Q'# "C1"
}

# Lifted from https://github.com/3096/genshin_scripts/blob/main/midi.py
# Used for auto root finding
LOWEST = 48
HIGHEST = 84
BOOL_USE_COUNT = True
class NoteKeyMap:
    KEY_STEPS = [
        (0, 'z'),
        (2, 'x'),
        (4, 'c'),
        (5, 'v'),
        (7, 'b'),
        (9, 'n'),
        (11, 'm'),
        (12, 'a'),
        (14, 's'),
        (16, 'd'),
        (17, 'f'),
        (19, 'g'),
        (21, 'h'),
        (23, 'j'),
        (24, 'q'),
        (26, 'w'),
        (28, 'e'),
        (29, 'r'),
        (31, 't'),
        (33, 'y'),
        (35, 'u')
    ]

    def __init__(self, root_note):
        self.map = {}
        for key_step in self.KEY_STEPS:
            self.map[root_note + key_step[0]] = key_step[1].upper()

    def get_key(self, note):
        return self.map.get(note)

# Helper functions
def radius_to_bounding_box(x, y, r):
    return (x-r, y-r, x+r, y+r)

def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
Canvas.create_circle = _create_circle

def _update_object(self, obj, x, y, r):
    return self.coords(obj, x-r, y-r, x+r, y+r)
Canvas.update_object = _update_object

class Application():
    def __init__(self):
        # Application variables

        # Song-related variables
        self.songcurrenttime = 0
        self.songduration = 0
        self.songname = ""
        self.songdata = []
        self.songdata_idx = 0
        # Each entry is (animationsLeft:Integer = BEATS_TO_START_ANIM, object on canvas)
        # When animationsLeft becomes 0, we remove the object from the canvas
        self.notes_in_animation = []
        # Precomputed value, we will add this expansion rate to expand the bounding box with every animation tick
        self.bbox_expansion_rate_per_frame = 0
        # Also another precomputed value
        self.charmap = {}

        # UI and config variables
        # Tkinter canvas tracks everything it draws as an object
        # This list stores the outlines of the keyboard
        self.keyboard_outline_objs = []
        self.root = Tk()
        # create the string values for the entries that invoke an event after being changed
        self.sv_filename = StringVar(self.root, value="music/sample.txt")
        self.sv_descriptlabel = StringVar(self.root, value=HELP_STRING)
        self.sv_radius = StringVar(self.root, value=str(29))
        self.sv_x_spacing = StringVar(self.root, value=str(60))
        self.sv_y_spacing = StringVar(self.root, value=str(44))
        # Elements that we will need access to
        self.canvas = None
        self.label_descriptlabel = None
        # Add misc entries and buttons so we can mass enable / disable
        self.inputObjects = []

        self.root.title('Teach me the lyre, Venti Sensei!')
        # Make the self.root window always on top
        self.root.wm_attributes("-topmost", True)
        # Convert white to transparent
        self.root.wm_attributes("-transparentcolor", "white")

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
        
        self.label_descriptlabel = Label(top_frame, text='Song Name', textvariable=self.sv_descriptlabel)

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
        self.label_descriptlabel.grid(row=1, column=0, columnspan=9)

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

    def disable_inputs(self):
        for obj in self.inputObjects:
            obj['state'] = 'disabled'

    def enable_inputs(self):
        for obj in self.inputObjects:
            obj['state'] = 'normal'

    def play_btn_press(self):
        # Disable inputs and pre_compute animation constants
        self.disable_inputs()
        # Now that user cannot change size of keyboard, set the bounding box expansion rate for animation
        self.set_bbox_expansion_rate_per_frame()
        self.set_charmap()
        self.songdata_idx = 1
        # here I assume the user inputs the correct filename
        if self.sv_filename.get().lower().endswith('.txt'):
            self.read_music_txt()
            self.root.after(DELAY_AFTER_PLAY_PRESSED, self.play_song_tick)
        elif self.sv_filename.get().lower().endswith('.json'):
            self.read_music_sky_json()
            self.root.after(DELAY_AFTER_PLAY_PRESSED, self.play_song_tick)
        elif self.sv_filename.get().lower().endswith('.txtmidi'):
            self.read_music_txtmidi()
            self.root.after(DELAY_AFTER_PLAY_PRESSED, self.play_song_tick)
        #elif self.sv_filename.get().lower().endswith('.midi'):
        #    print("not yet supported")
        else: # Nothing happened because we don't support any of the file formats
            print("File format not supported")
            self.enable_inputs()
            self.sv_descriptlabel.set(HELP_STRING)

    def read_music_txt(self):
        # Read in file
        print("Reading TXT")
        with open(self.sv_filename.get()) as file:
            self.songdata = file.readlines() 
            self.songname = "Now playing: " + self.songdata[0] # I expect the first line in the file to be the name of the song
            self.songduration = DELAY_AFTER_PLAY_PRESSED / 1000 + SECONDS_TO_START_ANIMATION

            # For every subsequent line, 
            # I expect the buttons to be pressed (no spaces), and the duration (in milliseconds) to the next series of buttons to be pressed.
            # These two things have to be separated by a space.
            # e.g. "QWAD 120" means the program will signal you to press QWAD at the same time for this iteration, and wait 120ms before it plays the next line.

            for i in range(len(self.songdata)):
                if i == 0:
                    continue
                # [Keys,ms to next]
                self.songdata[i] = self.songdata[i].split(' ')
                self.songdata[i][0] = self.songdata[i][0].upper()
                self.songdata[i][1] = float(self.songdata[i][1])
                self.songduration += self.songdata[i][1]

            # Calculate formatted song duration
            seconds = (self.songduration/1000)%60
            seconds = int(seconds)
            minutes = (self.songduration/(1000*60))
            minutes = int(minutes)
            self.songduration = "%d:%d" % (minutes, seconds)
            self.sv_descriptlabel.set(self.songname.replace('\n',''))

            for i in self.songdata:
                print(i)

    def read_music_sky_json(self):
        print("Reading JSON")
        with open(self.sv_filename.get()) as file:
            data = json.load(file)[0]
            # Assume that songdata is not without notes
            self.songname = "Now playing: " + data['name']
            self.sv_descriptlabel.set(self.songname.replace('\n',''))
            self.songdata.clear()
            idx = 0
            current_frame = -1
            for pair in data['songNotes']:
                # First note, just add without binning yet
                if current_frame == -1:
                    self.songdata.append([SKY_JSON_NOTE_MAP[pair['key']], 0])
                    current_frame = int(data['songNotes'][0]['time'] / FRAME_RATE)
                else:
                    frame = int(pair['time'] / FRAME_RATE)
                    # Same frame, append the note to the previous group because they will visually appear at the same time
                    if (frame == current_frame):
                        self.songdata[idx][0] += SKY_JSON_NOTE_MAP[pair['key']]
                    else:
                        # Play this note x frames from the current_frame
                        self.songdata[idx][1] = float((frame - current_frame) * FRAME_RATE)
                        # Add the next note to play x frames from now
                        self.songdata.append([SKY_JSON_NOTE_MAP[pair['key']], 0])
                        current_frame = frame
                        idx += 1

            for i in self.songdata:
                print(i)

    def read_music_txtmidi(self):
        print("Reading TXTMIDI")
        with open(self.sv_filename.get()) as file:
            songdata_tmp = file.readlines() 
            note_count = {}
            for i in range(len(songdata_tmp)):
                songdata_tmp[i] = songdata_tmp[i].split(' ')
                songdata_tmp[i] = [int(songdata_tmp[i][0]), int(songdata_tmp[i][1])]
                # collect notes
                if songdata_tmp[i][0] in note_count:
                    note_count[songdata_tmp[i][0]] += 1
                else:
                    note_count[songdata_tmp[i][0]] = 1

            # count notes
            notes = sorted(note_count.keys())
            print(len(notes))
            best_key_map = None
            best_root = None
            best_hits = -1
            total = 0
            for cur_root in range(max(notes[0] - 24, 0), min(notes[-1] + 25, 128)):
                cur_key_map = NoteKeyMap(cur_root)
                cur_note_hits = 0
                cur_total = 0
                for note, count in note_count.items():
                    if LOWEST <= note < HIGHEST:
                        if cur_key_map.get_key(note):
                            cur_note_hits += count if BOOL_USE_COUNT else 1
                        cur_total += count if BOOL_USE_COUNT else 1

                if cur_note_hits > best_hits:
                    best_hits = cur_note_hits
                    total = cur_total
                    best_key_map = cur_key_map
                    best_root = cur_root

            print(f"auto root found root at {best_root} with {best_hits}/{total} ({best_hits / total})")
            
            self.songdata.clear()
            idx = 0
            current_frame = -1
            # 0: key, 1: time
            for pair in songdata_tmp:
                # First note, just add without binning yet
                if current_frame == -1:
                    self.songdata.append([best_key_map.get_key(pair[0]), 0])
                    current_frame = int(songdata_tmp[0][1] / FRAME_RATE)
                else:
                    frame = int(pair[1] / FRAME_RATE)
                    # Same frame, append the note to the previous group because they will visually appear at the same time
                    if (frame == current_frame):
                        key = best_key_map.get_key(pair[0])
                        if (key != None):
                            self.songdata[idx][0] += key
                    else:
                        # Play this note x frames from the current_frame
                        self.songdata[idx][1] = float((frame - current_frame) * FRAME_RATE)
                        # Add the next note to play x frames from now
                        key = best_key_map.get_key(pair[0])
                        if (key != None):
                            self.songdata.append([key, 0])
                            current_frame = frame
                            idx += 1

            for i in self.songdata:
                print(i)

    def play_song_tick(self):
        # We've not played the first note, so start playing it
        if self.songdata_idx == 1:
            self.play_notes(self.songdata[self.songdata_idx][0])
            self.songdata_idx += 1
        else:
            # On the current note we are on, wait until the appropriate time, then play the note (based on our frame rate)
            # I'm a little lazy to do the time delta stuff, leave that to version 2.0 or something lmao
            if self.songdata_idx < len(self.songdata):
                self.songdata[self.songdata_idx][1] -= FRAME_RATE
                if self.songdata[self.songdata_idx][1] <= 0:
                    self.play_notes(self.songdata[self.songdata_idx][0])
                    self.songdata_idx += 1

        # If there are still more notes to animate
        if len(self.notes_in_animation) > 0 or self.songdata_idx < len(self.songdata):
            if len(self.notes_in_animation) > 0:
                self.animate_notes()

            # Update time?
            self.root.after(int(FRAME_RATE), self.play_song_tick)
        else:
            self.enable_inputs()
            self.sv_descriptlabel.set(HELP_STRING)

    def play_notes(self, note_string):
        # Add notes to the animation list
        for c in note_string:
            if c in self.charmap:
                curr_x, curr_y = self.charmap[c]
                self.notes_in_animation.append((0, self.canvas.create_circle(curr_x, curr_y, 0, outline="blue", width=2)))
    
    def animate_notes(self):
        i = 0
        while i < len(self.notes_in_animation): 
            iterations, obj = self.notes_in_animation[i]
            # Animation is over
            if (iterations > ITERATIONS_UNTIL_ANIM_OVER):
                self.canvas.delete(self.notes_in_animation[i][1])
                self.notes_in_animation.pop(i)
            else:
                # Get coords
                x1, y1, x2, y2 = self.canvas.coords(obj)
                # Update using expansion rate
                self.canvas.coords(obj, 
                    x1 - self.bbox_expansion_rate_per_frame, 
                    y1 - self.bbox_expansion_rate_per_frame, 
                    x2 + self.bbox_expansion_rate_per_frame, 
                    y2 + self.bbox_expansion_rate_per_frame)
                self.notes_in_animation[i] = (iterations + 1, obj)
                # Step to next object to animate
                i += 1

if __name__ == "__main__":
    my_application = Application()