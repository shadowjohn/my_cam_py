# history.md

## 2026-05-26 停止後進度與快速合成

### 問題

- 停止錄影後，程式正在處理影片與合併聲音，但 UI 只顯示簡短文字，使用者不容易判斷目前卡在哪個階段。
- 完成後只顯示「轉檔完成」，沒有明確提示，也不會直接帶使用者到輸出檔。
- 原流程主要透過 MoviePy `write_videofile()` 重新輸出影片，即使只是把音訊放進已寫好的 mp4，也會逐 frame 重編碼，停止後等待感明顯。

### 已調整

- 停止錄影後新增分段進度：停止錄影、等待音訊收尾、收尾影像、寫入最後 frame、準備合成、合併聲音、快速合成、完成。
- 完成後會跳出「錄影完成」提示，並用檔案總管 `/select,` 直接選取輸出的 mp4。
- 無聲音時直接把暫存影片替換成正式輸出檔，避免不必要轉檔。
- 有聲音時優先使用 `imageio_ffmpeg` 提供的 ffmpeg，以 `-c:v copy -c:a aac -shortest -movflags +faststart` 快速封裝，避免重編碼影像。
- 同時錄系統聲與麥克風時仍先用 pydub 混成暫存 wav，再走 ffmpeg 快速封裝。
- ffmpeg 快速封裝失敗時，保留 MoviePy 慢速 fallback，並在 UI 顯示「快速合成失敗，改用慢速輸出」。

### 驗證

- 新增 ffmpeg fast mux command 與 Explorer select args unittest。
- `python -m unittest tests.test_recorder_core -v` 通過 29 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。
- 以 OpenCV 產生測試 mp4、soundfile 產生 wav，實際執行 ffmpeg fast mux，returncode 0 且輸出 mp4 產生。
- `build.bat` 已重新產生 `dist\my_cam_py.exe`，檔案版本確認為 0.02。
- 新版 exe 啟動後維持執行超過 6 秒，未因 `imageio_ffmpeg` 新 import 立刻 crash。

## 2026-05-26 P0 mss GDI access violation 修正

### 問題

- 實錄時仍會 crash，這次 `crash_20260526_231111.log` 顯示為 Windows fatal exception: access violation。
- faulthandler stack 指向 `mss\windows.py` 的 `_grab_impl()`，前一刻 log 已出現 `gdi32.GetDIBits() failed`。
- access violation 不是一般 Python exception，持續重試同一個 mss GDI 擷取流程會讓程式直接消失，導致 VideoWriter 沒機會 release，留下缺少 moov atom 的 `_tmp.mp4`。

### 已調整

- `mss.mss()` 改成固定 `with_cursor=False`，不再使用 mss 的 GDI 游標擷取路徑。
- 「錄滑鼠指標」改成在寫入 frame 前用 OpenCV 軟體 overlay 畫游標標記，保留使用者操作提示，同時避開 mss cursor path。
- 開始錄影前新增畫面擷取 preflight，擷取失敗時不啟動錄音/錄影 thread。
- 遇到 `GetDIBits` / `BitBlt` 類型錯誤時立即停止錄影並收尾，不再等連續 3 秒門檻，避免進一步觸發 access violation。
- `FrameBuffer.put()` 支援 frame metadata，供錄影 thread 傳遞 cursor position 給寫檔 thread。

### 驗證

- 新增 `is_unsafe_capture_error()` 與 frame metadata unittest。
- `python -m unittest tests.test_recorder_core -v` 通過 27 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。
- `build.bat` 已重新產生 `dist\my_cam_py.exe`，檔案版本確認為 0.02。
- 新版 exe 啟動後維持執行超過 6 秒，未立刻 crash；已確認純畫面 mss grab 可擷取 120x80 測試區域。
- 純畫面 `mss(compression_level=2, with_cursor=False)` 全螢幕 2560x1080 連續抓 6 秒完成 90 frames，未觸發 access violation。

## 2026-05-26 P0 Crash 可觀測性與擷取失敗保護

### 問題

