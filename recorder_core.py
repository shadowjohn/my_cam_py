import queue
from datetime import datetime
from pathlib import Path
import os
import json
import threading


NO_AUDIO_DEVICE_LABEL = "無可用輸入音源"
SYSTEM_AUDIO_KEYWORDS = ["立體聲混音", "Stereo Mix", "loopback"]
GENERIC_SYSTEM_AUDIO_NAMES = [
    "主要音效擷取驅動程式",
    "Primary Sound Capture Driver",
    "Microsoft 音效對應表 - Input",
    "Microsoft Sound Mapper - Input",
]

DEFAULT_APP_CONFIG = {
    "fps": 25,
    "compression_level": 2,
    "record_mouse": True,
    "record_system_sound": True,
    "record_mic_sound": False,
    "system_audio_device_name": "",
    "mic_audio_device_name": "",
}


def normalize_record_area(x1, y1, x2, y2):
    left = min(int(x1), int(x2))
    right = max(int(x1), int(x2))
    top = min(int(y1), int(y2))
    bottom = max(int(y1), int(y2))
    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        raise ValueError("record area width and height must be greater than zero")

    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": width,
        "height": height,
    }


class FrameBuffer:
    def __init__(self, max_frames=1800):
        self._queue = queue.Queue(maxsize=max_frames)
        self._max_frames = max_frames
        self._received_frames = 0
        self._dropped_frames = 0
        self._lock = threading.Lock()

    def put(self, timestamp, frame, **metadata):
        item = {"timestamp": timestamp, "frame": frame}
        item.update(metadata)
        try:
            self._queue.put_nowait(item)
            with self._lock:
                self._received_frames += 1
        except queue.Full:
            try:
                # 滿載時丟掉最舊 frame，避免長時間錄影把 RAM 撐爆。
                self._queue.get_nowait()
                with self._lock:
                    self._dropped_frames += 1
            except queue.Empty:
                pass
            self._queue.put_nowait(item)
            with self._lock:
                self._received_frames += 1

    def get(self, timeout=0.1):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def empty(self):
        return self._queue.empty()

    def clear(self):
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def stats(self):
        with self._lock:
            return {
                "max_frames": self._max_frames,
                "queued_frames": self._queue.qsize(),
                "received_frames": self._received_frames,
                "dropped_frames": self._dropped_frames,
            }


def calculate_frame_repetitions(time_diff, fps, max_gap_seconds=5.0):
    frame_step_time = 1 / float(fps)
    if time_diff < frame_step_time:
        return 0, False
    if time_diff > max_gap_seconds:
        # 系統時鐘跳動或 queue 大量丟幀時，不要補出幾十分鐘甚至幾小時的重複幀。
        return 1, True
    return max(1, int(time_diff / frame_step_time)), False


def should_abort_capture(consecutive_errors, fps, min_errors=10, max_error_seconds=3):
    threshold = max(int(min_errors), int(float(fps) * max_error_seconds))
    return int(consecutive_errors) >= threshold


def is_unsafe_capture_error(ex):
    error_text = str(ex).lower()
    return "getdibits" in error_text or "bitblt" in error_text


def get_input_audio_devices(devices, hostapis=None):
    input_devices = []
    hostapis = hostapis or []

    for index, device in enumerate(devices):
        max_input_channels = int(device.get("max_input_channels", 0))
        if max_input_channels <= 0:
            continue

        hostapi_name = ""
        hostapi_index = device.get("hostapi")
        if hostapi_index is not None and 0 <= hostapi_index < len(hostapis):
            hostapi_name = hostapis[hostapi_index].get("name", "")

        name = device.get("name", "")
        if hostapi_name:
            label = "%s: %s (%s, in:%s)" % (index, name, hostapi_name, max_input_channels)
        else:
            label = "%s: %s (in:%s)" % (index, name, max_input_channels)

        input_devices.append({
            "index": index,
            "name": name,
            "hostapi": hostapi_name,
            "max_input_channels": max_input_channels,
            "label": label,
        })

    return input_devices


def find_preferred_input_device(input_devices, keywords):
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for device in input_devices:
            if keyword_lower in device["name"].lower():
                return device
    return None


def is_generic_system_audio_name(device_name):
    device_name_lower = str(device_name).lower()
    for generic_name in GENERIC_SYSTEM_AUDIO_NAMES:
        if generic_name.lower() in device_name_lower:
            return True
    return False


def has_system_audio_keyword(device_name):
    device_name_lower = str(device_name).lower()
    for keyword in SYSTEM_AUDIO_KEYWORDS:
        if keyword.lower() in device_name_lower:
            return True
    return False


def parse_audio_device_index(selection):
    try:
        return int(str(selection).split(":", 1)[0])
    except (TypeError, ValueError):
        return None


def extract_audio_device_name(selection):
    text = str(selection)
    if ":" not in text:
        return ""
    name_part = text.split(":", 1)[1].strip()
    if " (" in name_part:
        return name_part.rsplit(" (", 1)[0].strip()
    return name_part


