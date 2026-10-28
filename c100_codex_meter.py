#!/usr/bin/env python3
"""Display Codex's five-hour remaining usage on a Keychron C100 RGB matrix."""

from __future__ import annotations

import argparse
import colorsys
import ctypes
import json
import random
import sys
import time
from ctypes import POINTER, Structure, c_char_p, c_int, c_ubyte, c_ushort, c_void_p, c_wchar_p
from datetime import datetime
from pathlib import Path


VID = 0x3434
PID = 0x042C
REPORT_BYTES = 32
CMD_KEYCHRON_RGB = 0xA8
PER_KEY_RGB_SET_COLOR = 0x0A
RANDOM_SEED = 0xC0D35
SESSION_ROOT = Path.home() / ".codex" / "sessions"


class HidDeviceInfo(Structure):
    pass


HidDeviceInfo._fields_ = [
    ("path", c_char_p),
    ("vendor_id", c_ushort),
    ("product_id", c_ushort),
    ("serial_number", c_wchar_p),
    ("release_number", c_ushort),
    ("manufacturer_string", c_wchar_p),
    ("product_string", c_wchar_p),
    ("usage_page", c_ushort),
    ("usage", c_ushort),
    ("interface_number", c_int),
    ("next", POINTER(HidDeviceInfo)),
    ("bus_type", c_int),
]


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def find_rate_limits(value: object) -> dict | None:
    if isinstance(value, dict):
        rate_limits = value.get("rate_limits")
        if isinstance(rate_limits, dict):
            return rate_limits
        for child in value.values():
            found = find_rate_limits(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_rate_limits(child)
            if found:
                return found
    return None


def latest_five_hour_usage() -> tuple[float, int | None, Path] | None:
    if not SESSION_ROOT.exists():
        return None
    files = sorted(SESSION_ROOT.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files[:30]:
        try:
            with path.open("rb") as handle:
                size = handle.seek(0, 2)
                handle.seek(max(0, size - 4 * 1024 * 1024))
                chunk = handle.read().decode("utf-8", errors="ignore")
        except OSError:
            continue

        for line in reversed(chunk.splitlines()):
            if "rate_limits" not in line:
                continue
            try:
                limits = find_rate_limits(json.loads(line))
            except json.JSONDecodeError:
                continue
            if not limits:
                continue
            primary = limits.get("primary")
            if not isinstance(primary, dict) or primary.get("window_minutes") != 300:
                continue
            used = primary.get("used_percent")
            if not isinstance(used, (int, float)):
                continue
            resets_at = primary.get("resets_at")
            return float(used), int(resets_at) if isinstance(resets_at, (int, float)) else None, path
    return None


def stable_random_order() -> list[int]:
    positions = list(range(100))
    random.Random(RANDOM_SEED).shuffle(positions)
    return positions


def physical_to_driver_index(position: int) -> int:
    row, column = divmod(position, 10)
    return (9 - column) * 10 + row


def parse_rgb(value: str) -> tuple[int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise argparse.ArgumentTypeError("颜色必须是 #RRGGBB")
    try:
        return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("颜色必须是 #RRGGBB") from exc


def rgb_to_hsv_bytes(rgb: tuple[int, int, int], brightness: int) -> tuple[int, int, int]:
    hue, saturation, _ = colorsys.rgb_to_hsv(*(channel / 255.0 for channel in rgb))
    return round(hue * 255) & 0xFF, round(saturation * 255), brightness


def colors_for_remaining(remaining: int, rgb: tuple[int, int, int], brightness: int) -> list[tuple[int, int, int]]:
    lit_positions = set(stable_random_order()[:remaining])
    on = rgb_to_hsv_bytes(rgb, brightness)
    driver_colors = [(0, 0, 0)] * 100
    for physical_position in lit_positions:
        driver_colors[physical_to_driver_index(physical_position)] = on
    return driver_colors


class HidApi:
    def __init__(self) -> None:
        candidates = [
            Path("/opt/homebrew/lib/libhidapi.dylib"),
            Path("/usr/local/lib/libhidapi.dylib"),
        ]
        library_path = next((path for path in candidates if path.exists()), None)
        if not library_path:
            raise RuntimeError("找不到 libhidapi，请执行 brew install hidapi")
        self.lib = ctypes.CDLL(str(library_path))
        self.lib.hid_init.restype = c_int
        self.lib.hid_enumerate.argtypes = [c_ushort, c_ushort]
        self.lib.hid_enumerate.restype = POINTER(HidDeviceInfo)
        self.lib.hid_free_enumeration.argtypes = [POINTER(HidDeviceInfo)]
        self.lib.hid_open_path.argtypes = [c_char_p]
        self.lib.hid_open_path.restype = c_void_p
        self.lib.hid_write.argtypes = [c_void_p, POINTER(c_ubyte), ctypes.c_size_t]
        self.lib.hid_write.restype = c_int
        self.lib.hid_read_timeout.argtypes = [c_void_p, POINTER(c_ubyte), ctypes.c_size_t, c_int]
        self.lib.hid_read_timeout.restype = c_int
        self.lib.hid_close.argtypes = [c_void_p]
        if self.lib.hid_init() != 0:
            raise RuntimeError("hidapi 初始化失败")

    def raw_hid_path(self) -> bytes | None:
        head = self.lib.hid_enumerate(VID, PID)
        current = head
        fallback = None
        try:
            while current:
                info = current.contents
                path = bytes(info.path) if info.path else None
                if path and info.usage_page == 0xFF60 and info.usage == 0x61:
                    return path
                if path and info.usage_page >= 0xFF00:
                    fallback = fallback or path
                current = info.next
        finally:
            if head:
                self.lib.hid_free_enumeration(head)
        return fallback

    def send_colors(self, colors: list[tuple[int, int, int]]) -> None:
        path = self.raw_hid_path()
        if not path:
            raise ConnectionError("未找到 C100 Raw HID（USB 3434:042C）")
        device = self.lib.hid_open_path(path)
        if not device:
            raise ConnectionError("无法打开 C100 Raw HID 接口")
        try:
            for start in range(0, 100, 9):
                count = min(9, 100 - start)
                payload = [CMD_KEYCHRON_RGB, PER_KEY_RGB_SET_COLOR, start, count]
                for hsv in colors[start : start + count]:
                    payload.extend(hsv)
                packet = (c_ubyte * (REPORT_BYTES + 1))()
                packet[0] = 0
                for index, value in enumerate(payload[:REPORT_BYTES], start=1):
                    packet[index] = value
                written = self.lib.hid_write(device, packet, len(packet))
                if written < 0:
                    raise ConnectionError("C100 Raw HID 写入失败")
                reply = (c_ubyte * REPORT_BYTES)()
                self.lib.hid_read_timeout(device, reply, REPORT_BYTES, 30)
        finally:
            self.lib.hid_close(device)


def remaining_from_usage(used_percent: float) -> int:
    return max(0, min(100, round(100.0 - used_percent)))


def format_reset(timestamp: int | None) -> str:
    if not timestamp:
        return "未知"
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")


def run(args: argparse.Namespace) -> int:
    hid = None if args.dry_run else HidApi()
    last_sent: int | None = None
    last_send_time = 0.0
    last_error = None

    while True:
        if args.percent is not None:
            remaining = args.percent
            source = None
            reset_at = None
            used = 100 - remaining
        else:
            status = latest_five_hour_usage()
            if status is None:
                message = "暂未在 Codex 会话中找到 5 小时限额数据"
                if message != last_error:
                    log(message)
                    last_error = message
                if args.once:
                    return 2
                time.sleep(args.interval)
                continue
            used, reset_at, source = status
            remaining = remaining_from_usage(used)

        now = time.monotonic()
        if remaining != last_sent or now - last_send_time >= args.resend:
            if args.dry_run:
                lit = [index for index, hsv in enumerate(colors_for_remaining(remaining, args.color, args.brightness)) if hsv[2]]
                log(f"剩余 {remaining}%，点亮 {len(lit)} 键，驱动灯号：{lit}")
                return 0
            try:
                assert hid is not None
                hid.send_colors(colors_for_remaining(remaining, args.color, args.brightness))
                source_text = ""
                log(f"已更新 C100：剩余 {remaining}% / 亮 {remaining} 键，5 小时窗口 {format_reset(reset_at)} 重置{source_text}")
                last_sent = remaining
                last_send_time = now
                last_error = None
            except ConnectionError as exc:
                message = str(exc)
                if message != last_error:
                    log(message)
                    last_error = message

        if args.once:
            return 0 if last_sent is not None else 3
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="用 C100 的 100 颗灯显示 Codex 5 小时剩余用量")
    parser.add_argument("--interval", type=float, default=15.0, help="检查间隔秒数，默认 15")
    parser.add_argument("--resend", type=float, default=60.0, help="即使数值不变也重发的秒数，默认 60")
    parser.add_argument("--color", type=parse_rgb, default=parse_rgb("#00C8FF"), help="亮灯颜色 #RRGGBB")
    parser.add_argument("--brightness", type=int, choices=range(1, 256), default=180, metavar="1-255")
    parser.add_argument("--once", action="store_true", help="更新一次后退出")
    parser.add_argument("--dry-run", action="store_true", help="只显示计算结果，不访问键盘")
    parser.add_argument("--percent", type=int, choices=range(0, 101), help="手动指定剩余百分比，便于测试")
    return parser


if __name__ == "__main__":
    try:
        raise SystemExit(run(build_parser().parse_args()))
    except KeyboardInterrupt:
        log("已停止")
        raise SystemExit(130)