- 實錄仍會 crash，且沒有提示、沒有明顯 log。
- 最新殘留檔顯示 `_tmp.mp4` 缺少 `moov atom`，代表 VideoWriter 沒正常 release；同時 log 出現 `gdi32.GetDIBits() failed`，顯示畫面擷取曾連續失敗。

### 已調整

- 程式啟動時即建立 `output/logs`，並安裝 crash handler。
- 新增 `crash_YYYYMMDD_HHMMSS.log` 與 `crash_YYYYMMDD.log`，記錄未捕捉例外、Tk callback 例外、thread traceback 與 fatal crash faulthandler。
- background worker 例外現在會額外寫完整 traceback 到 crash log。
- `process_frames()` 改成 `try/finally` 保證釋放 `VideoWriter`。
- 連續畫面擷取失敗達約 3 秒時，會主動停止錄影並進入收尾，避免產生無效 mp4。
- 若沒有任何影像 frame 可輸出，會明確停止轉檔並寫 log。

### 驗證

- 新增連續擷取失敗門檻 unittest。
- `python -m unittest tests.test_recorder_core -v` 通過 25 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 窄版錄影中狀態防截字

### 已調整

- 第三排「畫質壓縮(0不壓縮)」縮短為「壓縮」。
- 錄影中的 FPS / queue 狀態由 `FPS: ... | Queue: ... Drop: ...` 縮短為 `60fps Q0/360 D0`。
- FPS 狀態 Label 固定寬度，避免錄影時把右側文字擠出視窗。

## 2026-05-26 P0 影音不同步與系統聲修正

### 問題

- 實錄東京街頭 4K 時，不到 1 分鐘的錄影被輸出成 2 小時以上。
- 同次實錄沒有錄到系統聲音。

### 根本原因

- 影像 frame timestamp 使用 `time.time()`，若系統時鐘被 Windows/NTP 校時或發生跳動，`process_frames()` 會把異常時間差當成真實錄影時間，補出大量重複 frame。
- 系統聲音選擇會優先沿用上次儲存的泛用輸入裝置，例如「主要音效擷取驅動程式」，導致真正可錄系統聲的「立體聲混音 / Stereo Mix」被壓過。

### 已修正

- 錄影 frame timestamp 與 FPS 計算改用 `time.monotonic()`，避免受系統時鐘跳動影響。
- 新增 `calculate_frame_repetitions()`，若偵測到異常大的 frame 時間差，最多寫 1 frame 並重新同步，避免影片時長爆增。
- 新增系統音源選擇規則：泛用輸入裝置不再優先於「立體聲混音 / Stereo Mix / loopback」。
- 以目前 `dist/config.json` 的「主要音效擷取驅動程式」測試，新邏輯會改選「立體聲混音」。

### 驗證

- 新增 frame 時間跳動與系統音源選擇 unittest。
- `python -m unittest tests.test_recorder_core -v` 通過 24 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 版本升級到 0.02

### 已調整

- `my_cam_py.py` 顯示版本升級為 `0.02`。
- `metadata.txt` 的 FileVersion / ProductVersion 升級為 `0.02`。
- README 目前版本與 2026-05-26 更新歷程改為 `v0.02 穩定化版`。
- `build.bat` 已重新產生 `dist\my_cam_py.exe`，exe 檔案版本確認為 `0.02`。

### 驗證

- `python -m unittest tests.test_recorder_core -v` 通過 20 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。
- 新版 `dist\my_cam_py.exe` 啟動後維持執行超過 5 秒，未立刻 crash。

## 2026-05-26 緊致窄版音源展開 UI

### 已調整

- 視窗寬度收回 452，維持小工具的窄邊緊致感。
- 收合狀態維持 145 高度；音源展開時高度增加到 215，隱藏後自動縮回。
- 「錄滑鼠指標」、「錄系統聲音」、「錄麥克風」維持同一排。
- 「音源選擇」展開後改成上下兩行：第一行系統音源，第二行麥克風。
- 「重整音源」放在系統音源列右側，避免收合狀態擠壓主畫面。
- README 已同步更新音源展開方式。

