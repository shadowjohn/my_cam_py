# Recorder Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make desktop recording stable across machines by fixing capture coordinates, frame buffering, UI thread updates, stop flow, audio device selection, and generated-file hygiene.

**Architecture:** Keep the current single-file Tkinter app shape, but extract pure helpers to `recorder_core.py` so critical behavior can be tested without launching the GUI. Use a bounded thread-safe queue for frames, route Tkinter updates through `root.after`, and make stop/merge flow run in background workers.

**Tech Stack:** Python 3.12, Tkinter, mss, OpenCV, sounddevice, soundfile, moviepy, pydub, unittest.

---

### Task 1: Capture Region And Frame Queue

**Files:**
- Create: `recorder_core.py`
- Create: `tests/test_recorder_core.py`
- Modify: `my_cam_py.py`
- Modify: `history.md`

- [ ] **Step 1: Write failing tests**

```python
import unittest

from recorder_core import FrameBuffer, normalize_record_area


class NormalizeRecordAreaTests(unittest.TestCase):
    def test_normalizes_reverse_drag(self):
        area = normalize_record_area(300, 220, 100, 80)
        self.assertEqual(area, {"left": 100, "top": 80, "right": 300, "bottom": 220, "width": 200, "height": 140})

    def test_rejects_zero_size_area(self):
        with self.assertRaises(ValueError):
            normalize_record_area(10, 20, 10, 80)


class FrameBufferTests(unittest.TestCase):
    def test_drops_oldest_frame_when_full(self):
        buffer = FrameBuffer(max_frames=2)
        buffer.put(1.0, "a")
        buffer.put(2.0, "b")
        buffer.put(3.0, "c")
        self.assertEqual(buffer.get(timeout=0.01), {"timestamp": 2.0, "frame": "b"})
        self.assertEqual(buffer.get(timeout=0.01), {"timestamp": 3.0, "frame": "c"})
        self.assertTrue(buffer.empty())
```

- [ ] **Step 2: Run test to verify red**

Run: `python -m unittest tests.test_recorder_core -v`

Expected: FAIL because `recorder_core` does not exist yet.

- [ ] **Step 3: Implement helpers and integrate**

Add `normalize_record_area(...)` and `FrameBuffer` in `recorder_core.py`. Import them in `my_cam_py.py`, store normalized area in `GDATA["capture_area"]`, and replace `frame_list` list usage with `FrameBuffer`.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m unittest tests.test_recorder_core -v
python -m py_compile my_cam_py.py recorder_core.py portalocker.py
```

Expected: tests pass and compile exits 0.

### Task 2: Tkinter-Safe UI Updates And Nonblocking Stop

**Files:**
- Modify: `my_cam_py.py`
- Modify: `history.md`

- [ ] **Step 1: Add UI scheduling helpers**

Create small helpers in `my_cam_py.py`: `ui_after(...)`, `ui_set_text(...)`, `ui_set_progress(...)`, `ui_set_widget_state(...)`, and use them in background threads.

- [ ] **Step 2: Make stop nonblocking**

Change `stop_recording()` so it flips `recording` to `False`, disables stop/start during shutdown, and starts `finish_recording()` in a background thread. `finish_recording()` joins workers, re-enables UI via `root.after`, and starts merge.

- [ ] **Step 3: Verify**

Run:

```powershell
python -m unittest tests.test_recorder_core -v
python -m py_compile my_cam_py.py recorder_core.py portalocker.py
```

Expected: tests pass and compile exits 0.

### Task 3: Audio Device Selection

**Files:**
- Modify: `my_cam_py.py`
- Modify: `history.md`

- [ ] **Step 1: Add device enumeration helpers**

Add a helper that returns input-capable devices from `sounddevice.query_devices()`, including index, name, hostapi, and channel count.

- [ ] **Step 2: Add UI dropdowns**

Add refreshable dropdowns for system audio and microphone. Keep keyword auto-selection for first launch, but do not silently fall back to device 0 when a requested type is unavailable.

- [ ] **Step 3: Harden recording errors**

Catch audio device open errors, record them into `GDATA["last_error"]`, and update UI through `root.after` instead of crashing worker threads silently.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m unittest tests.test_recorder_core -v
python -m py_compile my_cam_py.py recorder_core.py portalocker.py
```

Expected: tests pass and compile exits 0.

### Task 4: Generated File Hygiene

**Files:**
- Modify: `.gitignore`
- Modify: `history.md`

- [ ] **Step 1: Ignore transient recorder outputs**

Add ignore rules for `dist/output/`, `dist/*TEMP*`, temporary wav files, and temporary mp4 files while preserving tracked release artifacts.

- [ ] **Step 2: Verify git view**

Run:

```powershell
git status --short
git diff --stat
```

Expected: source changes are visible; transient `dist/output/` noise no longer dominates new status.
