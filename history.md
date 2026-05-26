# history.md

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