### 驗證

- 以 Tk 最小版面量測確認主要按鈕列、錄製選項列、FPS 設定列與音源展開列都小於 452 寬度。
- `python -m unittest tests.test_recorder_core -v` 通過 20 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。
- `build.bat` 已重新產生 `dist\my_cam_py.exe`。
- 新版 `dist\my_cam_py.exe` 啟動後維持執行超過 5 秒，未立刻 crash。

## 2026-05-26 EXE 啟動字型錯誤修正

### 問題

- 執行 `dist\my_cam_py.exe` 時，Tkinter 建立 Button 失敗：`_tkinter.TclError: expected integer but got "JhengHei"`。
- 根本原因是 `root.option_add("*Font", "Microsoft JhengHei UI 9")` 會被 Tcl 拆成多個 token，導致字型大小位置讀到 `JhengHei`。

### 已修正

- 改成 Tcl list 可正確解析的字型格式：`{Microsoft JhengHei UI} 9`。
- 重新執行 `build.bat`，更新 `dist\my_cam_py.exe`。

### 驗證

- 最小 Tk repro 已確認舊格式會失敗、新格式可建立 Button。
- `python -m unittest tests.test_recorder_core -v` 通過 20 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。
- 新版 `dist\my_cam_py.exe` 啟動後維持執行超過 5 秒，未再出現 traceback。

## 2026-05-26 錄製控制 UI 微調

### 已調整

- 將「錄滑鼠指標」、「錄系統聲音」與「錄麥克風」集中到同一排，錄影前可直接切換。
- 第一排保留主要操作：選擇範圍、開始錄影、停止錄影、錄影資料夾、說明與離開。
- 縮短按鈕文字並統一按鈕寬度與列距，預設視窗高度由 165 壓到 145。
- 新增「自動測試」按鈕：重整音源後依偏好規則自動選系統聲與麥克風，並實際 probe 裝置，無法開啟的聲道會自動取消勾選。
- 新增「音源選項」收合按鈕：預設隱藏系統音源、麥克風下拉選單與「重整音源」，需要手動指定時再展開。
- 自動測試完成後會保存目前設定，並自動收起進階音源選項。
- README 已同步更新錄製選項與音源操作方式。

### 驗證

- `python -m unittest tests.test_recorder_core -v` 通過 20 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 專案評估

### 專案定位

`my_cam_py` 是 Windows 桌面錄影工具，使用 Python 3.12 + Tkinter 做 UI，透過 `mss` 擷取螢幕、OpenCV 寫入影像、sounddevice/soundfile 錄音，最後用 moviepy/pydub 合併輸出 mp4。

目前專案偏向單檔可執行工具，核心邏輯集中在 `my_cam_py.py`，搭配本機打包流程產生 exe。

### 目前結構

- `my_cam_py.py`：主程式，約 572 行；包含 UI、錄影、錄音、合併、檔案清理與流程控制。
- `mss/`：vendored mss，README 註明此版有微調 `base.py` 與 `windows.py`。
- `portalocker.py`：本機檔案鎖，防止程式重複啟動。
- `requirements.txt`：鎖定 OpenCV、sounddevice、soundfile、moviepy、pydub、pywin32、pyinstaller 等版本。
- `build.bat` / `my_cam_py.spec`：PyInstaller 打包設定，路徑固定到 `C:\Python312_64`。
- `dist/`、`release/`、`examples/`：含 exe、範例影片與目前產出的錄影檔。

### 已確認狀態

- Git 分支：`main...origin/main`，目前與遠端同分支。
- 目前有未追蹤輸出檔：
  - `dist/1758298468TEMP_MPY_wvf_snd.mp4`
  - `dist/output/`
  - `examples/1720893308.png`
- 最小語法驗證已通過：
  - `python -m py_compile my_cam_py.py portalocker.py`
  - `python -m py_compile mss\__init__.py mss\base.py mss\windows.py mss\factory.py mss\models.py mss\tools.py mss\screenshot.py mss\exception.py`
- 本次未啟動 GUI 實際錄影，僅做靜態檢查與語法編譯。

