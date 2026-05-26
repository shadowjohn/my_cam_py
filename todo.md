# todo.md

## 下一輪建議

### P0：實錄穩定性

- [x] 輸出保護機制
  - 先輸出到 `xxx_tmp_final.mp4`，成功後再 rename 成正式檔。
  - 避免轉檔中斷時正式輸出檔不完整或消失。

- [x] 錯誤 log 檔
  - 建議寫入 `output/logs/YYYYMMDD.log`。
  - 記錄音源開啟失敗、mss grab 失敗、moviepy 轉檔失敗、thread exception。
  - 方便排查其他電腦抓不到系統音或麥克風的問題。

- [x] 實際錄影 smoke test checklist
  - 10 秒無聲錄影。
  - 10 秒麥克風。
  - 10 秒系統聲。
  - 10 秒系統聲 + 麥克風。
  - 反向框選。
  - 停止後馬上關閉程式。

### P1：音源相容性

- [x] 記住上次音源設定
  - 使用 `config.json` 保存 fps、壓縮品質、是否錄滑鼠、系統音源、麥克風音源。
  - 下次啟動自動選回同名裝置。

- [x] 音源可用性檢查
  - 開始錄影前快速 probe 選到的 device。
  - 失敗就提示並略過或要求重選，不等錄完才發現沒聲音。

- [ ] 系統聲音改善
  - 目前主要依賴 `Stereo Mix` / `立體聲混音` 類型輸入裝置。
  - 已先加入 `loopback` 關鍵字回選與錄音 channels 自動調整。
  - 後續可研究 WASAPI loopback 或虛擬音源支援，提升沒有 Stereo Mix 電腦的成功率。

### P2：效能與維護

- [x] 錄影 thread exception 收集
  - 將剩餘 `except: pass` 改成 `record_thread_error("video", ex)` 之類的集中記錄。
  - 不讓背景錯誤靜默消失。

- [x] frame queue 統計
  - 記錄 dropped frames、queue size、實際 FPS。
  - 長時間錄影卡頓時可判斷瓶頸在擷取、寫檔或轉檔。

- [ ] 拆模組
  - `recorder_core.py`：純邏輯。
  - `audio_devices.py`：音源列舉與選擇。
  - `recording_worker.py`：錄影與錄音 worker。
  - `ui_app.py`：Tkinter UI。
  - 目前已先把可測的設定、音源、queue、log、輸出保護邏輯集中到 `recorder_core.py`；完整拆 UI / worker 留待實錄壓測後再做。

## 建議優先做

1. 系統聲音 WASAPI loopback / 虛擬音源支援研究。
2. 實錄 smoke test 與長時間錄影壓測。
3. 完整拆分 UI / worker 模組。
