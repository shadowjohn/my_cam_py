import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from recorder_core import (
    FrameBuffer,
    append_log,
    build_explorer_select_args,
    build_ffmpeg_fast_mux_command,
    build_final_temp_path,
    calculate_frame_repetitions,
    extract_audio_device_name,
    format_exception_for_log,
    find_preferred_input_device,
    get_input_audio_devices,
    get_recording_channels,
    is_unsafe_capture_error,
    load_app_config,
    normalize_record_area,
    parse_audio_device_index,
    safe_replace_file,
    save_app_config,
    select_audio_device_label,
    select_default_audio_labels,
    select_system_audio_device_label,
    should_abort_capture,
)


class NormalizeRecordAreaTests(unittest.TestCase):
    def test_normalizes_reverse_drag(self):
        area = normalize_record_area(300, 220, 100, 80)

        self.assertEqual(
            area,
            {
                "left": 100,
                "top": 80,
                "right": 300,
                "bottom": 220,
                "width": 200,
                "height": 140,
            },
        )

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

    def test_reports_queue_stats_and_dropped_frames(self):
        buffer = FrameBuffer(max_frames=2)

        buffer.put(1.0, "a")
        buffer.put(2.0, "b")
        buffer.put(3.0, "c")
        stats = buffer.stats()

        self.assertEqual(stats["max_frames"], 2)
        self.assertEqual(stats["queued_frames"], 2)
        self.assertEqual(stats["received_frames"], 3)
        self.assertEqual(stats["dropped_frames"], 1)

        buffer.get(timeout=0.01)
        self.assertEqual(buffer.stats()["queued_frames"], 1)

    def test_keeps_optional_frame_metadata(self):
        buffer = FrameBuffer(max_frames=2)

        buffer.put(1.0, "frame", cursor_position=(20, 30))

        self.assertEqual(
            buffer.get(timeout=0.01),
            {"timestamp": 1.0, "frame": "frame", "cursor_position": (20, 30)},
        )


class FrameTimingTests(unittest.TestCase):
    def test_calculates_normal_frame_repetitions(self):
        frame_times, is_anomaly = calculate_frame_repetitions(0.1, fps=30, max_gap_seconds=5)

        self.assertEqual(frame_times, 3)
        self.assertFalse(is_anomaly)

    def test_ignores_too_fast_frame(self):
        frame_times, is_anomaly = calculate_frame_repetitions(0.01, fps=30, max_gap_seconds=5)

        self.assertEqual(frame_times, 0)
        self.assertFalse(is_anomaly)

    def test_clamps_clock_jump_instead_of_generating_hours_of_frames(self):
        frame_times, is_anomaly = calculate_frame_repetitions(7200, fps=60, max_gap_seconds=5)

        self.assertEqual(frame_times, 1)
        self.assertTrue(is_anomaly)


class CaptureHealthTests(unittest.TestCase):
    def test_aborts_after_three_seconds_of_capture_errors(self):
        self.assertFalse(should_abort_capture(29, fps=10, min_errors=10, max_error_seconds=3))
        self.assertTrue(should_abort_capture(30, fps=10, min_errors=10, max_error_seconds=3))

    def test_treats_getdibits_as_unsafe_capture_error(self):
        self.assertTrue(is_unsafe_capture_error(Exception("gdi32.GetDIBits() failed.")))
        self.assertFalse(is_unsafe_capture_error(Exception("temporary busy")))


