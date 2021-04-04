# Genshin Lyre Overlay AKA Venti Sensei
A Python program that highlights the notes when you play the lyre on Genshin Impact. 

Comes with an exe to work out of the box for non-programmers.

## Main-overlay.py / Main-overlay.exe
* The Window will overlay the keystrokes on the buttons for quality of life, and also animate the buttons you will have to press.
<img src="https://cdn.discordapp.com/attachments/826031962074513408/826367978660167700/unknown.png" width="512">

Quick demo of the old version that doesn't have button mapping overlay: https://i.imgur.com/VnqTvVv.mp4

## Main-keyboard.py / Main-keyboard.exe
* There is an alternate UI that shows the keyboard instead, and the notes fall from the top like synthesia:
* <img src="https://imgur.com/pAHS72u.png" width="512">
* This version is more suitable for playing more complicated pieces, and includes a textbox for you to modify the rate at which new notes appear.

Platform: Windows (Code is in Python, can be ported to MacOS)

## Main-overlay-game.py / Main-overlay-game.exe
* Game Mode, allows you to play your own songs. Uses the overlay UI, but this application also tracks your keystrokes. It then gives you a score (and some comments from Venti :p).

### How does it work?
* The application creates a window that overlays all other applications, including Genshin Impact in windowed mode.
* The user modifies the size and spacing of the circles based on their notes keyboard, and move the window such that they overlay the notes keyboard.
* The user inputs the filepath (filename) of the song they want to play and presses play button.
* The program will highlight the notes to play.
* After the song has ended, the user can input another filename to play that song.

### How to use the application
* You can run the main.exe files in the dist directory. If you have python 3.7 on your computer, you can just run the script directly in the src directory, so long as you have the dependencies installed.
* If the exe does not work, open command line and run the application from the command line; this will show you the error. Open an issue and paste the screenshot or dump the error text.

### How to add songs & the syntax
* Include your file containing the song in the same directory as the application.
* I have included an example song in the music directory `music/sample.txt` for reference.

### Supported Syntaxes
* The application will parse files differently based on the music file extension. You can find examples for each format in the music directory within dist or src directories.
* **.txt**: text file. In txt format. The first two lines are the same for every format under `.txt`. 
* **First Line:** Song name
* **Second Line:** `format: {number}`, where number represents the format number. This will determine how the program parses the file.
* **Third line onwards:** The application will process the data based on the format number:
* **Format 1**: Keypresses & delays on every line
    * Each line from the 3rd line onwards denotes a new entry. Each entry is:
    * `{Keys to press}{1 space}{milliseconds before the program plays the next entry}`
      * Note that the keys to press must not have any whitespace between them.
      * e.g. `QWE 1290` will prompt the user to press QWE at the same time, and wait 1290ms before prompting the next entry.
* **Format 2**: Notes in alphabetical format & delays on every line
  * * Each line from the 3rd line onwards denotes a new entry. Each entry is:
    * `{Note to press}{1 space}{milliseconds before the program plays the next entry}`
      * `format2_sample.txt` serves as a sample.
  * It also supports 1 command:
    * `OCT{number}`: Set the default octave (no space between OCT and number). So instead of specifying `C4`, you can just specify `C` and the program will auto-fill it to `C4` if the default octave is 4. The command can be called by putting `OCT{number}` on any new line.
  * In addition, as a quality of life add-on for comments & formatting, empty new lines and any lines with the prefix '/' will be skipped.
* **Format 3**: Keyboard sheet reading
  * The motivation of this format is to support music written in keystrokes format that do not have timing information.
  * New lines do not matter in this format, so long as they do not start with the prefix `BPM`, `DELAY` or `/`.
  * **Syntax**: 
    * Spaces and new lines do not matter when it comes to keystrokes.
    * Alphabets represent the keystrokes. e.g. `QW` will mean the program plays Q, then on the next beat play W.
    * Adding a `-` between two keystrokes signify that we skip one beat before playing the next keystroke. Multiple dashes would represent multiple beats skipped ahead.
    * Wrapping multiple keystrokes with brackets e.g. `(AQW)` signifies that they are played on the same beat.
  * **Commands**: Every command must start on a new line, and any keystrokes that follow after the command must start on a new line. The supported commands are:
    * **Set BPM**: `BPM {number}`: Set the BPM to the number specified for the rest of the keystrokes.
    * **Set BPM using ms**: `INTERVAL {milliseconds}`: Set the BPM by specifying the number of milliseconds between each beat.
    * **Delay keypresses**: `DELAY {number}` or `= {number}`: Add a pause between the previous keystrokes and the next. The number represents the number of beats we skip ahead.
    * **Delay keypresses (ms)**: `DELAY_MS {milliseconds}`: Add a pause between the previous keystrokes and the next by specifying the number of milliseconds instead.
  * Comments (any new lines prefixed by `/`) will be ignored by the parser.
* **.json**: [Sky Music](https://sky-music.herokuapp.com/) format exported directly from the herokuapp in JSON format (you have to rename the .txt file extension to .json). 
  * No modification by the user is required. Note that BPM is not factored into this application.
* **.txtmidi**: Unofficial file format that can be converted from midi as I am lazy to figure out how to properly use mido.py
  * Every new line is a note (numerical), space, then the timestamp of the note.
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
* Note that game mode tracks your keypresses but does not send anything.

### User requirements
* Windows
* Unknown lmao I need more people to help me test this
### Development requirements
* Main Application
  * Python3, Tkinter, PIL, pynput is sufficient to run the python script without compiling.
  * If compiling the python script as executables: 
    * [PyInstaller](https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen)
    * [Compiling as 1 exe](https://stackoverflow.com/questions/53678993/pyinstaller-importerror-error-how-to-solve-it)
    * [Issue with pynput: must install with "pip install pynput==1.6.8"](https://stackoverflow.com/questions/63681770/getting-error-when-using-pynput-with-pyinstaller)
* Midi Converter
  * C#, .NET Framework 5.0

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