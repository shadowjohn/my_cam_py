import queue


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

    def put(self, timestamp, frame):
        item = {"timestamp": timestamp, "frame": frame}
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            try:
                # 滿載時丟掉最舊 frame，避免長時間錄影把 RAM 撐爆。
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(item)

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


def parse_audio_device_index(selection):
    try:
        return int(str(selection).split(":", 1)[0])
    except (TypeError, ValueError):
        return None
