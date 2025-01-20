# my_cam_py
我的桌面錄影

用 python 寫的桌面錄影工具

<h3>開發動機:</h3> 
覺得人生是該寫一個桌面錄影，就開始寫了

<h3>版本：</h3>
V0.01

<h3>作者：</h3>
 羽山秋人 (https://3wa.tw)

<h3>版權：</h3>
 MIT

<h3>最初開發日期：</h3>
 2024-07-12
 
<h3>使用方法：</h3>
<ul>
	<li>1. 框選螢幕想錄的範圍</li>
	<li>2. 設定好 fps，通常大概只會選 30 或 60 吧</li>
	<li>3. 壓縮品質，與 png 壓縮品質有關 0 最清晰，建議設 1 或 2</li>
	<li>4. 要錄滑鼠指標嗎 可勾選</li>
	<li>5. 錄系統聲音嗎 可勾選</li>
	<li>6. 要錄麥克風嗎 可勾選</li>
	<li>7. 按下開始錄影即開始</li>
	<li>8. 按下停止錄影，會稍卡一下，按下確定後，會開始進行影片、聲音合併轉檔</li>
	<li>9. 打開資料夾，影片會存在執行程式的 output 目錄</li>
</ul>
<hr>
<center>
<img src="pic/s1.png"><br>
程式執行畫面
</center>


<h3>相依套件：</h3>
	python3.12 x64 位元，建議可安裝在 C:\python312_64<br>
	將系統路徑<br>
		PATH 加上 C:\python312_64<br>
		PATH 加上 C:\python312_64\Scripts<br>
	<img src="pic/s2.png"><br>
		
	opencv-python==4.10.0.84
	sounddevice==0.4.7
	soundfile==0.12.1
	scipy==1.14.0
	moviepy==1.0.3
	pydub==0.25.1
	pywin32==306
	pywin32-ctypes==0.2.2
	pyinstaller==6.9.0
	mss (此版羽山有微調 base.py 與 windows.py)
	
	詳見 requirements.txt
	
<h3>安裝相關套件：</h3>
	C:\python312_64\Scripts\pip.exe install -r requirements.txt

<h3>啟動：</h3>
	run.bat
	
<h3>編譯成exe：</h3>
	可詳見 build.bat
	如果不想執行時有視窗，可以加上 -w 參數
	
<h3>成果範例：</h3>
	https://github.com/shadowjohn/my_cam_py/tree/main/examples

<h3>更新歷程：</h3>
(2024-07-14) v0.01 版：<br>
初版<br>
https://www.microsoft.com/en-us/wdsi/submission/3ed2b02f-bdb6-43b3-86ce-86acf056181e
		
<h3>Todo：</h3>

