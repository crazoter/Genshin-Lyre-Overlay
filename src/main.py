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
        super().__init__()
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

        self.iv_showkeyboard = IntVar(value=0)
        c3 = Checkbutton(self.top_frame, text='Animate Keyboard (Laggy)',variable=self.iv_showkeyboard, onvalue=1, offvalue=0,fg='red')
        c3.grid(row=2, column=4, columnspan=2)
        self.inputObjects.append(c3)
        
        # self.sv_scorelabel = StringVar(self.root, value="Score: ")
        self.label_score = Label(self.top_frame, text='')
        self.label_score.grid(row=2, column=6, columnspan=8)

        # Redraw outlines without labels
        self.redraw_outlines(self.iv_animatecircles.get() == 1)
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
        self.KB_BAR_HEIGHT = 150
        self.KB_NOTE_HEIGHT = 10
        self.KB_HEIGHT = 250
        self.KB_DROP_RATE = self.KB_BAR_HEIGHT / self.KB_ITERATIONS_UNTIL_ANIM_OVER
        # this is a pretty funny hack
        # basically every tick will increment the iteration value from 0 to ITER_UNTIL_ANIM_OVER, then remove it when it reaches
        # This sets the value to negative so that it will animate properly (the base ITER_UNTIL_ANIM_OVER is for circles)
        self.KB_ANIM_START_VAL = self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ITERATIONS_UNTIL_ANIM_OVER
        # This is for the notes at the side
        self.kb_sidenote_offset = (self.songdata_idx, 0)
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
        
        self.kb_sidenote_printedto_idx = 0
        self.KB_CHANGING_NOTE_LENGTH = 255
        self.KB_CHANGINGNOTE_QUANT = 1
        # self.kb_changingnote_obj = self.kb_canvas.create_text(40, self.KB_BAR_HEIGHT + 70, font="11", fill="yellow", anchor=W)
        self.kb_changingnote_txt = ""
        self.kb_changingnote_idx = 0
        self.kb_changingnote_tick = 0
        self.kb_changingnote_notearr = [] # This will be used to hold (startIdx, endIdx) pairs for every note in the string
        self.kb_changingnote_notearr_idx = 0

        # https://stackoverflow.com/questions/29368737/how-to-color-a-substring-in-tkinter-canvas
        fn = "Sans Serif"
        fs = 14
        self.my_font = tkfont.Font(family=fn, size=fs)

        # words = '''I am writing a program that involves displaying some text in a create_text() box on a Tkinter canvas, within a loop. Each word is displayed, then replaced by the next. Sort of like flash cards. I need to color one letter of each word, close to the middle of the word, so that when the user is reading the words their eyes focus on the middle of the word. So if len(i)=1, color i[0], if len(i)>= 2 and <= 5, color i[1], and so on. It needs to be done using the Canvas, and using canvas.create_text(text = i[focus_index],fill = 'red') The result should print like this exaMple (but obviously "m" would be colored red, not be uppercase)'''
        # words = words.split()
        self.initial_scrolling_text_offset = self.KB_BAR_HEIGHT + 70
        # t1 = self.kb_canvas.create_text(200,100,text='', anchor='e', font=my_font, fill='green')
        self.t2 = self.kb_canvas.create_text(40, self.KB_BAR_HEIGHT + 70,text='', anchor='w', font=self.my_font, fill='yellow')
        self.t3 = self.kb_canvas.create_text(40, self.KB_BAR_HEIGHT + 70,text='', anchor='w', font=self.my_font, fill='orange')
        # t3 = self.kb_canvas.create_text(200,100,text='', anchor='w', font=my_font, fill='yellow')
        # new_word(0)

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
        self.kb_canvas.itemconfigure(self.t2, text=front)
        # self.kb_canvas.itemconfigure(t2, text=letter)
        self.kb_canvas.itemconfigure(self.t3, text=back)
        # self.kb_canvas.coords(self.t1, 200-self.my_font.measure(letter)/2, 100)
        self.kb_canvas.coords(self.t3, 40+self.my_font.measure(front), self.initial_scrolling_text_offset)

        # self.root.after(100, lambda: new_word(i+1))

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
        self.kb_sidenote_printedto_idx = 0
        self.kb_changingnote_txt = "." * (int(self.ITERATIONS_UNTIL_ANIM_OVER - self.KB_ANIM_START_VAL) // self.KB_CHANGINGNOTE_QUANT)
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
            while time_count > 0:
                time_count -= self.MS_PER_FRAME
                counts += 1
            # The plan is to strategically identify which notes can stretched over future '.'s so as to reduce the jittery effect
            note_str_len = len("{" + row[0] + ")")
            if counts > note_str_len + 1:
                self.kb_changingnote_notearr.append((len(self.kb_changingnote_txt), len(self.kb_changingnote_txt) + note_str_len))
                self.kb_changingnote_txt += "{" + row[0] + ")"
                self.kb_changingnote_txt += '.' * max(0, (counts - 1 + 1 - note_str_len) // self.KB_CHANGINGNOTE_QUANT)
            else:
                self.kb_changingnote_txt += "(" + row[0] + ")"
                self.kb_changingnote_txt += '.' * max(0, (counts - 1) // self.KB_CHANGINGNOTE_QUANT)

        # Try to make it smoother by making it occupy some spaces behind instead

        # self.kb_canvas.itemconfig(self.kb_changingnote_obj, text=self.kb_changingnote_txt[0:self.KB_CHANGING_NOTE_LENGTH])
        self.update_scrolling_text(self.kb_changingnote_txt[0:self.KB_CHANGING_NOTE_LENGTH])

        # add a placeholder element if we are not showing the keyboard for event handling
        if (self.iv_showkeyboard.get() == 0):
            note_in_animation = [30-len(self.kb_changingnote_txt), None, 2, '']
            self.notes_in_animation.append(note_in_animation)


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
                    (self.KB_ANIM_START_VAL - 30, self.kb_canvas.create_text(22 * 40, 6, fill='yellow', font="Times 8 bold", text=txt, anchor=W), 1, txt)
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

                #self.kb_canvas.itemconfig(self.kb_changingnote_obj,  text=self.kb_changingnote_txt[self.kb_changingnote_idx: self.kb_changingnote_idx + self.KB_CHANGING_NOTE_LENGTH])
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
        
        if type_of_display == 1 and self.iv_showkeyboard.get() == 1:
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


        self.notes_in_animation[i] = (iterations + 1, obj, type_of_display, c)
    
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
