pyinstaller --onefile --noconsole --specpath WaVeS/spec --distpath WaVeS/dist --workpath WaVeS/build --icon=icon.ico --hidden-import win32api main.py
copy "icon.ico" "WaVeS/dist"