class AudioDeviceTests(unittest.TestCase):
    def test_lists_input_capable_devices_only(self):
        devices = [
            {"name": "Speaker", "hostapi": 0, "max_input_channels": 0},
            {"name": "Stereo Mix", "hostapi": 0, "max_input_channels": 2},
            {"name": "USB Mic", "hostapi": 1, "max_input_channels": 1},
        ]
        hostapis = [{"name": "MME"}, {"name": "Windows WASAPI"}]

        input_devices = get_input_audio_devices(devices, hostapis)

        self.assertEqual([device["index"] for device in input_devices], [1, 2])
        self.assertEqual(input_devices[0]["label"], "1: Stereo Mix (MME, in:2)")
        self.assertEqual(input_devices[1]["label"], "2: USB Mic (Windows WASAPI, in:1)")

    def test_finds_preferred_input_device_by_keyword(self):
        input_devices = [
            {"index": 1, "name": "Stereo Mix", "label": "1: Stereo Mix (MME, in:2)"},
            {"index": 2, "name": "USB PnP Sound Device", "label": "2: USB PnP Sound Device (MME, in:1)"},
        ]

        device = find_preferred_input_device(input_devices, ["麥克風", "USB PnP Sound Device"])

        self.assertEqual(device["index"], 2)

    def test_does_not_fallback_to_device_zero_when_no_keyword_matches(self):
        input_devices = [{"index": 0, "name": "Unknown Input", "label": "0: Unknown Input (MME, in:2)"}]

        self.assertIsNone(find_preferred_input_device(input_devices, ["Stereo Mix"]))

    def test_parses_device_index_from_label(self):
        self.assertEqual(parse_audio_device_index("12: USB Mic (MME, in:1)"), 12)
        self.assertIsNone(parse_audio_device_index("無可用輸入音源"))

    def test_extracts_device_name_from_label(self):
        self.assertEqual(extract_audio_device_name("12: USB Mic (MME, in:1)"), "USB Mic")
        self.assertEqual(extract_audio_device_name("無可用輸入音源"), "")

    def test_selects_saved_audio_device_by_name_when_index_changes(self):
        input_devices = [
            {"index": 9, "name": "USB Mic", "label": "9: USB Mic (MME, in:1)"},
            {"index": 11, "name": "Stereo Mix", "label": "11: Stereo Mix (MME, in:2)"},
        ]

        selected = select_audio_device_label(
            "1: Missing Old Mic (MME, in:1)",
            input_devices,
            ["Microphone"],
            saved_device_name="USB Mic",
            allow_first=False,
        )

        self.assertEqual(selected, "9: USB Mic (MME, in:1)")

    def test_selects_no_audio_when_system_device_not_found(self):
        input_devices = [{"index": 9, "name": "USB Mic", "label": "9: USB Mic (MME, in:1)"}]

        selected = select_audio_device_label(
            "無可用輸入音源",
            input_devices,
            ["Stereo Mix"],
            saved_device_name="Missing Stereo Mix",
            allow_first=False,
        )

        self.assertEqual(selected, "無可用輸入音源")

    def test_get_recording_channels_uses_device_limit(self):
        input_devices = [
            {"index": 9, "name": "USB Mic", "max_input_channels": 1},
            {"index": 11, "name": "Stereo Mix", "max_input_channels": 2},
        ]

        self.assertEqual(get_recording_channels(input_devices, 9), 1)
        self.assertEqual(get_recording_channels(input_devices, 11), 2)
        self.assertEqual(get_recording_channels(input_devices, 99), 2)

    def test_select_default_audio_labels_for_auto_test(self):
        input_devices = [
            {"index": 3, "name": "USB PnP Sound Device", "label": "3: USB PnP Sound Device (MME, in:1)"},
            {"index": 5, "name": "Stereo Mix", "label": "5: Stereo Mix (MME, in:2)"},
        ]

        labels = select_default_audio_labels(input_devices)

        self.assertEqual(labels["system"], "5: Stereo Mix (MME, in:2)")
        self.assertEqual(labels["mic"], "3: USB PnP Sound Device (MME, in:1)")

    def test_system_audio_ignores_generic_saved_driver_when_stereo_mix_exists(self):
        input_devices = [
            {"index": 7, "name": "主要音效擷取驅動程式", "label": "7: 主要音效擷取驅動程式 (Windows DirectSound, in:2)"},
            {"index": 9, "name": "立體聲混音 (Realtek High Definition Audio)", "label": "9: 立體聲混音 (Realtek High Definition Audio) (Windows DirectSound, in:2)"},
        ]

        selected = select_system_audio_device_label(
            "7: 主要音效擷取驅動程式 (Windows DirectSound, in:2)",
            input_devices,
            saved_device_name="主要音效擷取驅動程式",
        )

        self.assertEqual(selected, "9: 立體聲混音 (Realtek High Definition Audio) (Windows DirectSound, in:2)")


