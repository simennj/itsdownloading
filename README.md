# itsdownloading
Bulk downloading of course files from itslearning for NTNU students before the switch to blackboard.
Can download any of your favorite courses. Make sure that the course is starred/marked as favorite
if it is not one of the available courses in the downloader.

## Run from source
You can run the script directly using python 3.5 (or later) and the libraries listed in requirements.txt
(use pip install -r requirements.txt to install them using pip).

### Step by step guide

1. Install Python from https://www.python.org/. Make sure you get version 3.5 or newer (__not__ 2.7).
2. Download the files from https://github.com/simennj/itsdownloading/archive/master.zip
3. Extract the files to a folder where you will find them.
4. Open the terminal if on Mac or cmd if on windows and navigate to the folder you extracted the files to. Guide for Mac users [here](https://computers.tutsplus.com/tutorials/navigating-the-terminal-a-gentle-introduction--mac-3855), guide for windows users [here](http://www.digitalcitizen.life/command-prompt-how-use-basic-commands).
5. Run `pip install -r requirements.txt` and then `python itsdownloading.py`.

## Run from standalone executable
Since python can be a bit of a pain to set up on windows, i have created executables for Windows.
You can find them [here](https://github.com/simennj/itsdownloading/releases).