### 核心流程

1. 啟動後以 `lock.txt` 做單例鎖定。
2. Tkinter 建立工具列 UI，使用者框選錄影區域。
3. 開始錄影後建立 video / process / audio threads。
4. `record_video()` 用 `mss.grab()` 抓畫面，塞到 `GDATA["frame_list"]`。
5. `process_frames()` 從 `frame_list` 取 frame，以 OpenCV 寫入暫存 mp4。
6. 停止錄影後 join threads，再呼叫 `merge_audio_video()` 轉成最終 mp4。
7. 視是否錄系統聲 / 麥克風，用 pydub overlay 或 moviepy set_audio 合併。

### 主要風險與建議

1. 錄影區座標未正規化
   - 目前只檢查 `x1 == x2` 或 `y1 == y2`。
   - 若使用者由右往左、由下往上框選，`width` / `height` 會變負數，可能導致 mss / OpenCV 失敗。
   - 建議優先修：開始錄影前統一轉成 `left/top/right/bottom/width/height`。

2. `frame_list` 用 list 做跨執行緒佇列
   - `record_video()` append，`process_frames()` pop(0)，沒有 lock。
   - `pop(0)` 是 O(n)，長時間錄影或高 FPS 時容易增加 CPU 與記憶體壓力。
   - 建議改成 `queue.Queue(maxsize=...)` 或 `collections.deque`，並設計滿載策略。

3. Tkinter UI 從背景 thread 更新
   - `merge_audio_video()` 內的 worker thread 直接修改 progress label / progressbar。
   - Tkinter 不是 thread-safe，長時間轉檔時可能偶發 freeze 或 crash。
   - 建議用 `root.after(...)` 或 UI event queue 統一回主執行緒更新。

4. 停止錄影會卡 UI
   - `stop_recording()` 在 UI thread 直接 join audio/video/process threads。
   - 停止時若 frame backlog 很大，視窗會無回應。
   - 建議停止按鈕只切狀態，後續 drain / merge 放到背景流程，UI 顯示處理中。

5. 音源選擇偏硬編碼
   - 系統聲音以 `["立體聲混音", "Stereo Mix"]` 搜尋，找不到就 fallback 到 device 0。
   - 不同機器可能錄到錯誤裝置或直接失敗。
   - 建議 UI 顯示音源清單，保存上次選擇；fallback 時給明確提示。

6. 打包流程可用但綁機器
   - `build.bat` 與 spec 目前硬綁 `C:\Python312_64` 與 site-packages 路徑。
   - 以個人工具來說可接受；若要給別台機器維護，建議改成 venv 相對流程。

7. 產物與原始碼界線需要整理
   - repo 已追蹤 exe / release / 範例影片，且目前 `dist/output` 仍有未追蹤大量輸出。
   - 建議確認哪些是正式 release artifact，哪些只應忽略。
   - 可補 `.gitignore`：`/dist/output/`、`/dist/*TEMP*`、暫存 wav/mp4。

### 優先改善順序

1. 修錄影區座標正規化，避免反向框選直接壞掉。
2. 把 `frame_list` 改成 thread-safe queue/deque，降低長錄影風險。
3. 把 background thread 的 UI 更新改成 `root.after`。
4. 停止錄影改成非阻塞狀態流程。
5. 音源選擇 UI 化，避免不同電腦錄錯聲音。
6. 整理 `.gitignore` 與 release/dist 產物規則。

### 維護備註

- 本案是明確的單機 Windows 工具，優先保持低依賴與可打包。
- 不建議一開始大重構；先補穩定性漏洞，再抽離錄影、錄音、轉檔模組。
- 若要繼續修改，優先從 `my_cam_py.py` 的 `select_area()`、`start_recording()`、`record_video()`、`process_frames()`、`stop_recording()`、`merge_audio_video()` 這幾段下手。

## 2026-05-26 穩定化第一批

### 已調整

