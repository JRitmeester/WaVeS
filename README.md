# WaVeS

WaVeS (Windows Volume Sliders) is a Python app that interfaces with a microcontroller that sends volume slider data over a serial connection to control the volume of applications in Windows.

## Inspiration

WaVeS is inspired by [Deej](https://github.com/omriharel/deej) and fulfills the exact same purpose. However, because it is written in Go, there was very little I could change about it. Using Python and the [Pycaw](https://github.com/AndreMiras) library, I made an interface that is hopefully more flexible for anyone who wants to customise the functionalities.

The Arduino code can be found [here](https://github.com/omriharel/deej/blob/master/arduino/deej-5-sliders-vanilla/deej-5-sliders-vanilla.ino).

## Installation

Opening the executable for the first time will create a `mappings.yml` file in `%AppData%/WaVeS`. This serves as the configuration file. Please read the contents of the file to see how you can designate each slider to on of the following:
* Master volume (`master`)
* System volume (`system`)
* A specific application (`chrome.exe`, `spotify.exe`, games, etc.)
* A specific output device (see below)
* Unmapped (everything that does not have its own slider)

* A specific output device. 

## Example config file
An example of a config file (without comments) is:
```
mappings:
  0:
    - master
  1:
    - system
  2:
    - discord.exe
  3:
    - brave.exe
    - spotify.exe
  4:
    - unmapped

device:
  name: "Arduino Micro"
  port: "COM6"  # Only used if device name cannot be found automatically
  baudrate: 9600
  sliders: 5

settings:
  inverted: false  # When true: top=low volume, bottom=high volume
  system_in_unmapped: true  # Include system sounds in 'unmapped' if not explicitly assigned
  session_reload_interval: 1  # Interval in seconds to check for new applications
```

Unassigned apps can be excluded from "unmapped" by assigning those apps to a non-existent slider number:
```
1000:
    - chrome.exe
```
This will allow you to control all unmapped apps with "unmapped" but exclude Chrome. Why you'd want this, I'm not sure, but it's probably useful in some edge cases.

## Customisation
You are free to use the source code. The repository contains a `build.bat` file that will compile the necessary files into an executable in the same directory, including the icon. If you share this project with other parties, please do give credit where appropriate.

## Contributing
In order to clone the project and set it up, you can run `poetry install` which should work for the most part. However PyQt5 is annoying and requires manual installation afterwards using `poetry run pip install pyqt5`.

## License
[MIT](https://choosealicense.com/licenses/mit/)