def select_audio_device_label(current_label, input_devices, keywords, saved_device_name="", allow_first=False):
    current_index = parse_audio_device_index(current_label)
    available_indexes = [device["index"] for device in input_devices]
    if current_index in available_indexes:
        return current_label

    if saved_device_name:
        for device in input_devices:
            if device["name"] == saved_device_name:
                return device["label"]

    preferred_device = find_preferred_input_device(input_devices, keywords)
    if preferred_device is not None:
        return preferred_device["label"]

    if allow_first and len(input_devices) > 0:
        return input_devices[0]["label"]
    return NO_AUDIO_DEVICE_LABEL


def select_system_audio_device_label(current_label, input_devices, saved_device_name=""):
    current_index = parse_audio_device_index(current_label)
    for device in input_devices:
        if device["index"] == current_index:
            if has_system_audio_keyword(device["name"]) or not is_generic_system_audio_name(device["name"]):
                return current_label

    preferred_device = find_preferred_input_device(input_devices, SYSTEM_AUDIO_KEYWORDS)
    if preferred_device is not None:
        return preferred_device["label"]

    if saved_device_name and not is_generic_system_audio_name(saved_device_name):
        for device in input_devices:
            if device["name"] == saved_device_name:
                return device["label"]

    return NO_AUDIO_DEVICE_LABEL


def get_recording_channels(input_devices, device_index, preferred_channels=2):
    for device in input_devices:
        if device["index"] == device_index:
            max_input_channels = int(device.get("max_input_channels", preferred_channels))
            return max(1, min(preferred_channels, max_input_channels))
    return preferred_channels


def select_default_audio_labels(input_devices, saved_system_device_name="", saved_mic_device_name=""):
    return {
        "system": select_system_audio_device_label(
            NO_AUDIO_DEVICE_LABEL,
            input_devices,
            saved_device_name=saved_system_device_name,
        ),
        "mic": select_audio_device_label(
            NO_AUDIO_DEVICE_LABEL,
            input_devices,
            ["麥克風", "Microphone", "USB PnP Sound Device", "Realtek HD Audio Mic input"],
            saved_device_name=saved_mic_device_name,
            allow_first=True,
        ),
    }


def normalize_app_config(config):
    normalized = DEFAULT_APP_CONFIG.copy()
    if isinstance(config, dict):
        normalized.update(config)

    try:
        normalized["fps"] = int(normalized["fps"])
    except (TypeError, ValueError):
        normalized["fps"] = DEFAULT_APP_CONFIG["fps"]
    if normalized["fps"] not in [15, 20, 25, 27, 30, 60]:
        normalized["fps"] = DEFAULT_APP_CONFIG["fps"]

    try:
        normalized["compression_level"] = int(normalized["compression_level"])
    except (TypeError, ValueError):
        normalized["compression_level"] = DEFAULT_APP_CONFIG["compression_level"]
    if normalized["compression_level"] < 0 or normalized["compression_level"] > 9:
        normalized["compression_level"] = DEFAULT_APP_CONFIG["compression_level"]

    for key in ["record_mouse", "record_system_sound", "record_mic_sound"]:
        normalized[key] = bool(normalized[key])

    for key in ["system_audio_device_name", "mic_audio_device_name"]:
        normalized[key] = str(normalized.get(key, "") or "")

    return normalized


def load_app_config(config_file):
    config_path = Path(config_file)
    if not config_path.is_file():
        return DEFAULT_APP_CONFIG.copy()
    try:
        with config_path.open("r", encoding="utf-8") as file:
            return normalize_app_config(json.load(file))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_APP_CONFIG.copy()


def save_app_config(config_file, config):
    config_path = Path(config_file)
    if config_path.parent:
        config_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_app_config(config)
    with config_path.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2)
    return normalized


def build_final_temp_path(output_file):
    output_path = Path(output_file)
    return str(output_path.with_name("%s_tmp_final%s" % (output_path.stem, output_path.suffix)))


def build_ffmpeg_fast_mux_command(ffmpeg_exe, video_file, audio_file, output_file):
    return [
        ffmpeg_exe,
        "-y",
        "-i", video_file,
        "-i", audio_file,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        output_file,
    ]


def build_explorer_select_args(file_path):
    return ["explorer.exe", "/select," + os.path.normpath(file_path)]


def safe_replace_file(temp_file, output_file):
    os.replace(temp_file, output_file)


def append_log(log_dir, category, message, exception=None, now=None):
    now = now or datetime.now()
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / ("%s.log" % now.strftime("%Y%m%d"))

    line = "[%s] [%s] %s" % (now.strftime("%Y-%m-%d %H:%M:%S"), category, message)
    if exception is not None:
        line += " | %s" % exception

    with log_file.open("a", encoding="utf-8") as file:
        file.write(line + "\n")

    return str(log_file)


def format_exception_for_log(ex):
    if ex is None:
        return ""
    return "%s: %s" % (ex.__class__.__name__, ex)
