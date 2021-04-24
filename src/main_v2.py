# Requirements: python3, numpy, opencv, mss, tkinter

import time
import numpy as np
import cv2
import random
from multiprocessing import Process, Lock
import mss
import threading
# import matplotlib.pyplot as plt

import main_overlay

from tkinter import *
from tkinter import scrolledtext, messagebox
from tkinter import font as tkfont

# If you want to enable macro, need to run in admin mode
from pynput.keyboard import Key, Controller


HUE_80_90_THRESHOLD = 0.3

KEYS = [['Q','W','E','R','T','Y','U'],
    ['A','S','D','F','G','H','J'],
    ['Z','X','C','V','B','N','M']]

LEFT_HAND_KEY_LIST = {
    'Q','W','E',
    'A','S','D',
    'Z','X','C'
}
KEY_LIST = [ 'U', 'Y', 'T', 'R', 'E', 'W', 'Q', 'J', 'H', 'G', 'F', 'D', 'S', 'A', 'M', 'N', 'B', 'V', 'C', 'X', 'Z' ]

# Primary Color, Dark Color, Highlighted Color
KEY_COLOR_LIST = [('#B00', '#800', '#F00'), ('#0B0', '#080', '#0F0'), ('#00B', '#008', '#00F')]

KEY_INFO_MAP = {}
# Index, 
for i in range(len(KEY_LIST)):
    KEY_INFO_MAP[KEY_LIST[i]] = (i, KEY_COLOR_LIST[i // 7])

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
            # plt.imshow(img)
            # plt.show()

            # For now we'll not be using S,V
            img = np.delete(img, [1,2], 1)
            # print(time.time())
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
                        print("msst ACQ", time.time())
                        app.keys_and_timings_mutex.acquire()
                        print("msst", key_val, app.keys_and_timings_to_track, app.false_notes)
                        success = key_val in app.keys_and_timings_to_track and app.keys_and_timings_to_track[key_val] > 0
                        if success:
                            app.keys_and_timings_to_track[key_val] -= 1
                            app.score += 1
                        else:
                            app.false_notes += 1
                        print("msst uscore", time.time())
                        # app.update_score()
                        print("msst EXIT", time.time())
                        app.keys_and_timings_mutex.release()
                        print("msst REL", time.time())
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
        self.MIN_HEIGHT_PER_KEY = 2
        self.SCROLL_TEXT_HEIGHT = 20
        super().__init__()
        # self.keyboard = Controller()
        self.root.wm_attributes("-alpha", "0.8")

        print("Starting the application (this could take some time)")

        self.keys_and_timings_to_track = {}
        self.keys_and_timings_mutex = Lock()
        self.score = 0
        self.scoreables = 0
        self.false_notes = 0

        # https://stackoverflow.com/questions/12364981/how-to-delete-tkinter-widgets-from-a-window

        self.iv_isgame = IntVar(value=1)
        c1 = Checkbutton(self.top_frame, text='Enable Game',variable=self.iv_isgame, onvalue=1, offvalue=0,fg='red')
        c1.grid(row=2, column=0, columnspan=2)
        self.inputObjects.append(c1)

        self.iv_animatecircles = IntVar(value=0)
        c2 = Checkbutton(self.top_frame, text='Animate Circles (Laggy)',variable=self.iv_animatecircles, onvalue=1, offvalue=0,fg='red')
        c2.grid(row=2, column=2, columnspan=2)
        self.inputObjects.append(c2)

        self.iv_showkeyboard = IntVar(value=1)
        c3 = Checkbutton(self.top_frame, text='Animate Keyboard (Laggy)',variable=self.iv_showkeyboard, onvalue=1, offvalue=0,fg='red')
        c3.grid(row=2, column=4, columnspan=2)
        self.inputObjects.append(c3)

        self.iv_macro = IntVar(value=0)
        c3 = Checkbutton(self.top_frame, text='Enable Macro (Run program as admin)',variable=self.iv_macro, onvalue=1, offvalue=0,fg='red')
        c3.grid(row=2, column=6, columnspan=2)
        self.inputObjects.append(c3)
        
        # self.sv_scorelabel = StringVar(self.root, value="Score: ")
        self.label_score = Label(self.top_frame, text='')
        self.label_score.grid(row=2, column=8, columnspan=8)

        # run event loop until window appears
        self.root.wait_visibility()
        # Perform this action, as sct will cause modifications to the size of the screen on start-up
        print("Preparing MSS")
        with mss.mss() as sct:
            pass
        self.run_mssthread = False
        print(self.get_monitor())

        # GAME
        self.START_KEYPRESS_CHECKITER = 30 # ~1s

        # Keyboard UI
        self.KB_SECONDS_TO_START_ANIMATION = 10        # Number of seconds before we begin animating the circle
        self.KB_ITERATIONS_UNTIL_ANIM_OVER = self.FPS * self.KB_SECONDS_TO_START_ANIMATION
        self.CIRCLE_WAIT_ITERS_TO_SYNC = self.KB_ITERATIONS_UNTIL_ANIM_OVER - self.ITERATIONS_UNTIL_ANIM_OVER
    
        # this is a pretty funny hack
        # basically every tick will increment the iteration value from 0 to ITER_UNTIL_ANIM_OVER, then remove it when it reaches
        # This sets the value to negative so that it will animate properly (the base ITER_UNTIL_ANIM_OVER is for circles)
        self.KB_ANIM_START_VAL = self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ITERATIONS_UNTIL_ANIM_OVER
        # This is for the notes at the side
        self.kb_sidenote_offset = (self.songdata_idx, 0)
        # Draw keyboard
        self.canvas_width = 0 # To be set during redraw_outline        
        self.kb_sidenote_printedto_idx = 0
        self.KB_CHANGING_NOTE_LENGTH = 255
        self.KB_CHANGINGNOTE_QUANT = 1
        self.kb_changingnote_txt = ""
        self.kb_changingnote_idx = 0
        self.kb_changingnote_tick = 0
        self.kb_changingnote_notearr = [] # This will be used to hold (startIdx, endIdx) pairs for every note in the string
        self.kb_changingnote_notearr_idx = 0
        self.height_per_key = 0
        self.note_height = 0 # Set in redraw
        self.note_width = 20

        # Redraw outlines without labels
        self.redraw_outlines(self.iv_animatecircles.get() == 1)

    def redraw_outlines(self, draw_circles = True, draw_keyboard = True):
        super().redraw_outlines(draw_circles)
        # Draw keys
        if draw_keyboard is False:
            return
        if not self.sv_y_offset.get().isdigit() or not self.sv_radius.get().isdigit():
            return

        self.SCROLL_TEXT_HEIGHT = 20
        space_for_keyboard = float(self.sv_y_offset.get()) - float(self.sv_radius.get()) - self.SCROLL_TEXT_HEIGHT
        self.height_per_key = space_for_keyboard / (3 * 7)
        self.note_height = self.height_per_key - 2
        # Draw iff there's enough space
        if self.height_per_key <= self.MIN_HEIGHT_PER_KEY:
            return
        # Draw buttons and grid
        text_width = 20
        text_padding = 4
        self.canvas_width = self.canvas.winfo_width()
        # Add scrolling text
        # https://stackoverflow.com/questions/29368737/how-to-color-a-substring-in-tkinter-canvas
        self.my_font = tkfont.Font(family="Sans Serif", size=14)
        self.scrolling_text_bg = self.canvas.create_rectangle(0, 0, self.canvas_width, self.SCROLL_TEXT_HEIGHT, outline="black", fill="black")
        self.t2 = self.canvas.create_text(0, self.SCROLL_TEXT_HEIGHT / 2, text='', anchor='w', font=self.my_font, fill='yellow')
        self.t3 = self.canvas.create_text(0, self.SCROLL_TEXT_HEIGHT / 2, text='', anchor='w', font=self.my_font, fill='orange')

        # Add keys
        for i in range(self.BUTTON_COLS * self.BUTTON_ROWS):
            offset = self.SCROLL_TEXT_HEIGHT + i * self.height_per_key
            key = KEY_LIST[i].upper()
            colorset = KEY_COLOR_LIST[i // 7]
            fill = colorset[2]
            # print(offset, text_width, self.height_per_key)
            self.canvas.create_rectangle(0, offset, text_width, offset + self.note_height, outline="black", fill="black")
            self.canvas.create_text(text_width / 2, offset + self.height_per_key / 2 - 1, fill=fill, font="Serif 11 bold", text=key)

    def update_scrolling_text(self, newtext):
        # Todo: use self.kb_changingnote_notearr_idx to update the idx instead
        idx = 0
        counter = self.START_KEYPRESS_CHECKITER
        while counter > 0 and idx < len(newtext):
            if newtext[idx] == '.':
                counter -= 1
                idx += 1
            elif newtext[idx] == '(' or newtext[idx] == '{':
                counter += 1
                idx += 1
            else:
                idx += 1

        front = newtext[:idx]
        back = newtext[idx + 1:]
        self.canvas.itemconfigure(self.t2, text=front)
        self.canvas.itemconfigure(self.t3, text=back)
        self.canvas.coords(self.t3, self.my_font.measure(front), self.SCROLL_TEXT_HEIGHT / 2)

        # self.root.after(100, lambda: new_word(i+1))

    def reformat_outlines_callback(self, sv):
        if (sv.get().isdigit()):
            # Redraw outlines without labels
            self.redraw_outlines(self.iv_animatecircles.get() == 1)
            return True
        return False

    # Overriden method
    def post_play_press_pre_data_parse(self):
        self.root.resizable(width=False, height=False)
        self.set_bbox_expansion_rate_per_frame()
        self.set_charmap()
        self.redraw_outlines(self.iv_animatecircles.get() == 1)
        if self.height_per_key <= self.MIN_HEIGHT_PER_KEY:
            self.iv_showkeyboard.set(0)
        self.songdata_idx = 0
        self.kb_sidenote_printedto_idx = 0
        self.kb_changingnote_txt = "." * (int(self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ANIM_START_VAL) // self.KB_CHANGINGNOTE_QUANT)
        self.KB_DROP_RATE = self.canvas_width / self.KB_ITERATIONS_UNTIL_ANIM_OVER
        self.kb_changingnote_notearr = []
        self.kb_changingnote_notearr_idx = 0
        print(self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ANIM_START_VAL)
        self.kb_changingnote_idx = 0
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
    
    def post_data_parse(self):
        for row in self.songdata:
            # naive but simple solution
            counts = 0
            time_count = row[1]
            val = "".join(sorted(row[0]))
            while time_count > 0:
                time_count -= self.MS_PER_FRAME
                counts += 1
            # The plan is to strategically identify which notes can stretched over future '.'s so as to reduce the jittery effect
            note_str_len = len("{" + val + ")")
            if counts > note_str_len + 1:
                self.kb_changingnote_notearr.append((len(self.kb_changingnote_txt), len(self.kb_changingnote_txt) + note_str_len))
                self.kb_changingnote_txt += "{" + val + ")"
                self.kb_changingnote_txt += '.' * max(0, (counts - 1 + 1 - note_str_len) // self.KB_CHANGINGNOTE_QUANT)
            else:
                self.kb_changingnote_txt += "(" + val + ")"
                self.kb_changingnote_txt += '.' * max(0, (counts - 1) // self.KB_CHANGINGNOTE_QUANT)

        # Try to make it smoother by making it occupy some spaces behind instead
        self.update_scrolling_text(self.kb_changingnote_txt[0:self.KB_CHANGING_NOTE_LENGTH])

        # add a placeholder element if we are not showing the keyboard for event handling
        if (self.iv_showkeyboard.get() == 0):
            note_in_animation = [30-len(self.kb_changingnote_txt), None, 2, '']
            self.notes_in_animation.append(note_in_animation)

        # Print song name
        songname_height = self.canvas.winfo_height() / 2
        self.notes_in_animation.append(
            (self.ITERATIONS_UNTIL_ANIM_OVER, self.canvas.create_rectangle(0, songname_height - 20, self.canvas_width, songname_height + 20, fill="black"), 1, '')
        )
        self.notes_in_animation.append(
            (self.ITERATIONS_UNTIL_ANIM_OVER, self.canvas.create_text(self.canvas_width / 2, songname_height + 10, fill='#EEE', font="Serif 11 bold", text=self.songname), 1, '')
        )


    # Overriden method
    def play_notes(self, note_string):
        # Add notes to the animation list
        for c in note_string:
            self.play_char_note(c)
        # Conditionally play sidenote; merge lines according to how much space we have
        # record the songidx that we merged until, so that we can compare later on and repeat
        """
        if self.iv_showkeyboard.get() == 1:
            if self.songdata_idx == self.kb_sidenote_printedto_idx:
                print(self.songdata_idx, self.kb_sidenote_printedto_idx)
                txt = "({0})".format(note_string)
                ms_until_next = 1000
                while self.kb_sidenote_printedto_idx < len(self.songdata) - 1:
                    diff = ms_until_next - max(0, self.songdata[self.kb_sidenote_printedto_idx][1])
                    # exceeded limit
                    if diff < 0:
                        break
                    else:
                        self.kb_sidenote_printedto_idx += 1
                        ms_until_next -= diff
                    txt += "{0}({1})".format('-'*int(diff/200), self.songdata[self.kb_sidenote_printedto_idx][0])
                self.kb_sidenote_printedto_idx += 1
                    
                self.notes_in_animation.append(
                    # Magic hardcoded value
                    # - an extra 30 to make sure it still persists while the remaining  notes are playing
                    (self.KB_ANIM_START_VAL - 30, self.canvas.create_text(22 * 40, 6, fill='yellow', font="Times 8 bold", text=txt, anchor=W), 1, txt)
                )
        """

    # Override; this is called per tick
    def animate_notes(self):
        super().animate_notes()

        if self.kb_changingnote_tick < self.KB_CHANGINGNOTE_QUANT - 1:
            self.kb_changingnote_tick += 1
        else:
            self.kb_changingnote_tick = 0
            # Animate "scrolling" text
            # Skip bracket if necessary
            if self.kb_changingnote_idx < len(self.kb_changingnote_txt):
                if self.kb_changingnote_txt[self.kb_changingnote_idx] != '(':
                    self.kb_changingnote_idx += 1
                else:
                    # Only skip the contents of 1 bracket at a time
                    while (self.kb_changingnote_idx < len(self.kb_changingnote_txt) 
                        and self.kb_changingnote_txt[self.kb_changingnote_idx] != ')'):
                        self.kb_changingnote_idx += 1
                    # Skip the closing bracket too
                    self.kb_changingnote_idx += 1

                self.update_scrolling_text(self.kb_changingnote_txt[self.kb_changingnote_idx: self.kb_changingnote_idx + self.KB_CHANGING_NOTE_LENGTH])
        
        if self.iv_isgame.get() == 1:
            self.update_score()

    # Overriden method
    def play_char_note(self, c):
        if c in self.charmap:
            # We will always add a note so that the game mode will have something to listen for
            # even if nothing is being drawn
            timing = 0
            # we need to sync the circle animation, so make it wait for the keyboard
            # Actually, since the scrolling text follows the same timestep as the keyboard, let's just wait for them both
            # if self.iv_showkeyboard.get() == 1:
            timing = -self.CIRCLE_WAIT_ITERS_TO_SYNC
            note_in_animation = [timing, None, 0, c]
            if self.iv_animatecircles.get() == 1:
                curr_x, curr_y = self.charmap[c]
                note_in_animation[1] = self.canvas.create_circle(curr_x, curr_y, 0, outline="red", width=2)
            self.notes_in_animation.append(note_in_animation)

        if self.iv_showkeyboard.get() == 1:
            if c in KEY_INFO_MAP:
                curr_y = self.SCROLL_TEXT_HEIGHT + KEY_INFO_MAP[c][0] * self.height_per_key
                colour = KEY_INFO_MAP[c][1][0]
                outline = KEY_INFO_MAP[c][1][1]

                # print(self.canvas_width)
                self.notes_in_animation.append(
                    (self.KB_ANIM_START_VAL, self.canvas.create_rectangle(self.canvas_width, curr_y, self.canvas_width + self.note_width, curr_y + self.note_height, outline=outline, fill=colour), 1, c)
                )
                self.notes_in_animation.append(
                    (self.KB_ANIM_START_VAL, self.canvas.create_text(self.canvas_width + self.note_width / 2, curr_y + self.note_height / 2, fill='black', font="Serif 11 bold", text=c), 1, c)
                )
    
    # Overriden method
    def on_delete_note(self, note):
        if self.iv_isgame.get() == 0:
            return

        iterations, obj, is_keyboard_note, c = note
        print("ODN ACQ", c)
        self.keys_and_timings_mutex.acquire()
        if c in self.keys_and_timings_to_track:
            # if self.keys_and_timings_to_track[c] <= 0:
            #    del self.keys_and_timings_to_track[c]
            # else:
            if self.keys_and_timings_to_track[c] > 0:
                self.keys_and_timings_to_track[c] -= 1
        # Python will hang if I update the label in critical section
        # self.update_score()
        self.keys_and_timings_mutex.release()
        print("ODN REL")

    # Overriden method
    def animate_object(self, i, note_in_animation):
        iterations, obj, type_of_display, c = note_in_animation

        # Get coords; 
        if type_of_display == 0:
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
                if (self.ITERATIONS_UNTIL_ANIM_OVER - iterations == self.START_KEYPRESS_CHECKITER):
                    print("ANIM ACQ")
                    self.keys_and_timings_mutex.acquire()
                    if c in self.keys_and_timings_to_track:
                        self.keys_and_timings_to_track[c] += 1
                    else:
                        self.keys_and_timings_to_track[c] = 1
                    self.scoreables += 1
                    self.keys_and_timings_mutex.release()
                    print("ANIM REL")
            
            if self.iv_macro.get() == 1:
                if (self.ITERATIONS_UNTIL_ANIM_OVER - iterations == self.START_KEYPRESS_CHECKITER):
                    char_val = c.lower()
                    self.keyboard.press(char_val)
                    self.keyboard.release(char_val)

        
        if type_of_display == 1 and self.iv_showkeyboard.get() == 1:
                # Get coords
                coords = self.canvas.coords(obj)
                if len(coords) == 4:
                    # Boxes have 4 coordinates
                    x1, y1, x2, y2 = coords
                    # Update using expansion rate
                    self.canvas.coords(obj, 
                        x1 - self.KB_DROP_RATE, y1, 
                        x2 - self.KB_DROP_RATE, y2)
                    # Change box color
                    if (self.ITERATIONS_UNTIL_ANIM_OVER - iterations == self.START_KEYPRESS_CHECKITER):
                        if c in KEY_INFO_MAP:
                            self.canvas.itemconfig(obj, fill=KEY_INFO_MAP[c][1][2])
                else:
                    # Text only have 2 coordinates
                    x, y = coords
                    # Update using expansion rate
                    self.canvas.coords(obj, x - self.KB_DROP_RATE, y)


        self.notes_in_animation[i] = (iterations + 1, obj, type_of_display, c)
    
    # override
    def song_ended(self):
        if self.iv_isgame.get() == 0 or self.scoreables <= 0:
            return
        self.root.resizable(width=True, height=True)
        self.run_mssthread = False
        final_score = (self.score - 0.5 * (self.false_notes)) / (self.scoreables * 1.0)
        print(final_score)
        venti_verdict = ""
        stars = "☆☆☆"
        if final_score < 0.33:
            stars = "★☆☆"
            chars = ['Klee', 'Razor', 'Bennett', 'Mona']
            venti_verdict = (
                "Not bad... but you can do better. Don't give up! "
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
                "Wow, that must've taken a lot of practice... Or are you just talented? "
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
        self.label_score['text'] = "Score: {0}/{1} notes hit - 1/2 * {2} wrong notes played = {3}".format(self.score, self.scoreables, self.false_notes, self.score - 0.5 * (self.false_notes))
        # self.sv_scorelabel.set("Score: {0}/{1} notes hit - 1/2 * {2} wrong notes played = {3}".format(self.score, self.scoreables, self.false_notes, self.score - 0.5 * (self.false_notes)))
        pass


    def on_closing(self, call_root_destroy):
        print("key-recorder closing")
        self.run_mssthread = False
        super().on_closing(False)
        
        if call_root_destroy:
            self.root.destroy()
    
    # Note: the code doesn't account for the fact that the screen may be out of bounds.
    def get_monitor(self):
        self.root.update()
        # I soon realize that r is not actually the radius, but welp lmao
        r = int(self.sv_radius.get()) # deduct the width of the circle outline
        x_offset = int(self.sv_x_offset.get())
        y_offset = int(self.sv_y_offset.get())
        x_spacing = int(self.sv_x_spacing.get())
        y_spacing = int(self.sv_y_spacing.get())
        # print("y", self.canvas.winfo_rooty(), self.top_frame.winfo_rooty())
        return {
            "left": self.canvas.winfo_rootx() + x_offset - r,
            "top": self.canvas.winfo_rooty() + y_offset - r,
            "width": (7 * (r + x_spacing)), # self.canvas.winfo_width(),
            "height": (3 * (r + y_spacing)) # self.canvas.winfo_height()
        }

    def screen_prep(self):
        # (left_incl, right_excl, top_incl, btm_excl)
        self.key_positions = []

        r = int(self.sv_radius.get()) # deduct the width of the circle outline
        x_offset = int(self.sv_x_offset.get())
        y_offset = int(self.sv_y_offset.get())
        x_spacing = int(self.sv_x_spacing.get())
        y_spacing = int(self.sv_y_spacing.get())

        curr_x = r
        curr_y = r
        
        for k in range(3):
            for j in range(7):        
                # -3 to remove the circle outline
                self.key_positions.append((curr_x - (r - 3), curr_x + r - 3, curr_y - (r - 3), curr_y + r - 3, KEYS[k][j]))
                curr_x += r + x_spacing
            curr_x = r
            curr_y += r + y_spacing
 
if __name__ == "__main__":
    my_application = KeyRecordApplication()
    my_application.start()
