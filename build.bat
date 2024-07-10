rem rd /S build
c:\python312_64\scripts\pyinstaller -F -w --onefile --clean --icon="pic\icon.ico" --version-file=metadata.txt ^
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
--exclude-module=pygments ^
my_cam_py.py