# my_cam_py
我的桌面錄影

用 python 寫的桌面錄影工具

<h3>開發動機:</h3> 
覺得人生是該寫一個桌面錄影，就開始寫了

<h3>版本：</h3>
V0.01<br>
穩定化分支：錄影流程、音源選擇與長時間錄影穩定性調整中

<h3>作者：</h3>
 羽山秋人 (https://3wa.tw)

<h3>版權：</h3>
 MIT

<h3>最初開發日期：</h3>
 2024-07-12
 
<h3>使用方法：</h3>
<ul>
	<li>1. 框選螢幕想錄的範圍，正向或反向拖曳都可以</li>
	<li>2. 設定好 fps，通常大概只會選 30 或 60 吧</li>
	<li>3. 壓縮品質，與 png 壓縮品質有關，0 最清晰，建議設 1 或 2</li>
	<li>4. 要錄滑鼠指標嗎 可勾選</li>
	<li>5. 要錄系統聲音嗎 可勾選，並在「系統音源」下拉選單選擇正確音源</li>
	<li>6. 要錄麥克風嗎 可勾選，並在「麥克風」下拉選單選擇正確音源</li>
	<li>7. 如果換了音效裝置，按「重整音源」重新載入音源清單</li>
	<li>8. 按下開始錄影即開始</li>
	<li>9. 按下停止錄影後，程式會在背景完成收尾與影片、聲音合併轉檔</li>
	<li>10. 打開資料夾，影片會存在執行程式的 output 目錄</li>
</ul>
<h3>系統聲音注意事項：</h3>
<ul>
	<li>Windows 電腦若沒有「立體聲混音 / Stereo Mix」或其他可錄系統音的輸入裝置，可能無法直接錄系統聲音。</li>
	<li>找不到系統音源時，程式不會再自動改錄 device 0，會略過系統聲音，避免錄錯音源或錄到一半 crash。</li>
	<li>若需要錄系統聲音，可先到 Windows 音效設定啟用 Stereo Mix，或使用虛擬 loopback 音源。</li>
	<li>麥克風與系統音源建議錄影前先確認下拉選單選到正確裝置。</li>
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

<h3>開發驗證：</h3>
<pre>
python -m unittest tests.test_recorder_core -v
python -m py_compile my_cam_py.py recorder_core.py portalocker.py
python -c "import cv2, sounddevice, soundfile, moviepy, pydub, mss; print('imports ok')"
</pre>
	
<h3>編譯成exe：</h3>
	可詳見 build.bat
	如果不想執行時有視窗，可以加上 -w 參數
	
<h3>成果範例：</h3>
	https://github.com/shadowjohn/my_cam_py/tree/main/examples

<h3>更新歷程：</h3>
(2026-05-26) 穩定化分支：<br>
修正反向框選、frame queue、背景 thread 更新 UI、停止錄影非阻塞、音源選擇 UI、錄音失敗保護與暫存輸出忽略規則。<br>
	
(2024-07-14) v0.01 版：<br>
初版<br>
https://www.microsoft.com/en-us/wdsi/submission/3ed2b02f-bdb6-43b3-86ce-86acf056181e
		
<h3>Todo：</h3>
<ul>
	<li>實測長時間錄影與不同電腦音源組合</li>
	<li>可考慮加入音源設定記憶功能</li>
	<li>可考慮把錄影、錄音、轉檔流程拆成獨立模組</li>
</ul>

