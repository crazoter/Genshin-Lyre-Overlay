# Genshin Lyre Overlay AKA Venti Sensei
A Python program that highlights the notes when you play the lyre on Genshin Impact. Comes with an exe to work out of the box for non-programmers.

## Main.py
* The Window will overlay the keystrokes on the buttons for quality of life, and also animate the buttons you will have to press.
<img src="https://cdn.discordapp.com/attachments/826031962074513408/826367978660167700/unknown.png" width="512">

Quick demo of the old version that doesn't have button mapping overlay: https://i.imgur.com/VnqTvVv.mp4

## Main-keyboard.py / Main-keyboard.exe
* There is an alternate UI that shows the keyboard instead, and the notes fall from the top like synthesia:
* <img src="https://imgur.com/pAHS72u.png" width="512">
* This version is more suitable for playing more complicated pieces, and includes a textbox for you to modify the rate at which new notes appear.

Platform: Windows (Code is in Python, can be ported to MacOS)

### How does it work?
* The application creates a window that overlays all other applications, including Genshin Impact in windowed mode.
* The user modifies the size and spacing of the circles based on their notes keyboard, and move the window such that they overlay the notes keyboard.
* The user inputs the filepath (filename) of the song they want to play and presses play button.
* The program will highlight the notes to play.
* After the song has ended, the user can input another filename to play that song.

### How to use the application
* You can run the main.exe files in either `build/main.exe` or `dist/main.exe`. If you have python 3.7 on your computer, you can just run the script directly using `python3 src/main.py`.

### How to add songs & the syntax
* Include your file containing the song in the same directory as the application.
* I have included an example song in the music directory `music/sample.txt` for reference.

### Supported Syntaxes
* The application will parse files differently based on the music file extension.
* **.txt**: text file. In txt format, the numbers represent the duration (in ms) to wait before playing the set of notes on the next line.
* The syntax of the files are as follows (I'm not musically trained so bear with me):
  * 1st line: Name of the song to be displayed on screen
  * 2rd line onwards: Each line denotes a new entry. Each entry is:
  * {Keys to press}{1 whitespace}{number of milliseconds to the next entry}
    * Note that the keys to press must not have any whitespace between them.
    * e.g. `QWE 1290` will prompt the user to press QWE at the same time, and wait 1290ms before prompting the next entry.
* **.json**: [Sky Music](https://sky-music.herokuapp.com/) format exported directly from the herokuapp in JSON format (you have to rename the .txt file extension to .json). 
  * No modification by the user is required. Note that BPM is not factored into this application.
* **.txtmidi**: Unofficial file format that can be converted from midi as I am lazy to figure out how to properly use mido.py
  * Every new line is a note, space, then the timestamp of the note.
  * To use midi files, put the name of the midi as `file.midi` in `Midi Converter/bin/debug/net5.0/file.midi`. Run the exe and you'll get `output.txtmidi`. Rename this txtmidi to whatever name you want; you can use this txtmidi in the application.
  * You can open `output.txtmidi` in any text editor as it is not a binary file.
### Visual Cues
* As the notes are placed in a compact fashion in-game, I decided to make the visual cues akin to an expanding circle from the centre of the button, like the exact opposite of the Windblume mini-game where they converge onto the button:
  * When the edge of the circle touches the edge of the button, that is when you want to play the note.
  * Held notes don't apply to the lyre, so the feature is not included.

### Will I get banned by using this application?
* This has a few advantages over a macro:
  * The application does not detect or interact with the Genshin Impact window.
  * The application does not perform or detect any keypresses; the player is still in full control of the lyre.
  * As such, it is much more unlikely that Mihoyo will ban you for using this application (as opposed to using a macro, which can be easily detected to be producing an abnormal amount of keypresses).

### Compilation requirements
* Python3, Tkinter, PIL, [PyInstaller](https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen)

### How to contribute:
* To the playlist of songs:
  * I have created a github issue for adding new songs. Simply leave a comment including your song in the appropriate format for others to use!
* To the repository:
  * There are plenty of possible improvements / new features and you are more than welcome to contribute :)
    * Convert Midi / other music formats into notes
    * UX / UI improvements
    * Support for other platforms
    * Testing / Bug fixes
* To my Welkin Moon fund :p
  * You can donate via PayPal if you liked it and you want to sponsor my Welkin Moon: https://paypal.me/crazoter

## Q & A
* Q: Any intentions to implement this system on other platforms?
  * A: No, but if you have experience and want to contribute, feel free :)