- 新增 `recorder_core.py`，抽出可測試的純邏輯。
- 新增 `normalize_record_area()`，開始錄影前會把反向框選正規化成 `left/top/right/bottom/width/height`。
- 新增 `FrameBuffer`，用 bounded thread-safe queue 取代跨執行緒共用 list。
- `record_video()` 改成將 frame 放入 queue；`process_frames()` 改成從 queue 讀取，不再使用 `pop(0)`。
- `start_recording()` 改成先驗證狀態與錄影範圍，再鎖 UI，避免未選範圍時 UI 被鎖住。

### 驗證

- `python -m unittest tests.test_recorder_core -v` 通過 3 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 穩定化第二批

### 已調整

- 新增 `ui_after()`、`ui_set_text()`、`ui_set_progress()`、`ui_set_widget_state()`，背景 thread 更新 UI 時統一透過 `root.after()` 回主執行緒。
- `record_video()` 不再直接呼叫 Tkinter 更新 FPS，改排程回主執行緒。
- `stop_recording()` 改成非阻塞：按下停止後只切狀態並啟動 `finish_recording()` 背景收尾，不在 UI thread 直接 join。
- `finish_recording()` 負責等待 audio/video/process threads 結束，再啟動轉檔。
- 轉檔流程加上失敗保護；若 `VideoFileClip` 或後續合併失敗，會記錄 `GDATA["last_error"]` 並恢復 UI。
- 開始錄影時把 UI checkbox / optionmenu 的值複製成一般 Python 值，背景 thread 不再直接讀 Tkinter variable。
- 關閉視窗時若仍在錄影或轉檔，改成設定「收尾後離開」，避免直接 destroy 導致暫存檔或輸出中斷。

### 驗證

- `python -m unittest tests.test_recorder_core -v` 通過 3 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 穩定化第三批

### 已調整

- `recorder_core.py` 新增音源純邏輯：
  - `get_input_audio_devices()`：只列出可錄音的 input devices。
  - `find_preferred_input_device()`：依關鍵字選取偏好音源。
  - `parse_audio_device_index()`：從 UI label 解析 device index。
- 新增 4 個音源測試，確認不會在找不到關鍵字時自動 fallback 到 device 0。
- Tkinter UI 新增「系統音源」與「麥克風」下拉選單，以及「重整音源」按鈕。
- 系統音源只在找到 `立體聲混音` / `Stereo Mix` 或使用者手動選定時啟用；找不到時會略過系統聲音，不再錄錯 device 0。
- 麥克風會優先選 `麥克風` / `Microphone` / `USB PnP Sound Device` / `Realtek HD Audio Mic input`，找不到時可由使用者手動選。
- 錄音 thread 開啟音源失敗時，會記錄 `GDATA["last_error"]`、更新 UI，並關閉該聲道，避免轉檔時因缺音檔 crash。

### 驗證

