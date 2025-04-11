# WaVeS
<p align="center">
  <img src="https://github.com/JRitmeester/WaVeS/blob/main/WaVeS.png" width="500px">
</p>

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

### Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- A Windows machine (to run and build the executable)
- Git (obviously)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/JRitmeester/WaVeS.git
   cd WaVeS
   ```

2. Install dependencies with Poetry:

   ```bash
   poetry install
   ```

3. Install PyQt5 manually (it's weird and doesn't install cleanly through Poetry sometimes):

   ```bash
   poetry run pip install pyqt5
   ```

---

### 🧱 Building the Executable

To build a standalone `.exe`:

```bash
build.bat
```

This will:
- Export dependencies from Poetry
- Run PyInstaller using `WaVeS.spec`
- Output `WaVeS.exe` in the `dist/` directory


## Contributing
Because this is a side project that I already spend more time on than I maybe should, I do currently not accept any unexpected pull requests. If you have an idea or feature request, feel free to open an issue and we can see what we can come up with!

## License
[GNU AGPLv3](https://choosealicense.com/licenses/agpl-3.0/)

