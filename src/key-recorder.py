# Requirements: python3, numpy, opencv, mss, tkinter

import time
import numpy as np
import cv2
# from matplotlib import pyplot as plt
import mss
import threading

import main_overlay

from tkinter import *
from tkinter import scrolledtext

HUE_80_90_THRESHOLD = 0.3

KEYS = [['Q','W','E','R','T','Y','U'],
    ['A','S','D','F','G','H','J'],
    ['Z','X','C','V','B','N','M']]

key_state = {'Q': False,'W': False,'E': False,'R': False,'T': False,'Y': False,'U': False,
'A': False,'S': False,'D': False,'F': False,'G': False,'H': False,'J': False,'Z': False,
'X': False,'C': False,'V': False,'B': False,'N': False,'M': False}

def mssthread(app):
    result = []
    # Main logic loop
    with mss.mss() as sct:
        monitor = app.get_monitor()
        start_time = time.time()
        while app.run_mssthread:
            # Part of the screen to capture
            # print(monitor)
            # while "Screen capturing":
            # last_time = time.time()
            now_time = time.time()

            # Get raw pixels from the screen, save it to a Numpy array
            img = np.array(sct.grab(monitor))
            # plt.imshow(img, interpolation='nearest')
            # plt.show()
            # return
            img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Show via matplotlib to make sure i'm not doing anything silly
            # fig, axes = plt.subplots(nrows=3, ncols=7, sharex=True, sharey=True)
            # iterval = 0

            # For now we'll not be using S,V
            img = np.delete(img, [1,2], 1)
            for i in app.key_positions:
                crop = img[i[2] : i[3], i[0] : i[1]]
                # Detect by thresholding to detect that greenish tint
                # If this doesn't work well, then we'd need to detect by colour delta 
                green_count = np.count_nonzero((80 < crop) & (crop < 90))
                pixel_count = crop.shape[0] * crop.shape[1] # * crop.shape[2]

                # matplotlib is telling me it's off by 1 or so pixels, but it's fine for our purposes
                # axes[iterval // 7, iterval % 7].imshow(crop, interpolation='nearest')
                # iterval += 1
                # print (green_count, pixel_count)
                if green_count / pixel_count > HUE_80_90_THRESHOLD:
                    # print(i)
                    if not key_state[i[4]]:
                        result.append((i[4], int((now_time - start_time) * 1000)))
                    key_state[i[4]] = True

                else:
                    key_state[i[4]] = False
            # plt.show()
            # return
            # print("fps: {}".format(1 / (time.time() - last_time)))
    # Clean-up on stop button pressed
    print(result)
    # Re-used code
    prev_sequence = ""
    prev_press = -1
    final_press = -1
    frame_time = 1000 / 30
    # Append text to the textboxes as needed
    # Keystrokes will append the text as the come, but in text_format1 it uses time_elapsed to next note.
    for key_val, curr_time in result:
        final_press = curr_time
        if prev_press == -1:
            prev_press = curr_time
            prev_sequence += key_val
        else:
            time_elapsed = curr_time - prev_press
            if time_elapsed >= frame_time:
                append_txt(app.text_format1, "{0} {1}\n".format(prev_sequence, time_elapsed))
                space = ""
                # Use arbitrary constant to denote when to add spaces (lol)
                # This is around 300+ms
                if time_elapsed > frame_time * 10:
                    space = " "
                if len(prev_sequence) > 1:
                    append_txt(app.text_strokes, "{0}({1})".format(space, prev_sequence))
                else:
                    append_txt(app.text_strokes, "{0}{1}".format(space, prev_sequence))

                prev_sequence = ''
                prev_press = curr_time

            prev_sequence += key_val
    
    # Thus, we don't need to append to text_strokes, but need for text_format1
    if prev_sequence != "":
        append_txt(app.text_format1, "{0} {1}\n".format(prev_sequence, 0))
        
        time_elapsed = final_press - prev_press
        space = ""
        if time_elapsed > frame_time * 10:
            space = " "
        if len(prev_sequence) > 1:
            append_txt(app.text_strokes, "{0}({1})".format(space, prev_sequence))
        else:
            append_txt(app.text_strokes, "{0}{1}".format(space, prev_sequence))
    
    app.button_stop['state'] = 'disabled'
    app.button_start['state'] = 'normal'

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
        self.config_filename = "config_key_recorder.txt"
        super().__init__()
        # https://stackoverflow.com/questions/12364981/how-to-delete-tkinter-widgets-from-a-window
        # Remove elements we won't use
        self.label_file.destroy()
        self.entry_file.destroy()
        self.button_play.destroy()

        self.root.title('Key Recorder')
        self.sv_descriptlabel.set('Resize the circles to fit the notes, then press the Start button. Press Stop when finished.')
        self.button_start = Button(self.top_frame, text='Start', background="green", command=self.start_button_press)
        self.button_start['state'] = 'normal'
        self.button_stop = Button(self.top_frame, text='Stop', background="red", command=self.stop_button_press)
        self.button_stop['state'] = 'disabled'

        self.button_start.grid(row=0, column=0)
        self.button_stop.grid(row=0, column=1)

        # create the string values for the entries that invoke an event after being changed
        self.bottom = Frame(self.root, bg='gray2', padx=2, pady=2)
        self.bottom.grid(row=2, sticky="nsew")

        self.text_format1 = scrolledtext.ScrolledText(self.bottom, background="lavender", wrap=WORD)
        self.text_format1.grid(row=0, column=0)
        self.text_strokes = scrolledtext.ScrolledText(self.bottom, background="lavender", wrap=WORD)
        self.text_strokes.grid(row=0, column=1)

        self.prev_press = -1
        self.prev_sequence = ''
        # frame_time = 1000 / 30

        append_txt(self.text_format1, "Song Name\nFormat: 1\nSPEED 1.0\n")

        # Redraw outlines without labels
        self.redraw_outlines(False)
        # run event loop until window appears
        self.root.wait_visibility()
        # Perform this action, as sct will cause modifications to the size of the screen on start-up
        with mss.mss() as sct:
            pass
        self.run_mssthread = False
        print(self.get_monitor())

    def reformat_outlines_callback(self, sv):
        if (sv.get().isdigit()):
            # Redraw outlines without labels
            self.redraw_outlines(False)
            return True
        return False

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

    def start_button_press(self, event=' '):
        # Start 
        # Run the app's main logic loop in a different thread
        # self.button_start['state'] = 'disabled'
        self.screen_prep()
        self.run_mssthread = True
        """
        # Code to check out what I'm actually screenshotting
        with mss.mss() as sct:
            monitor = self.get_monitor()
            img = np.array(sct.grab(monitor))
            plt.imshow(img, interpolation='nearest')
            plt.show()
        return 
        """
        main_loop_thread = threading.Thread(target=mssthread, args=(self, ))
        main_loop_thread.daemon = True
        main_loop_thread.start()
        # print(my_application.get_screenshot_region())
        self.button_stop['state'] = 'normal'

    def stop_button_press(self, event=' '):
        self.run_mssthread = False
        # thread will enable the UI when it's ready

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

    """
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
                #
                i = (curr_x - r, curr_x + r - 1, curr_y - r, curr_y + r - 1)
                crop = img[i[2] : i[3], i[0] : i[1]]

                green_count = np.count_nonzero((80 < crop) & (crop < 90))
                pixel_count = crop.shape[0] * crop.shape[1] # * crop.shape[2]
                print (green_count, pixel_count)
                if green_count / pixel_count > 0.3:
                    print('Pressed')
                # print(k, j)
                # print(crop)
                # print("\n\n\n")
                # green threshold: H and S between 80 and 90
                #
                curr_x += r + x_offset
                #
                # Snippet for checking code
                import numpy as np
                a = np.asarray([ [1,2], [3,4], [4,1], [6,2], [5,3], [0,4] ])
                print(a)
                print(np.count_nonzero((0 < a) & (a < 2)))
                # 
                # Snippet for getting colour characteristics    
                #
                color = ('b','g','r')
                for f,col in enumerate(color):
                    histr = cv2.calcHist([crop],[f],None,[256],[0,256])
                    plt.plot(histr,color = col)
                    plt.xlim([0,256])
                plt.show()
                # 
                # return
            curr_x = r + x_offset
            curr_y += r + y_offset
    """
 
if __name__ == "__main__":
    my_application = KeyRecordApplication()
    my_application.start()
