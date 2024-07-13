# my_cam_py
我的桌面錄影

用 python 寫的桌面錄影工具

版本: V0.01
作者: 羽山秋人 (https://3wa.tw)

LICENSE: MIT
<hr>
<img src="pic/s1.png">
程式執行畫面


相依套件:
	python3.12 x64 位元，可安裝在 C:\python312_64
	將系統路徑
		PATH 加上 C:\python312_64
		PATH 加上 C:\python312_64\Scripts
	<img src="pic/s2.png">	
	
	opencv-python==4.10.0.84
	sounddevice==0.4.7
	soundfile==0.12.1
	scipy==1.14.0
	moviepy==1.0.3
	pydub==0.25.1
	pywin32==306
	pywin32-ctypes==0.2.2
	pyinstaller==6.9.0
	mss (此版羽山有微調)
	
	詳見 requirements.txt
	
安裝相關套件:
	pip install -r requirements.txt

啟動:
	run.bat
	
編譯成exe:
	可詳見 build.bat
	如果不想執行時有視窗，可以加上 -w 參數
		
	