- `python -m unittest tests.test_recorder_core -v` 通過 7 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py` 通過。

## 2026-05-26 穩定化第四批

### 已調整

- `.gitignore` 新增 `dist/output/` 與 `dist/*TEMP*` 等暫存輸出規則。
- 保留既有 tracked `dist/my_cam_py.exe`、`release/v0.01/my_cam_py.exe` 與範例影片，不刪除正式產物。

### 驗證

- `git status --short` 不再列出 `dist/output/` 與 `dist/1758298468TEMP_MPY_wvf_snd.mp4`。

## 2026-05-26 收尾驗證

### 驗證結果

- `python -m unittest tests.test_recorder_core -v` 通過 7 tests。
- `python -m py_compile my_cam_py.py recorder_core.py portalocker.py mss\__init__.py mss\base.py mss\windows.py mss\factory.py mss\models.py mss\tools.py mss\screenshot.py mss\exception.py` 通過。
- `python -c "import cv2, sounddevice, soundfile, moviepy, pydub, mss; print('imports ok')"` 通過。
- 實機音源列舉測到 12 個 input devices，包含 `立體聲混音` 與 `Microphone (USB PnP Sound Device)`。
- 本次未啟動 GUI 實際錄影，避免在工作機產生新的錄影輸出。

### 環境補充

- 收尾驗證時發現 `C:\Python312_64` 缺少 `soundfile`，已依 `requirements.txt` 補安裝 `soundfile==0.12.1`。
- `pip` 仍顯示既有環境警告：`Ignoring invalid distribution ~ensorflow`，此警告與本次修改無關。

## 2026-05-26 README 更新

### 已調整

- 更新使用方法，補上音源下拉、重整音源、背景轉檔與反向框選支援。
- 新增系統聲音注意事項，說明 Stereo Mix / loopback 音源限制。
- 新增開發驗證指令與 2026-05-26 穩定化更新歷程。

## 2026-05-26 P0 實錄穩定性

### 已調整

- `recorder_core.py` 新增 `build_final_temp_path()`、`safe_replace_file()`、`append_log()`。
- 轉檔輸出改成先寫入 `*_tmp_final.mp4`，成功後再用 `os.replace()` 替換正式 mp4。
- 轉檔失敗時不覆蓋正式輸出檔，已捕捉的失敗會清掉半成品暫存檔。
- 新增 `output/logs/YYYYMMDD.log` 錯誤紀錄機制。
- 音源列舉、麥克風錄音、系統聲音錄音、畫面擷取、轉檔失敗與輸出完成都會寫 log。
- 畫面擷取錯誤不再完全靜默；第一筆與每 100 筆錯誤會寫入 log，避免高頻失敗時洗爆 log。
- 新增 `docs/smoke-test-checklist.md`，記錄實際錄影檢查清單。
- `todo.md` 已將 P0 三項標記完成，下一輪優先改成設定記憶、音源 probe 與 thread exception 收集。

### 驗證

- 新增安全輸出與 log 相關 unittest，測試數由 7 個增加到 10 個。

## 2026-05-26 P1 音源相容性

### 已調整

- 新增 `config.json` 設定記憶，保存 fps、壓縮品質、錄滑鼠、錄系統音、錄麥克風與上次音源名稱。
- 程式啟動時載入 `config.json`，UI 會套用上次設定。
- 音源下拉回選改用裝置名稱；USB 音源重插造成 index 改變時，仍會優先找同名裝置。
- 開始錄影前會保存目前設定。
- 開始錄影前新增音源 probe，先嘗試開啟已選的系統音源 / 麥克風。
- probe 失敗時會提示並略過該聲道，保留影片錄製。
- 錄音 channels 會依裝置 `max_input_channels` 自動取 1 或 2，避免單聲道 USB mic 被硬開 2 channels。
- `.gitignore` 新增 `/config.json` 與 `/dist/config.json`，避免個人音源設定進 repo。
- 系統音源偏好關鍵字補 `loopback`；真正 WASAPI loopback / 虛擬音源支援仍保留為後續研究。

### 驗證

- 新增 config、音源名稱回選與 recording channels 相關 unittest，測試數由 10 個增加到 17 個。

## 2026-05-26 P2 效能與維護

### 已調整

- `FrameBuffer` 新增統計：`max_frames`、`queued_frames`、`received_frames`、`dropped_frames`。
- frame queue 滿載丟幀時會累計 dropped frames。
- FPS 顯示新增 queue / drop 統計：`FPS: ... | Queue: n/max Drop: n`。
- dropped frames 增加時會寫入 `output/logs/YYYYMMDD.log`，方便長時間錄影後判斷瓶頸。
- 新增 `format_exception_for_log()`，log 會包含 exception 類型，例如 `ValueError: ...`。
- 新增 `create_worker_thread()`，統一包住 video / process / audio / finish / merge worker。
- worker thread 發生未預期例外時會寫 log、停止錄影，並嘗試進入收尾流程，避免背景 crash 後 UI 卡住。
- 更新 `docs/smoke-test-checklist.md`，補 queue/drop 與長時間錄影 log 檢查項目。
- 完整 UI / worker 模組拆分暫不硬做；目前先把可測邏輯集中到 `recorder_core.py`，避免在穩定化分支一次大拆造成新風險。

### 驗證

- 新增 frame queue 統計與 exception 格式相關 unittest，測試數由 17 個增加到 19 個。
