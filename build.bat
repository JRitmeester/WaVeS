pyinstaller --onefile --noconsole --specpath WaVeS/spec --distpath WaVeS/dist --workpath WaVeS/build --hidden-import win32api main.py
copy "WaVeS/dist" "."
@RD /S /Q "WaVeS"