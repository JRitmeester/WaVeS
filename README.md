# WaVeS

WaVeS (Windows Volume Sliders) is a Python app that interfaces with a microcontroller that sends volume slider data over a serial connection to control the volume of applications in Windows.

## Inspiration

WaVeS is inspired by [Deej](https://github.com/omriharel/deej) and fulfills the exact same purpose. However, because it is written in Go, there was very little I could change about it. Using Python and the [Pycaw](https://github.com/AndreMiras) library, I made an interface that is hopefully more flexible for anyone who wants to customise the functionalities.

The Arduino code can be found [here](https://github.com/omriharel/deej/blob/master/arduino/deej-5-sliders-vanilla/deej-5-sliders-vanilla.ino).

## Installation

The [executable](https://github.com/JRitmeester/WaVeS/releases/) can be downloaded as-is. It will create a `mappings.txt` file in the same directory as where the executable was run. This serves as the configuration file. Please read the contents of the file to see how you can designate each slider to on of the following:
* A specific application (`chrome.exe`, `spotify.exe`, games, etc.)
* System volume
* Unmapped (everything that does not have its own slider)
* Master volume
* A specific output device. 
  
## Specifying an output device.
To find the right name, go to Sound > Playback and find the name of the speaker you want to adjust. This does not have 
to be your default speaker (Otherwise you can just use "master"). You can specify a small part of the string if you 
want. The full format is: `device: [device name in black] ([device name in gray])`

Where you replace the first part `[device name in black]` with... the device name in black (like "Speakers) and the same
for `[device name in gray]`, like "Realtek High Definition Audio". Note the need for the parentheses `()`! If there is 
only one device with the name "Speakers" in either one, you can just use that.


## Example config file
An example of a config file (without comments) is:
```
0: master
1: system
2: chrome.exe, isaac-ng.exe, spotify.exe
3: discord.exe
4: unmapped
5: device: Speakers (Realtek High Definition Audio)

sliders: 6      # Number of sliders you have
port: COM7       # COM port used for automatic detection
device name: Arduino Micro  # Name of the device in device manager, used if COM port changes.
baudrate: 9600   # Baudrate of the microcontroller
inverted: False  # Invert the volume
system in unmapped: True     # Include system sounds in unmapped if it isn't explicitly assigned to anything.
```

Apps can be excluded from "unmapped" by assigning specific apps to a number equal to or higher than the number of sliders you have:
```
1000: chrome.exe
```
This will allow you to control all unmapped apps with "unmapped" but exclude Chrome. Why you'd want this, I'm not sure, but it's probably useful in some edge cases.

## Usage
Upon running the [executable](https://github.com/JRitmeester/WaVeS/releases/download/v1.0/WaVeSv1.0.exe), a tray icon will open. Clicking the icon will reload the mappings from `mappings.txt`, so that they can be changed as desired without having to close and restart the app.

## Customisation
You are free to use the source code. The repository contains a `buid.bat` file that will compile the necessary files into an executable in the same directory, including the icon. If you share this project with other parties, please do give credit where appropriate.

## Contributing
In order to clone the project and set it up, you can run `poetry install` which should work for the most part. However PyQt5 is annoying and requires manual installation afterwards using `poetry run pip install pyqt5`.

## License
[MIT](https://choosealicense.com/licenses/mit/)
