# Requirements: python3, numpy, opencv, mss, tkinter

import time
import numpy as np
import cv2
import random
from multiprocessing import Process, Lock
import mss
import threading

import importlib
main_overlay = importlib.import_module("main-overlay")

from tkinter import *
from tkinter import scrolledtext, messagebox

HUE_80_90_THRESHOLD = 0.3

KEYS = [['Q','W','E','R','T','Y','U'],
    ['A','S','D','F','G','H','J'],
    ['Z','X','C','V','B','N','M']]

LEFT_HAND_KEY_LIST = {
    'Q','W','E',
    'A','S','D',
    'Z','X','C'
}

KEY_LIST = [ 'Z', 'X', 'C', 'A', 'S', 'D', 'Q', 'W', 'E', 'V', 'B', 'N', 'M', 'F', 'G', 'H', 'J', 'R', 'T', 'Y', 'U' ]
KEY_IDX_MAP = {}
for i in range(len(KEY_LIST)):
    KEY_IDX_MAP[KEY_LIST[i]] = i

key_state = {'Q': False,'W': False,'E': False,'R': False,'T': False,'Y': False,'U': False,
'A': False,'S': False,'D': False,'F': False,'G': False,'H': False,'J': False,'Z': False,
'X': False,'C': False,'V': False,'B': False,'N': False,'M': False}