class OutputProtectionTests(unittest.TestCase):
    def test_builds_temp_output_path_next_to_final_file(self):
        temp_path = build_final_temp_path(r"D:\demo\output\123.mp4")

        self.assertEqual(temp_path, r"D:\demo\output\123_tmp_final.mp4")

    def test_safe_replace_file_replaces_final_after_success(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            final_file = root / "final.mp4"
            temp_file = root / "final_tmp_final.mp4"
            final_file.write_text("old", encoding="utf-8")
            temp_file.write_text("new", encoding="utf-8")

            safe_replace_file(str(temp_file), str(final_file))

            self.assertEqual(final_file.read_text(encoding="utf-8"), "new")
            self.assertFalse(temp_file.exists())

    def test_builds_ffmpeg_fast_mux_command_with_video_copy(self):
        command = build_ffmpeg_fast_mux_command(
            "ffmpeg.exe",
            r"D:\demo\video_tmp.mp4",
            r"D:\demo\audio.wav",
            r"D:\demo\final_tmp.mp4",
        )

        self.assertIn("-c:v", command)
        self.assertIn("copy", command)
        self.assertIn("-c:a", command)
        self.assertIn("aac", command)
        self.assertIn("-shortest", command)
        self.assertEqual(command[-1], r"D:\demo\final_tmp.mp4")

    def test_builds_explorer_select_args(self):
        args = build_explorer_select_args(r"D:\demo folder\final.mp4")

        self.assertEqual(args[0], "explorer.exe")
        self.assertTrue(args[1].startswith("/select,"))
        self.assertIn(r"D:\demo folder\final.mp4", args[1])


class LoggingTests(unittest.TestCase):
    def test_append_log_writes_date_log_with_category(self):
        with TemporaryDirectory() as temp_dir:
            log_file = append_log(
                temp_dir,
                "audio",
                "系統聲音錄音失敗",
                exception="device unavailable",
                now=datetime(2026, 5, 26, 9, 8, 7),
            )

            self.assertEqual(Path(log_file).name, "20260526.log")
            content = Path(log_file).read_text(encoding="utf-8")
            self.assertIn("[2026-05-26 09:08:07] [audio] 系統聲音錄音失敗 | device unavailable", content)

    def test_format_exception_for_log_includes_type(self):
        self.assertEqual(format_exception_for_log(ValueError("bad device")), "ValueError: bad device")


class AppConfigTests(unittest.TestCase):
    def test_load_missing_config_returns_defaults(self):
        with TemporaryDirectory() as temp_dir:
            config = load_app_config(str(Path(temp_dir) / "config.json"))

            self.assertEqual(config["fps"], 25)
            self.assertEqual(config["compression_level"], 2)
            self.assertTrue(config["record_mouse"])

    def test_save_and_load_config_roundtrip(self):
        with TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            save_app_config(str(config_file), {
                "fps": 60,
                "compression_level": 1,
                "record_mouse": False,
                "record_system_sound": True,
                "record_mic_sound": True,
                "system_audio_device_name": "Stereo Mix",
                "mic_audio_device_name": "USB Mic",
            })

            config = load_app_config(str(config_file))

            self.assertEqual(config["fps"], 60)
            self.assertEqual(config["compression_level"], 1)
            self.assertFalse(config["record_mouse"])
            self.assertEqual(config["system_audio_device_name"], "Stereo Mix")
            self.assertEqual(config["mic_audio_device_name"], "USB Mic")

    def test_load_invalid_config_returns_defaults(self):
        with TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text("{bad json", encoding="utf-8")

            config = load_app_config(str(config_file))

            self.assertEqual(config["fps"], 25)
            self.assertEqual(config["system_audio_device_name"], "")
