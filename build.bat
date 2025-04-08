poetry export --without-hashes --format=requirements.txt > requirements.txt
poetry run pyinstaller WaVeS.spec