def mssthread(app):
    # Main logic loop
    with mss.mss() as sct:
        monitor = app.get_monitor()
        while app.run_mssthread:
            # Get raw pixels from the screen, save it to a Numpy array
            img = np.array(sct.grab(monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # For now we'll not be using S,V
            img = np.delete(img, [1,2], 1)
            for i in app.key_positions:
                crop = img[i[2] : i[3], i[0] : i[1]]
                # Detect by thresholding to detect that greenish tint
                # If this doesn't work well, then we'd need to detect by colour delta 
                green_count = np.count_nonzero((80 < crop) & (crop < 90))
                pixel_count = crop.shape[0] * crop.shape[1] # * crop.shape[2]

                if green_count / pixel_count > HUE_80_90_THRESHOLD:
                    # Key was pressed
                    if not key_state[i[4]]:
                        key_val = i[4]
                        app.keys_and_timings_mutex.acquire()
                        if key_val in app.keys_and_timings_to_track:
                            app.keys_and_timings_to_track[key_val] -= 1
                            if app.keys_and_timings_to_track[key_val] == 0:
                                del app.keys_and_timings_to_track[key_val]
                            app.score += 1
                        else:
                            app.false_notes += 1
                        app.update_score()
                        app.keys_and_timings_mutex.release()
                    key_state[i[4]] = True

                else:
                    key_state[i[4]] = False

# https://stackoverflow.com/questions/44865023/how-can-i-create-a-circular-mask-for-a-numpy-array
# Not used, but could be useful for removing extra stuff outside of the circle
def create_circular_mask(h, w, center=None, radius=None):

    if center is None: # use the middle of the image
        center = (int(w/2), int(h/2))
    if radius is None: # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w-center[0], h-center[1])

    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)

    mask = dist_from_center <= radius
    return mask

# Helper functions
def current_milli_time():
    return int(time.time() * 1000)

def append_txt(text, value):
    # Trim last character which is always \n
    value = text.get("1.0",END)[:-1] + value
    text.delete(1.0, END)
    text.insert(END, value)

class KeyRecordApplication(main_overlay.OverlayApplication):
    def __init__(self):
        super().__init__()

        self.keys_and_timings_to_track = {}
        self.keys_and_timings_mutex = Lock()
        self.score = 0
        self.scoreables = 0
        self.false_notes = 0

        # https://stackoverflow.com/questions/12364981/how-to-delete-tkinter-widgets-from-a-window

        self.iv_isgame = IntVar(value=0)
        c1 = Checkbutton(self.top_frame, text='Enable Game',variable=self.iv_isgame, onvalue=1, offvalue=0,fg='red')
        c1.grid(row=2, column=0, columnspan=2)
        self.inputObjects.append(c1)

        self.iv_animatecircles = IntVar(value=1)
        c2 = Checkbutton(self.top_frame, text='Animate Circles',variable=self.iv_animatecircles, onvalue=1, offvalue=0,fg='red')
        c2.grid(row=2, column=2, columnspan=2)
        self.inputObjects.append(c2)

        self.iv_showkeyboard = IntVar(value=0)
        c3 = Checkbutton(self.top_frame, text='Animate Keyboard',variable=self.iv_showkeyboard, onvalue=1, offvalue=0,fg='red')
        c3.grid(row=2, column=4, columnspan=2)
        self.inputObjects.append(c3)
        
        self.sv_scorelabel = StringVar(self.root, value="Score: ")
        label_score = Label(self.top_frame, text='', textvariable=self.sv_scorelabel)
        label_score.grid(row=2, column=6, columnspan=8)

        # Redraw outlines without labels
        self.redraw_outlines(self.iv_animatecircles.get() == 1)
        # run event loop until window appears
        self.root.wait_visibility()
        # Perform this action, as sct will cause modifications to the size of the screen on start-up
        with mss.mss() as sct:
            pass
        self.run_mssthread = False
        print(self.get_monitor())

        # Keyboard UI
        self.KB_SECONDS_TO_START_ANIMATION = 10        # Number of seconds before we begin animating the circle
        self.KB_ITERATIONS_UNTIL_ANIM_OVER = self.FPS * self.KB_SECONDS_TO_START_ANIMATION
        self.CIRCLE_WAIT_ITERS_TO_SYNC = self.KB_ITERATIONS_UNTIL_ANIM_OVER - self.ITERATIONS_UNTIL_ANIM_OVER
        self.KB_BAR_HEIGHT = 200
        self.KB_NOTE_HEIGHT = 10
        self.KB_HEIGHT = 300
        self.KB_DROP_RATE = self.KB_BAR_HEIGHT / self.KB_ITERATIONS_UNTIL_ANIM_OVER
        # this is a pretty funny hack
        self.KB_ANIM_START_VAL = self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ITERATIONS_UNTIL_ANIM_OVER
        # Draw keyboard
        # create & layout the canvas
        self.kb_canvas = Canvas(self.center, bg='black', height=self.KB_HEIGHT, width=900)
        self.kb_canvas.grid(row=2, column=1, sticky="nsew")
        self.kb_canvas.create_text(10, self.KB_BAR_HEIGHT + 30, fill='yellow', font="Times 8 bold", text='1')
        self.kb_canvas.create_text(10, self.KB_BAR_HEIGHT + 40, fill='yellow', font="Times 8 bold", text='2')
        self.kb_canvas.create_text(10, self.KB_BAR_HEIGHT + 50, fill='yellow', font="Times 8 bold", text='3')

        # Draw buttons and grid
        for i in range(self.BUTTON_COLS * self.BUTTON_ROWS):
            offset = 40 + i * 40
            key = KEY_LIST[i].upper()
            colour = "#f00"
            if key in LEFT_HAND_KEY_LIST:
                colour = "light blue"

            height_offset = self.KB_BAR_HEIGHT + 30
            if key in KEYS[1]:
                height_offset = self.KB_BAR_HEIGHT + 40
            elif key in KEYS[2]:
                height_offset = self.KB_BAR_HEIGHT + 50
            self.kb_canvas.create_rectangle(offset, self.KB_BAR_HEIGHT, offset + 20, self.KB_BAR_HEIGHT + self.KB_NOTE_HEIGHT, outline="gray", fill="gray")
            self.kb_canvas.create_text(offset + 12, height_offset, fill=colour, font="Times 11 bold", text=key)

    def reformat_outlines_callback(self, sv):
        if (sv.get().isdigit()):
            # Redraw outlines without labels
            self.redraw_outlines(self.iv_animatecircles.get() == 1)
            return True
        return False

    # Overriden method
    def post_play_press_pre_data_parse(self):
        self.set_bbox_expansion_rate_per_frame()
        self.set_charmap()
        self.redraw_outlines(self.iv_animatecircles.get() == 1)
        self.songdata_idx = 0
        if self.iv_isgame.get() == 1:
            self.score = 0
            self.false_notes = 0
            self.scoreables = 0
            self.update_score()
            self.screen_prep()
            self.run_mssthread = True
            main_loop_thread = threading.Thread(target=mssthread, args=(self, ))
            main_loop_thread.daemon = True
            main_loop_thread.start()

    # Overriden method
    def play_char_note(self, c):
        if c in self.charmap:
            # We will always add a note so that the game mode will have something to listen for
            # even if nothing is being drawn
            timing = 0
            # we need to sync the circle animation, so make it wait for the keyboard
            if self.iv_showkeyboard.get() == 1:
                timing = -self.CIRCLE_WAIT_ITERS_TO_SYNC
            note_in_animation = [timing, None, 0, c]
            if self.iv_animatecircles.get() == 1:
                curr_x, curr_y = self.charmap[c]
                note_in_animation[1] = self.canvas.create_circle(curr_x, curr_y, 0, outline="red", width=2)
            self.notes_in_animation.append(note_in_animation)

        if self.iv_showkeyboard.get() == 1:
            if c in KEY_IDX_MAP:
                curr_x = 40 + KEY_IDX_MAP[c] * 40
                colour = "#f00"
                # textcolor = "black"
                if c in LEFT_HAND_KEY_LIST:
                    colour = "light blue"
                    # textcolor = "black"
                self.notes_in_animation.append(
                    (self.KB_ANIM_START_VAL, self.kb_canvas.create_rectangle(curr_x, 0, curr_x + 20, 14, outline='black', fill=colour), 1, c)
                )
                self.notes_in_animation.append(
                    (self.KB_ANIM_START_VAL, self.kb_canvas.create_text(curr_x + 10, 6, fill='black', font="Times 8 bold", text=c), 1, c)
                )
    
    # Overriden method
    def on_delete_note(self, note):
        if self.iv_isgame.get() == 0:
            return

        iterations, obj, is_keyboard_note, c = note
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
        iterations, obj, is_keyboard_note, c = note_in_animation

        # Get coords; 
        if not is_keyboard_note:
            if self.iv_animatecircles.get() == 1 and iterations >= 0:
                # if iterations is negative, then it's waiting for the keyboard notes
                x1, y1, x2, y2 = self.canvas.coords(obj)
                # Update using expansion rate
                self.canvas.coords(obj, 
                    x1 - self.bbox_expansion_rate_per_frame, 
                    y1 - self.bbox_expansion_rate_per_frame, 
                    x2 + self.bbox_expansion_rate_per_frame, 
                    y2 + self.bbox_expansion_rate_per_frame)

            # There will always be one non keyboard note even if circles are not animated
            if self.iv_isgame.get() == 1:
                if (self.ITERATIONS_UNTIL_ANIM_OVER - iterations == 10): # magic number here; 10 frame leeway; ~333ms
                    self.keys_and_timings_mutex.acquire()
                    if c in self.keys_and_timings_to_track:
                        self.keys_and_timings_to_track[c] += 1
                    else:
                        self.keys_and_timings_to_track[c] = 1
                    self.scoreables += 1
                    self.keys_and_timings_mutex.release()
        
        if is_keyboard_note and self.iv_showkeyboard.get() == 1:
                # Get coords
                coords = self.kb_canvas.coords(obj)
                if len(coords) == 4:
                    # Boxes have 4 coordinates
                    x1, y1, x2, y2 = coords
                    # Update using expansion rate
                    self.kb_canvas.coords(obj, 
                        x1, y1 + self.KB_DROP_RATE, 
                        x2, y2 + self.KB_DROP_RATE)
                else:
                    # Text only have 2 coordinates
                    x, y = coords
                    # Update using expansion rate
                    self.kb_canvas.coords(obj, x, y + self.KB_DROP_RATE)


        self.notes_in_animation[i] = (iterations + 1, obj, is_keyboard_note, c)
    
    # override
    def song_ended(self):
        if self.iv_isgame.get() == 0:
            return

        self.run_mssthread = False
        final_score = (self.score - 0.5 * (self.false_notes)) / (self.scoreables * 1.0)
        print(final_score)
        venti_verdict = ""
        stars = "☆☆☆"
        if final_score < 0.33:
            stars = "★☆☆"
            chars = ['Klee', 'Razor', 'Bennett', 'Mona']
            venti_verdict = (
                "Umm... You... Don't really have a sense of rhythm do you? Don't give up! "
                "Maybe I can ask {0} to coach you...\n\nRank: Musical Hobbyist"
            ).format(chars[random.randint(0,3)])
        elif final_score < 0.66:
            stars = "★★☆"
            chars = ['Noelle', 'Lisa', 'Kaeya', 'Jean']
            venti_verdict = (
                "Not bad, not bad. You are almost as good as {0}. Keep practicing!"
                "\n\nRank: Rising Star"
            ).format(chars[random.randint(0,3)])
        elif final_score < 0.99:
            stars = "★★★"
            chars = ['me', 'Albedo', 'Diluc', 'Barbara']
            venti_verdict = (
                "Wow, that must've taken a lot of practice... Or are you just talented?"
                "Would you mind playing a duet with {0} sometime? Haha..."
                "\n\nRank: Windblume Laureate"
            ).format(chars[random.randint(0,3)])
        else:
            stars = "★PERFECT★"
            venti_verdict = (
                "Incredible. That was perfect. I don't think I could've played much better myself!"
                "\n\nRank: Perfect, like Diluc's Dandelion Wine. Or Diona's Special. Hm, I can't decide which drink is better."
            )
        final_score = self.score - 0.5 * (self.false_notes)
        messagebox.showinfo("Venti listened to your song and gives his verdict", 
            (
                "Score: {0} ({1})"
                "\n\n{2}"
            ).format(stars, final_score, venti_verdict)
        )

    def update_score(self):
        self.sv_scorelabel.set("Score: {0}/{1} notes hit - 1/2 * {2} wrong notes played = {3}".format(self.score, self.scoreables, self.false_notes, self.score - 0.5 * (self.false_notes)))


    def on_closing(self, call_root_destroy):
        print("key-recorder closing")
        self.run_mssthread = False
        super().on_closing(False)
        
        if call_root_destroy:
            self.root.destroy()
    
    # Note: the code doesn't account for the fact that the screen may be out of bounds.
    def get_monitor(self):
        self.root.update()
        # print("y", self.canvas.winfo_rooty(), self.top_frame.winfo_rooty())
        return {
            "left": self.canvas.winfo_rootx(),
            "top": self.canvas.winfo_rooty(),
            "width": self.canvas.winfo_width(),
            "height": self.canvas.winfo_height()
        }

    def screen_prep(self):
        # (left_incl, right_excl, top_incl, btm_excl)
        self.key_positions = []

        r = int(self.sv_radius.get()) # deduct the width of the circle outline
        x_offset = int(self.sv_x_spacing.get())
        y_offset = int(self.sv_y_spacing.get())

        curr_x = r + x_offset
        curr_y = r + y_offset
        
        for k in range(3):
            for j in range(7):        
                # -3 to remove the circle outline
                self.key_positions.append((curr_x - (r - 3), curr_x + r - 3, curr_y - (r - 3), curr_y + r - 3, KEYS[k][j]))
                curr_x += r + x_offset
            curr_x = r + x_offset
            curr_y += r + y_offset
 
if __name__ == "__main__":
    my_application = KeyRecordApplication()
    my_application.start()
