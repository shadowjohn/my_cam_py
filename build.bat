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
--exclude-module=pygments ^
--add-data=C:\Python312_64\Lib\site-packages\moviepy:moviepy ^
my_cam_py.py