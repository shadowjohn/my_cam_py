rem rd /S build
rem -w --clean
c:\python312_64\scripts\pyinstaller -F --onefile --icon="pic\icon.ico" --version-file=metadata.txt ^
--exclude-module=_ssl ^
--exclude-module=_bz2 ^
--exclude-module=_lzma ^
--exclude-module=pyconfig ^
--exclude-module=pytorch ^
--exclude-module=torch ^
--exclude-module=sqlite3 ^
--exclude-module=pandas ^
--exclude-module=IPython ^
--exclude-module=scipy ^
--exclude-module=matplotlib ^
--exclude-module=contourpy ^
--exclude-module=cycler ^
--exclude-module=fontTools ^
--exclude-module=kiwisolver ^
--exclude-module=tornado ^
--exclude-module=pygments ^
--exclude-module=pyinstaller ^
--exclude-module=tensorflow ^
--exclude-module=unittest ^
--exclude-module=doctest ^
--exclude-module=pillow ^
--exclude-module=av ^
--exclude-module=requests ^
--exclude-module=urllib3 ^
--exclude-module=certifi ^
--exclude-module=charset_normalizer ^
--exclude-module=idna ^
--exclude-module=setuptools ^
--exclude-module=PIL ^
my_cam_py.py
