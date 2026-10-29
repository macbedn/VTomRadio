#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import math
import sys
import threading
import time
import zipfile
import http.client
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

APP_VERSION = "0.6.0"
RESTORE_CHUNK_SIZES = (256, 192, 128, 96)
RESTORE_INTER_CHUNK_DELAY = 0.003
WRITE_DATA_TIMEOUT_RESTORE = 5.0
MAX_AUTO_RETRIES = 1
DEFAULT_SPIFFS_CAPACITY_KB = 896
READ_FILE_RETRIES = 1
TRANSIENT_UPLOAD_RETRIES = 4
DELETE_RETRIES = 2
RESTORE_UPLOAD_ATTEMPT_CHUNKS = (4096, 2048, 1460, 1024)
RESTORE_FILE_SETTLE_DELAY = 0.06
RESTORE_RECOVERY_TIMEOUT = 20.0
AUTO_RESUME_AFTER_RESTORE = True
FS_PROFILE_CHOICES = (
    ("myradio_896", "myRadio / 896 KB", 896),
    ("vtomradio_yoradio_16mb_3904", "VTomRadio LittleFS 3.8 MB", 3904),
    ("generic_1024", "Általános / 1 MB", 1024),
    ("generic_1536", "Általános / 1.5 MB", 1536),
    ("generic_2048", "Általános / 2 MB", 2048),
    ("generic_4096", "Általános / 4 MB", 4096),
    ("custom", "Egyedi", None),
    ("auto", "Automatikus", None),
)
FS_SAFETY_FLOOR_BYTES = 96 * 1024


TEXT = {
    "HU": {
        "title": "LittleFS-SPIFFS Partition Manager",
        "radio_ip": "Rádió IP",
        "wifi_connected": "WiFi kapcsolat aktív.",
        "connect": "Kapcsolódás",
        "backup": "Teljes mentés (ZIP)",
        "backup_verify": "Mentés ellenőrzése",
        "restore": "Mentés visszaállítása",
        "list": "Fájllista frissítése",
        "delete": "Kijelölt törlése",
        "upload_files": "Fájlok várósorba",
        "upload_folder": "Mappa várósorba",
        "download": "Kijelölt mentése",
        "reboot": "Rádió újraindítása",
        "lang": "Nyelv: HU / EN",
        "spiffs_capacity": "Partíció méret",
        "set_spiffs_capacity": "Partíció méret profil",
        "spiffs_capacity_prompt": "Válassz partíció profilt, vagy adj meg egyedi teljes méretet KB-ban.",
        "spiffs_capacity_disabled": "Partíció méret helyellenőrzés: automatikus (ha elérhető)",
        "spiffs_capacity_set": "Partíció méret profil aktív: {name} ({value} KB)",
        "spiffs_capacity_custom": "Egyedi Partíció méret méret KB-ban:",
        "fs_estimate_unknown": "Partíció méret: nincs adat",
        "fs_estimate_ok": "Partíció méret: {profile} | Teljes {total}, foglalt {used}, szabad {free} | Várósor {queue} - elfér",
        "fs_estimate_low": "Partíció méret: {profile} | Teljes {total}, foglalt {used}, szabad {free} | Várósor {queue} - kevés tartalék",
        "fs_estimate_full": "Partíció méret: {profile} | Teljes {total}, foglalt {used}, szabad {free} | Várósor {queue} - nem fér el",
        "space_check_insufficient": "Kevés a becsült szabad hely.\n\nBecsült szabad hely: {free}\nVárósor mérete: {need}\n\nFeltöltés megszakítva.",
        "space_check_low": "Kevés a becsült szabad hely.\n\nBecsült szabad hely: {free}\nVárósor mérete: {need}\n\nA feltöltés még elindítható, de nagy az open_failed hiba esélye.\nFolytatod?",
        "critical_spiffs_write_error": "Kritikus fájlrendszer írási hiba, a várósor leállítva.",
        "open_failed_hint": "A rádió nem tudta megnyitni a célfájlt írásra. Ez általában kevés vagy töredezett fájlrendszer szabad helyre utal.",
        "tree": "A rádió fájlrendszer tartalma",
        "type": "Típus",
        "size": "Méret",
        "modified": "Dátum",
        "root": "gyökér",
        "status_ready": "Készen.",
        "status_connecting": "Kapcsolódás folyamatban...",
        "status_connect_cancelled": "Kapcsolódás megszakítva.",
        "status_maintenance": "Karbantartó mód indítása...",
        "status_listing": "Fájllista frissítése...",
        "status_saving": "Mentés folyamatban...",
        "status_restoring": "Visszaállítás folyamatban...",
        "status_verifying": "Ellenőrzés folyamatban...",
        "status_uploading": "Feltöltés folyamatban...",
        "status_deleting": "Törlés folyamatban...",
        "status_downloading": "Mentés a számítógépre...",
        "status_rebooting": "Újraindítás kérése...",
        "target_folder": "célmappa",
        "mkdir": "Mappa létrehozása",
        "enter_dir_name": "Add meg az új mappa nevét:",
        "mkdir_done": "Mappa sikeresen létrehozva.",
        "status_mkdir": "Mappa létrehozása...",
        "connect_first": "Előbb csatlakozz a rádióhoz.",
        "error": "Hiba",
        "warning": "Figyelmeztetés",
        "done": "Kész",
        "saved": "Mentve",
        "maintenance_ok": "Karbantartó mód aktív.",
        "tree_no_selection": "Jelölj ki egy fájlt vagy mappát.",
        "download_select_file": "A mentéshez jelölj ki egy fájlt.",
        "root_delete_blocked": "A gyökér bejegyzés nem törölhető. Jelölj ki konkrét fájlokat vagy mappákat.",
        "delete_confirm": "Biztosan törlöd a kijelölt elemeket?\n\nKijelölt elemek: {count}\n{items}\n\nA művelet nem visszavonható.",
        "backup_done": "A teljes mentés elkészült.",
        "backup_verified": "A teljes mentés elkészült és ellenőrizve.",
        "backup_verify_failed": "A mentés ellenőrzése sikertelen: {path}",
        "restore_done": "A visszaállítás elkészült.",
        "download_done": "A kijelölt fájl mentése elkészült.",
        "upload_done": "A feltöltés elkészült.",
        "delete_done": "A törlés elkészült.",
        "reboot_done": "Az újraindítás kérése elküldve.",
        "connect_cancel": "Megszakítás",
        "no_files": "Nincs fájl a rádión.",
        "empty_folder": "A kiválasztott mappa üres.",
        "folder": "mappa",
        "file": "fájl",
        "queue": "Feltöltési várósor",
        "queue_name": "Név",
        "queue_target": "Cél",
        "queue_status": "Állapot",
        "queue_progress": "Folyamat",
        "queue_size": "Méret",
        "queue_add_files": "Fájlok hozzáadása",
        "queue_add_folder": "Mappa hozzáadása",
        "queue_start": "Várósor indítása",
        "queue_cancel": "Megszakítás",
        "queue_retry": "Hibásak újra",
        "queue_remove": "Kijelölt eltávolítása",
        "queue_clear_done": "Készek törlése",
        "queue_idle": "A várósor üres.",
        "queue_waiting": "Várakozik",
        "queue_uploading": "Feltöltés",
        "queue_done": "Kész",
        "queue_failed": "Hibás",
        "queue_cancelled": "Megszakítva",
        "queue_retrying": "Újrapróba",
        "queue_running": "A várósor fut.",
        "queue_added": "A fájlok bekerültek a várósorba.",
        "queue_cancel_requested": "Megszakítás kérve...",
        "queue_finished": "Várósor kész.",
        "queue_empty_start": "Nincs feltöltendő elem a várósorban.",
        "queue_file": "Aktuális fájl",
        "queue_overall": "Összesen",
        "queue_speed": "Sebesség",
        "queue_eta": "Hátralévő idő",
        "queue_index": "Fájl",
        "queue_failures": "Hibák",
        "queue_cancelled_done": "A várósor megszakadt.",
        "last_step": "Utolsó művelet",
        "save_selected_title": "Fájl mentése",
        "save_backup_title": "Mentés mentése ZIP fájlba",
        "open_backup_title": "Mentés kiválasztása",
        "footer": "2026 © gidano",
    },
    "EN": {
        "title": "LittleFS-SPIFFS Partition Manager",
        "radio_ip": "Radio IP",
        "wifi_connected": "WiFi connection is active.",
        "connect": "Connect",
        "backup": "Full backup (ZIP)",
        "backup_verify": "Verify backup",
        "restore": "Restore backup",
        "list": "Refresh file list",
        "delete": "Delete selected",
        "upload_files": "Add files to queue",
        "upload_folder": "Add folder to queue",
        "download": "Save selected",
        "reboot": "Reboot radio",
        "lang": "Language: HU / EN",
        "spiffs_capacity": "Partition size",
        "set_spiffs_capacity": "Partition size profile",
        "spiffs_capacity_prompt": "Choose an estimated filesystem profile, or enter a custom total size in KB.",
        "spiffs_capacity_disabled": "Partition size space check: automatic (if available)",
        "spiffs_capacity_set": "Partition size profile active: {name} ({value} KB)",
        "spiffs_capacity_custom": "Custom Partition size in KB:",
        "fs_estimate_unknown": "Partition size: no data",
        "fs_estimate_ok": "Partition size: {profile} | Total {total}, used {used}, free {free} | Queue {queue} - fits",
        "fs_estimate_low": "Partition size: {profile} | Total {total}, used {used}, free {free} | Queue {queue} - low reserve",
        "fs_estimate_full": "Partition size: {profile} | Total {total}, used {used}, free {free} | Queue {queue} - does not fit",
        "space_check_insufficient": "Estimated free space is too low.\n\nEstimated free space: {free}\nQueue size: {need}\n\nUpload aborted.",
        "space_check_low": "Estimated free space is low.\n\nEstimated free space: {free}\nQueue size: {need}\n\nUpload can still be started, but open_failed errors are likely.\nContinue?",
        "critical_spiffs_write_error": "Critical filesystem write error, queue stopped.",
        "open_failed_hint": "The radio could not open the target file for writing. This usually points to low or fragmented filesystem free space.",
        "tree": "Radio filesystem contents",
        "type": "Type",
        "size": "Size",
        "modified": "Date",
        "root": "root",
        "status_ready": "Ready.",
        "status_connecting": "Connecting...",
        "status_connect_cancelled": "Connection cancelled.",
        "status_maintenance": "Starting maintenance mode...",
        "status_listing": "Refreshing file list...",
        "status_saving": "Saving backup...",
        "status_restoring": "Restoring backup...",
        "status_verifying": "Verifying...",
        "status_uploading": "Uploading...",
        "status_deleting": "Deleting...",
        "status_downloading": "Saving to computer...",
        "status_rebooting": "Requesting reboot...",
        "target_folder": "target folder",
        "mkdir": "Create directory",
        "enter_dir_name": "Enter directory name:",
        "mkdir_done": "Directory created successfully.",
        "status_mkdir": "Creating directory...",
        "connect_first": "Connect to the radio first.",
        "error": "Error",
        "warning": "Warning",
        "done": "Done",
        "saved": "Saved",
        "maintenance_ok": "Maintenance mode is active.",
        "tree_no_selection": "Select a file or folder.",
        "download_select_file": "Select a file to save.",
        "root_delete_blocked": "The root entry cannot be deleted. Select specific files or folders.",
        "delete_confirm": "Are you sure you want to delete the selected items?\n\nSelected items: {count}\n{items}\n\nThis action cannot be undone.",
        "backup_done": "Full backup completed.",
        "backup_verified": "Full backup completed and verified.",
        "backup_verify_failed": "Backup verification failed: {path}",
        "restore_done": "Restore completed.",
        "download_done": "Selected file saved.",
        "upload_done": "Upload completed.",
        "delete_done": "Delete completed.",
        "reboot_done": "Reboot requested.",
        "connect_cancel": "Cancel",
        "no_files": "There are no files on the radio.",
        "empty_folder": "The selected folder is empty.",
        "folder": "folder",
        "file": "file",
        "queue": "Upload queue",
        "queue_name": "Name",
        "queue_target": "Target",
        "queue_status": "Status",
        "queue_progress": "Progress",
        "queue_size": "Size",
        "queue_add_files": "Add files",
        "queue_add_folder": "Add folder",
        "queue_start": "Start queue",
        "queue_cancel": "Cancel",
        "queue_retry": "Retry failed",
        "queue_remove": "Remove selected",
        "queue_clear_done": "Clear completed",
        "queue_idle": "The queue is empty.",
        "queue_waiting": "Waiting",
        "queue_uploading": "Uploading",
        "queue_done": "Done",
        "queue_failed": "Failed",
        "queue_cancelled": "Cancelled",
        "queue_retrying": "Retrying",
        "queue_running": "The queue is running.",
        "queue_added": "Files added to queue.",
        "queue_cancel_requested": "Cancel requested...",
        "queue_finished": "Queue finished.",
        "queue_empty_start": "There is nothing in the upload queue.",
        "queue_file": "Current file",
        "queue_overall": "Overall",
        "queue_speed": "Speed",
        "queue_eta": "ETA",
        "queue_index": "File",
        "queue_failures": "Failures",
        "queue_cancelled_done": "Queue cancelled.",
        "last_step": "Last step",
        "save_selected_title": "Save file",
        "save_backup_title": "Save backup ZIP",
        "open_backup_title": "Choose backup ZIP",
        "footer": "2026 © gidano",
    },
}


def normalize_remote_path(path: str) -> str:
    path = (path or "").replace("\\", "/")
    while "//" in path:
        path = path.replace("//", "/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def format_eta(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds == float("inf"):
        return "--:--"
    sec = int(seconds)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def human_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec <= 0:
        return "0 KB/s"
    kb = bytes_per_sec / 1024.0
    if kb < 1024:
        return f"{kb:.1f} KB/s"
    return f"{kb / 1024.0:.2f} MB/s"


def fmt_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB"):
        if value < 1024 or unit == "MB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def fmt_mtime(epoch_seconds: int | None) -> str:
    if not epoch_seconds:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(epoch_seconds)))
    except Exception:
        return ""




def parse_positive_int_or_none(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    number = int(digits)
    return number if number > 0 else None


def is_probable_spiffs_open_failed(error_text: str) -> bool:
    msg = (error_text or "").lower()
    return "open_failed" in msg or ("write_begin" in msg and "open" in msg and "failed" in msg)


def build_open_failed_hint(base_error: str, localized_hint: str) -> str:
    base_error = (base_error or "").strip()
    if not base_error:
        return localized_hint
    if localized_hint in base_error:
        return base_error
    return f"{base_error} | {localized_hint}"


def is_probable_transient_upload_disconnect(error_text: str) -> bool:
    msg = (error_text or "").lower()
    transient_tokens = (
        "winerror 10060",
        "winerror 10054",
        "kapcsolódási kísérlet nem sikerült",
        "did not properly respond",
        "forcibly closed",
        "connection reset",
        "reset by peer",
        "timed out",
        "timeout",
    )
    return any(token in msg for token in transient_tokens)


def set_windows_app_id():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gidano.myRadio.FS.Kezelo")
    except Exception:
        pass


def get_app_icon_path() -> str | None:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "icon.ico")
    try:
        candidates.append(Path(sys.executable).resolve().parent / "icon.ico")
    except Exception:
        pass
    try:
        candidates.append(Path(__file__).resolve().parent / "icon.ico")
    except Exception:
        pass
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def is_windows_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False


def apply_dark_title_bar(window):
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        for attr in (20, 19):
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), ctypes.sizeof(value))
            except Exception:
                pass
    except Exception:
        pass


def apply_theme(root: tk.Tk, dark: bool):
    style = ttk.Style(root)
    if dark:
        try:
            style.theme_use("clam")
        except Exception:
            pass
        bg = "#1e1e1e"
        panel = "#252526"
        fg = "#ffffff"
        edge = "#6f6f6f"
        select = "#3a3d41"
        root.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=panel, foreground=fg, bordercolor=edge, focusthickness=1, focuscolor=edge)
        style.map("TButton", background=[("active", "#2f3136"), ("pressed", "#2a2d31")], foreground=[("disabled", "#8a8a8a")])
        style.configure("TCombobox", fieldbackground=panel, background=panel, foreground=fg, arrowcolor=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.map("TCombobox", fieldbackground=[("readonly", panel)], selectbackground=[("readonly", select)], selectforeground=[("readonly", fg)])
        # Make normal text entry fields readable in Windows dark mode too.
        # Without this, ttk.Entry may keep a light fieldbackground while the text
        # foreground is inherited as white, which makes the radio IP invisible.
        style.configure("TEntry", fieldbackground=panel, background=panel, foreground=fg, insertcolor=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.map("TEntry", fieldbackground=[("focus", panel), ("!disabled", panel)], foreground=[("!disabled", fg)])
        style.configure("Treeview", background=panel, fieldbackground=panel, foreground=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.configure("Treeview.Heading", background="#2d2d30", foreground=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.map("Treeview", background=[("selected", select)], foreground=[("selected", fg)])
        style.map("Treeview.Heading", background=[("active", "#383b40")])
        style.configure("Horizontal.TProgressbar", troughcolor=panel, background="#6aa2ff", bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.configure("Vertical.TScrollbar", background=panel, troughcolor=bg, arrowcolor=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
        style.configure("Horizontal.TScrollbar", background=panel, troughcolor=bg, arrowcolor=fg, bordercolor=edge, lightcolor=edge, darkcolor=edge)
    else:
        try:
            style.theme_use("vista")
        except Exception:
            pass


class ProtoError(RuntimeError):
    pass


class UserCancelled(RuntimeError):
    pass


@dataclass
class RemoteFile:
    path: str
    size: int
    is_dir: bool = False
    modified_ts: int | None = None


@dataclass
class UploadTask:
    local_path: Path
    remote_path: str
    size: int
    status: str = "waiting"
    progress_pct: float = 0.0
    uploaded_bytes: int = 0
    retries_done: int = 0
    max_retries: int = MAX_AUTO_RETRIES
    error: str = ""
    task_id: str = field(default_factory=lambda: f"task-{time.time_ns()}")


class HttpSpiFFSClient:
    def __init__(self):
        self.base_url = ""
        self.connected = False
        self.debug_lines: list[str] = []
        self.fs_info_cache: dict[str, int | str] | None = None

    @property
    def ser(self):
        # Compatibility with old GUI checks. WiFi mode has no serial port.
        return self if self.connected else None

    def connect(self, host: str, timeout: float = 15.0, cancel_event: threading.Event | None = None):
        host = (host or "").strip()
        if not host:
            raise ProtoError("missing radio IP")
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host
        self.base_url = host.rstrip("/")
        deadline = time.time() + max(2.0, timeout)
        last_error: Exception | None = None
        # Use short connect slices so user cancellation can interrupt quickly.
        while time.time() < deadline:
            if cancel_event and cancel_event.is_set():
                raise UserCancelled("connect cancelled")
            remaining = max(0.5, deadline - time.time())
            try:
                self._request("GET", "/api/fs/ping", timeout=min(2.5, remaining))
                self.connected = True
                return
            except Exception as e:
                last_error = e

            if cancel_event and cancel_event.is_set():
                raise UserCancelled("connect cancelled")

            # Older firmwares may miss /api/fs/ping; fallback with short LIST probe.
            try:
                self._request("GET", "/api/fs/list", timeout=min(3.0, remaining))
                self.connected = True
                return
            except Exception as e:
                last_error = e

            time.sleep(0.25)

        if cancel_event and cancel_event.is_set():
            raise UserCancelled("connect cancelled")
        raise ProtoError(str(last_error) if last_error else "connect timeout")

    def disconnect(self):
        self.connected = False

    def ping(self):
        try:
            self._request("GET", "/api/fs/ping", timeout=5.0)
        except ProtoError:
            self._request("GET", "/api/fs/list", timeout=15.0)
        return True

    def begin_maintenance(self):
        # WiFi mode talks to the normal webserver. No serial maintenance window needed.
        return True

    def abort_write(self):
        return True

    def mkdir(self, path: str):
        path = normalize_remote_path(path)
        self._post_form("/api/fs/mkdir", {"path": path})

    def rmdir(self, path: str):
        path = normalize_remote_path(path)
        last_error: Exception | None = None
        for attempt in range(DELETE_RETRIES + 1):
            try:
                self._post_form("/api/fs/rmdir", {"path": path}, timeout=90.0)
                return
            except Exception as e:
                last_error = e
                if attempt < DELETE_RETRIES and is_probable_transient_upload_disconnect(str(e)):
                    time.sleep(0.35 * (attempt + 1))
                    continue
                raise
        if last_error:
            raise last_error

    def delete_file(self, path: str):
        path = normalize_remote_path(path)
        last_error: Exception | None = None
        for attempt in range(DELETE_RETRIES + 1):
            try:
                self._post_form("/api/fs/delete", {"path": path}, timeout=90.0)
                return
            except Exception as e:
                last_error = e
                if attempt < DELETE_RETRIES and is_probable_transient_upload_disconnect(str(e)):
                    time.sleep(0.35 * (attempt + 1))
                    continue
                raise
        if last_error:
            raise last_error

    def reboot(self):
        self._request("POST", "/api/reboot", data=b"", headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=5.0)
        self.connected = False

    def get_fs_info(self) -> dict[str, int | str] | None:
        try:
            raw = self._request("GET", "/api/fs/info", timeout=10.0)
        except ProtoError:
            return None

        try:
            info = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return None

        if not isinstance(info, dict) or not info.get("ok"):
            return None

        try:
            total = int(info.get("total", 0) or 0)
            used = int(info.get("used", 0) or 0)
            free = int(info.get("free", 0) or 0)
        except Exception:
            return None

        if total <= 0:
            return None

        backend = str(info.get("backend", "")).strip().lower() or "unknown"
        parsed = {
            "backend": backend,
            "total": total,
            "used": max(0, used),
            "free": max(0, free),
        }
        self.fs_info_cache = parsed
        return parsed

    def list_files(self) -> list[RemoteFile]:
        raw = self._request("GET", "/api/fs/list", timeout=45.0)
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception as e:
            raise ProtoError(f"bad WiFi LIST reply: {e}")
        files: list[RemoteFile] = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                path = item.get("path") or item.get("name") or ""
                if not path:
                    continue
                is_dir = bool(item.get("dir") or item.get("is_dir") or item.get("type") == "dir")
                try:
                    size = int(item.get("size", 0) or 0)
                except Exception:
                    size = 0
                raw_mtime = item.get("mtime", item.get("modified", item.get("last_write", item.get("timestamp"))))
                try:
                    modified_ts = int(raw_mtime) if raw_mtime not in (None, "") else None
                except Exception:
                    modified_ts = None
                if modified_ts is not None and modified_ts <= 0:
                    modified_ts = None
                files.append(RemoteFile(normalize_remote_path(str(path)), size, is_dir, modified_ts))
        return sorted(files, key=lambda x: (x.path.lower(), not x.is_dir))

    def read_file(self, path: str, expected_size: int | None = None) -> bytes:
        path = normalize_remote_path(path)
        query = urllib.parse.urlencode({"path": path})
        data = self._request("GET", "/api/fs/read?" + query, timeout=30.0)
        if expected_size is not None and len(data) != expected_size:
            raise ProtoError(f"READ size mismatch for {path}: expected {expected_size}, got {len(data)}")
        return data

    def read_file_retry(self, path: str, expected_size: int | None = None, retries: int = READ_FILE_RETRIES) -> bytes:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                return self.read_file(path, expected_size=expected_size)
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(0.25)
                    continue
                raise
        raise ProtoError(str(last_error) if last_error else f"READ failed for {path}")

    def write_file(self, path: str, data: bytes, chunk_sizes=None, write_data_timeout: float | None = None, inter_chunk_delay: float = 0.0):
        path = normalize_remote_path(path)
        boundary = "----myradio-manager-" + str(time.time_ns())
        head = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"path\"\r\n\r\n"
            f"{path}\r\n"
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{Path(path).name or 'upload.bin'}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = head + data + tail

        # Important: pass the target path in the URL query too.
        # Arduino WebServer may not expose earlier multipart form fields via
        # server.arg("path") yet when UPLOAD_FILE_START fires, so relying only
        # on the multipart "path" field can make uploads fall back to basename
        # handling on some firmwares and flatten restored folders into root.
        query = urllib.parse.urlencode({"path": path})
        parsed = urllib.parse.urlsplit(self.base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ProtoError("missing or invalid base URL")
        target = parsed.path.rstrip("/") + "/upload?" + query
        # Serial restore used very small write timeouts/chunks; over WiFi those
        # values can prematurely break larger HTTP uploads.
        timeout = max(30.0, float(write_data_timeout)) if write_data_timeout is not None else 60.0
        conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        total_len = len(body)

        conn = conn_cls(parsed.netloc, timeout=timeout)
        try:
            conn.putrequest("POST", target)
            conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
            conn.putheader("Content-Length", str(total_len))
            conn.putheader("Connection", "close")
            conn.endheaders()

            conn.send(head)

            plan = [int(cs) for cs in (chunk_sizes or (4096,)) if int(cs) > 0]
            if not plan:
                plan = [4096]
            # Avoid very small HTTP writes (for example 96..256 bytes) that create
            # excessive packet churn and can destabilize long ESP uploads.
            plan = [max(1024, cs) for cs in plan]

            uploaded = 0
            chunk_index = 0
            max_chunk = max(plan)
            chunk_total = max(1, math.ceil(len(data) / max_chunk))
            while uploaded < len(data):
                chunk_size = plan[chunk_index % len(plan)]
                part = data[uploaded:uploaded + chunk_size]
                conn.send(part)
                uploaded += len(part)
                chunk_index += 1
                yield chunk_index, chunk_total, uploaded
                if inter_chunk_delay > 0:
                    time.sleep(inter_chunk_delay)

            conn.send(tail)
            resp = conn.getresponse()
            resp_data = resp.read()
            self.debug_lines.append(f"POST /upload?path=... -> {resp.status}")
            self.debug_lines = self.debug_lines[-20:]
            if resp.status >= 400:
                detail = resp_data.decode("utf-8", errors="replace")[:240]
                raise ProtoError(f"HTTP {resp.status} POST /upload?{query}: {detail}")
        except ProtoError:
            raise
        except Exception as e:
            raise ProtoError(f"WiFi request failed POST /upload?{query}: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _post_form(self, path: str, fields: dict[str, str], timeout: float = 15.0) -> bytes:
        body = urllib.parse.urlencode(fields).encode("utf-8")
        return self._request("POST", path, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=timeout)

    def _request(self, method: str, path: str, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: float = 10.0) -> bytes:
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = self.base_url + path
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                out = resp.read()
                self.debug_lines.append(f"{method} {path} -> {resp.status}")
                self.debug_lines = self.debug_lines[-20:]
                return out
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:240]
            raise ProtoError(f"HTTP {e.code} {method} {path}: {detail}")
        except Exception as e:
            raise ProtoError(f"WiFi request failed {method} {path}: {e}")


class App(tk.Tk):
    def __init__(self):
        set_windows_app_id()
        super().__init__()
        self.lang = "HU"
        self.client = HttpSpiFFSClient()
        self.files: list[RemoteFile] = []
        self.worker = None
        self.cancel_event = threading.Event()
        self.queue_lock = threading.Lock()
        self.upload_queue: list[UploadTask] = []
        self.queue_running = False
        self.current_queue_task_id: str | None = None
        self.known_remote_dirs: set[str] = {"/"}
        # Treeview item metadata.  Do not reconstruct remote paths only from
        # visible labels, because virtual folders are synthesized from file paths
        # when the firmware does not report DIR entries explicitly.
        self.tree_item_info: dict[str, tuple[str, bool]] = {}
        # Remember full paths uploaded/created by this tool. This repairs GUI display
        # when the firmware LIST command later reports only basename-only root files.
        self.known_remote_file_paths: dict[tuple[str, int], str] = {}
        self.known_remote_dir_paths: set[str] = {"/"}
        self.queue_stop_reason: str | None = None
        self.fs_profile_key = "auto"
        self.fs_profile_name = "Automatikus"
        self.spiffs_capacity_kb = None
        self.detected_fs_total_bytes: int | None = None
        self.detected_fs_backend: str | None = None
        self.connect_cancel_event = threading.Event()
        self.connecting = False

        self.title(f"{self.tr('title')} v{APP_VERSION}")
        self.geometry("1180x860")
        self.minsize(1180, 720)
        self._dark_mode = is_windows_dark_mode()
        apply_theme(self, self._dark_mode)
        icon_path = get_app_icon_path()
        if icon_path:
            try:
                self.iconbitmap(default=icon_path)
            except Exception:
                try:
                    self.iconbitmap(icon_path)
                except Exception:
                    pass

        self.ip_var = tk.StringVar(value="192.168.1.")
        self.status_var = tk.StringVar(value=self.tr("status_ready"))
        self.progress_var = tk.DoubleVar(value=0.0)
        self.overall_progress_var = tk.DoubleVar(value=0.0)
        self.current_file_var = tk.StringVar(value="-")
        self.overall_var = tk.StringVar(value="0 / 0")
        self.speed_var = tk.StringVar(value="0 KB/s")
        self.eta_var = tk.StringVar(value="--:--")
        self.failures_var = tk.StringVar(value="0")
        self.fs_estimate_var = tk.StringVar(value=self.tr("fs_estimate_unknown"))
        self.verify_backup_var = tk.BooleanVar(value=False)

        self._build_ui()
        self.update_fs_estimate()
        self._tree_scrollbar_after_id = None
        self._queue_tree_scrollbar_after_id = None
        self.after(100, self._refresh_tree_scrollbar)
        self.after(100, self._refresh_queue_tree_scrollbar)
        self.bind("<Configure>", lambda event: self.after_idle(self._on_window_layout_change))
        if self._dark_mode:
            self.after(50, lambda: apply_dark_title_bar(self))

    def tr(self, key: str) -> str:
        return TEXT[self.lang][key]

    def _prepare_dialog_parent(self):
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass
        return self

    def show_info(self, title: str, message: str):
        return self._show_modal_dialog(title, message, "info", ("ok",))

    def show_warning(self, title: str, message: str):
        return self._show_modal_dialog(title, message, "warning", ("ok",))

    def show_error(self, title: str, message: str):
        return self._show_modal_dialog(title, message, "error", ("ok",))

    def ask_yes_no(self, title: str, message: str) -> bool:
        return bool(self._show_modal_dialog(title, message, "question", ("yes", "no")))

    def _dialog_button_text(self, button: str) -> str:
        if button == "yes":
            return "Igen" if self.lang == "HU" else "Yes"
        if button == "no":
            return "Nem" if self.lang == "HU" else "No"
        return "OK"

    def _show_modal_dialog(self, title: str, message: str, kind: str, buttons: tuple[str, ...]):
        self._prepare_dialog_parent()
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.resizable(False, False)
        bg = "#1e1e1e" if self._dark_mode else "#f0f0f0"
        dialog.configure(bg=bg)
        try:
            icon_path = get_app_icon_path()
            if icon_path:
                dialog.iconbitmap(icon_path)
        except Exception:
            pass

        result = {"value": buttons[0] == "ok"}
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True)
        icon_text = {"info": "i", "warning": "!", "error": "X", "question": "?"}.get(kind, "i")
        icon = ttk.Label(body, text=icon_text, width=3, anchor="center", font=("Segoe UI", 24, "bold"))
        icon.pack(side="left", padx=(0, 14), anchor="n")
        text = ttk.Label(body, text=message, justify="left", wraplength=420)
        text.pack(side="left", fill="both", expand=True)

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", pady=(18, 0))

        def close_with(value):
            result["value"] = value
            dialog.destroy()

        for button in buttons:
            value = button in {"ok", "yes"}
            btn = ttk.Button(button_row, text=self._dialog_button_text(button), command=lambda v=value: close_with(v), width=12)
            btn.pack(side="right", padx=(8, 0))
            if button in {"ok", "yes"}:
                btn.focus_set()

        dialog.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = max(1, self.winfo_width())
        parent_h = max(1, self.winfo_height())
        dialog_w = dialog.winfo_reqwidth()
        dialog_h = dialog.winfo_reqheight()
        x = parent_x + max(0, (parent_w - dialog_w) // 2)
        y = parent_y + max(0, (parent_h - dialog_h) // 2)
        if dialog_w < parent_w:
            x = min(max(x, parent_x), parent_x + parent_w - dialog_w)
        if dialog_h < parent_h:
            y = min(max(y, parent_y), parent_y + parent_h - dialog_h)
        dialog.geometry(f"+{x}+{y}")
        dialog.protocol("WM_DELETE_WINDOW", lambda: close_with(False))
        dialog.grab_set()
        dialog.wait_window()
        return result["value"]

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.lbl_ip = ttk.Label(top, text=self.tr("radio_ip"))
        self.lbl_ip.grid(row=0, column=0, sticky="w")
        self.ip_entry = ttk.Entry(top, textvariable=self.ip_var, width=20)
        if self._dark_mode:
            try:
                self.ip_entry.configure(style="TEntry")
            except Exception:
                pass
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=6)
        self.ip_entry.bind("<Return>", lambda _event: self.connect())
        self.ip_entry.bind("<KP_Enter>", lambda _event: self.connect())
        self.btn_maint = ttk.Button(top, text=self.tr("connect"), command=self.connect)
        self.btn_maint.grid(row=0, column=2, padx=4)
        self.btn_lang = ttk.Button(top, text=self.tr("lang"), command=self.toggle_lang)
        self.btn_lang.grid(row=0, column=3, padx=4)
        self.btn_capacity = ttk.Button(top, text=self.tr("spiffs_capacity"), command=self.set_spiffs_capacity)
        self.btn_capacity.grid(row=0, column=4, padx=4)
        top.columnconfigure(1, weight=1)

        actions = ttk.Frame(self, padding=(8, 0, 8, 8))
        actions.pack(fill="x")
        self.btn_list = ttk.Button(actions, text=self.tr("list"), command=self.refresh_list)
        self.btn_list.pack(side="left", padx=3)
        self.btn_backup = ttk.Button(actions, text=self.tr("backup"), command=self.backup_zip)
        self.btn_backup.pack(side="left", padx=3)
        self.chk_backup_verify = ttk.Checkbutton(actions, text=self.tr("backup_verify"), variable=self.verify_backup_var)
        self.chk_backup_verify.pack(side="left", padx=(4, 10))
        self.btn_restore = ttk.Button(actions, text=self.tr("restore"), command=self.restore_zip)
        self.btn_restore.pack(side="left", padx=3)
        self.btn_download = ttk.Button(actions, text=self.tr("download"), command=self.download_selected)
        self.btn_download.pack(side="left", padx=3)
        self.btn_mkdir = ttk.Button(actions, text=self.tr("mkdir"), command=self.create_directory)
        self.btn_mkdir.pack(side="left", padx=3)
        self.btn_delete = ttk.Button(actions, text=self.tr("delete"), command=self.delete_selected)
        self.btn_delete.pack(side="left", padx=3)
        self.btn_reboot = ttk.Button(actions, text=self.tr("reboot"), command=self.reboot_radio)
        self.btn_reboot.pack(side="left", padx=3)

        self.connection_progress_row = ttk.Frame(self, padding=(8, 0, 8, 4))
        self.connection_progress_spacer = ttk.Frame(self.connection_progress_row, width=250)
        self.connection_progress_spacer.pack(side="left")
        self.connection_progress_label = ttk.Label(self.connection_progress_row, text=self.tr("status_connecting"))
        self.connection_progress_label.pack(side="left", padx=(0, 8))
        self.connection_progress = ttk.Progressbar(self.connection_progress_row, mode="indeterminate", length=360)
        self.connection_progress.pack(side="left")
        self.btn_connect_cancel = ttk.Button(self.connection_progress_row, text=self.tr("connect_cancel"), command=self.cancel_connect, width=12)
        self.btn_connect_cancel.pack(side="left", padx=(8, 0))

        self.main_pane = ttk.Panedwindow(self, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.connection_progress_row.pack_forget()

        left = ttk.Frame(self.main_pane)
        right = ttk.Frame(self.main_pane)
        self.main_pane.add(left, weight=1)
        self.main_pane.add(right, weight=1)

        self.left_panel = ttk.LabelFrame(left, text=self.tr("tree"), padding=8)
        self.left_panel.pack(fill="both", expand=True)
        self.tree_wrap = ttk.Frame(self.left_panel)
        self.tree_wrap.pack(fill="both", expand=True)
        self.tree_wrap.rowconfigure(0, weight=1)
        self.tree_wrap.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(self.tree_wrap, columns=("type", "size", "modified"), show="tree headings", selectmode="extended")
        self.tree.heading("#0", text=self.tr("tree"))
        self.tree.heading("type", text=self.tr("type"))
        self.tree.heading("size", text=self.tr("size"))
        self.tree.heading("modified", text=self.tr("modified"))
        self.tree.column("#0", width=430, minwidth=160, anchor="w", stretch=True)
        self.tree.column("type", width=95, minwidth=90, anchor="w", stretch=False)
        self.tree.column("size", width=85, minwidth=80, anchor="w", stretch=False)
        self.tree.column("modified", width=132, minwidth=120, anchor="w", stretch=False)
        self.tree_ys = ttk.Scrollbar(self.tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_tree_yview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_ys.grid(row=0, column=1, sticky="ns")
        self.tree_ys.grid_remove()
        self.tree.bind("<<TreeviewOpen>>", lambda event: self._schedule_tree_scrollbar_refresh())
        self.tree.bind("<<TreeviewClose>>", lambda event: self._schedule_tree_scrollbar_refresh())
        self.tree.bind("<Configure>", lambda event: self._schedule_tree_scrollbar_refresh())

        self.queue_panel = ttk.LabelFrame(right, text=self.tr("queue"), padding=8)
        self.queue_panel.pack(fill="both", expand=True)

        queue_buttons = ttk.Frame(self.queue_panel)
        queue_buttons.pack(fill="x", pady=(0, 8))
        self.btn_queue_add_files = ttk.Button(queue_buttons, text=self.tr("queue_add_files"), command=self.queue_add_files)
        self.btn_queue_add_files.pack(side="left", padx=2)
        self.btn_queue_add_folder = ttk.Button(queue_buttons, text=self.tr("queue_add_folder"), command=self.queue_add_folder)
        self.btn_queue_add_folder.pack(side="left", padx=2)
        self.btn_queue_start = ttk.Button(queue_buttons, text=self.tr("queue_start"), command=self.start_queue)
        self.btn_queue_start.pack(side="left", padx=2)
        self.btn_queue_cancel = ttk.Button(queue_buttons, text=self.tr("queue_cancel"), command=self.cancel_queue)
        self.btn_queue_cancel.pack(side="left", padx=2)
        self.btn_queue_remove = ttk.Button(queue_buttons, text=self.tr("queue_remove"), command=self.remove_selected_tasks)
        self.btn_queue_remove.pack(side="left", padx=2)

        self.queue_tree_wrap = ttk.Frame(self.queue_panel)
        self.queue_tree_wrap.pack(fill="both", expand=True)
        self.queue_tree_wrap.rowconfigure(0, weight=1)
        self.queue_tree_wrap.columnconfigure(0, weight=1)

        self.queue_tree = ttk.Treeview(self.queue_tree_wrap, columns=("target", "status", "progress", "size"), show="tree headings", height=18, selectmode="extended")
        self.queue_tree.heading("#0", text=self.tr("queue_name"))
        self.queue_tree.heading("target", text=self.tr("queue_target"))
        self.queue_tree.heading("status", text=self.tr("queue_status"))
        self.queue_tree.heading("progress", text=self.tr("queue_progress"))
        self.queue_tree.heading("size", text=self.tr("queue_size"))
        self.queue_tree.column("#0", width=150, minwidth=120, anchor="w", stretch=True)
        self.queue_tree.column("target", width=130, minwidth=120, anchor="w", stretch=True)
        self.queue_tree.column("status", width=70, minwidth=90, anchor="w", stretch=True)
        self.queue_tree.column("progress", width=60, minwidth=90, anchor="w", stretch=True)
        self.queue_tree.column("size", width=60, minwidth=80, anchor="w", stretch=True)
        self.queue_tree_ys = ttk.Scrollbar(self.queue_tree_wrap, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=self._on_queue_tree_yview)
        self.queue_tree.grid(row=0, column=0, sticky="nsew")
        self.queue_tree_ys.grid(row=0, column=1, sticky="ns")
        self.queue_tree_ys.grid_remove()
        self.queue_tree.bind("<Configure>", lambda event: self._schedule_queue_tree_scrollbar_refresh())

        self.progress_box = ttk.LabelFrame(self.queue_panel, text=self.tr("queue_progress"), padding=8)
        self.progress_box.pack(fill="x", pady=(8, 0))
        self.progress = ttk.Progressbar(self.progress_box, variable=self.progress_var, maximum=100.0)
        self.progress.pack(fill="x")
        self.progress_overall = ttk.Progressbar(self.progress_box, variable=self.overall_progress_var, maximum=100.0)
        self.progress_overall.pack(fill="x", pady=(6, 0))

        grid = ttk.Frame(self.progress_box)
        grid.pack(fill="x", pady=(8, 0))
        for idx in range(0, 4):
            grid.columnconfigure(idx, weight=1)
        self.lbl_queue_file = ttk.Label(grid, text=self.tr("queue_file"))
        self.lbl_queue_file.grid(row=0, column=0, sticky="w")
        ttk.Label(grid, textvariable=self.current_file_var).grid(row=0, column=1, sticky="w")
        self.lbl_queue_index = ttk.Label(grid, text=self.tr("queue_index"))
        self.lbl_queue_index.grid(row=0, column=2, sticky="w")
        ttk.Label(grid, textvariable=self.overall_var).grid(row=0, column=3, sticky="w")
        self.lbl_queue_speed = ttk.Label(grid, text=self.tr("queue_speed"))
        self.lbl_queue_speed.grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(grid, textvariable=self.speed_var).grid(row=1, column=1, sticky="w", pady=(4, 0))
        self.lbl_queue_eta = ttk.Label(grid, text=self.tr("queue_eta"))
        self.lbl_queue_eta.grid(row=1, column=2, sticky="w", pady=(4, 0))
        ttk.Label(grid, textvariable=self.eta_var).grid(row=1, column=3, sticky="w", pady=(4, 0))
        self.lbl_queue_failures = ttk.Label(grid, text=self.tr("queue_failures"))
        self.lbl_queue_failures.grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Label(grid, textvariable=self.failures_var).grid(row=2, column=1, sticky="w", pady=(4, 0))
        self.lbl_queue_overall = ttk.Label(grid, text=self.tr("queue_overall"))
        self.lbl_queue_overall.grid(row=2, column=2, sticky="w", pady=(4, 0))
        self.queue_status_label = ttk.Label(grid, textvariable=self.status_var, wraplength=320, justify="left")
        self.queue_status_label.grid(row=2, column=3, sticky="ew", pady=(4, 0))
        self.fs_estimate_label = ttk.Label(grid, textvariable=self.fs_estimate_var, wraplength=680, justify="left")
        self.fs_estimate_label.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(6, 0))

        self.after(100, self._apply_initial_layout)

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")
        ttk.Label(bottom, text=self.tr("footer")).pack(side="right")

    def _schedule_tree_scrollbar_refresh(self):
        try:
            if self._tree_scrollbar_after_id is not None:
                self.after_cancel(self._tree_scrollbar_after_id)
        except Exception:
            pass
        self._tree_scrollbar_after_id = self.after_idle(self._refresh_tree_scrollbar)

    def _schedule_queue_tree_scrollbar_refresh(self):
        try:
            if self._queue_tree_scrollbar_after_id is not None:
                self.after_cancel(self._queue_tree_scrollbar_after_id)
        except Exception:
            pass
        self._queue_tree_scrollbar_after_id = self.after_idle(self._refresh_queue_tree_scrollbar)

    def _set_queue_tree_scrollbar_visible(self, visible: bool):
        try:
            if visible:
                self.queue_tree_ys.grid()
            else:
                self.queue_tree_ys.grid_remove()
        except Exception:
            pass

    def _on_queue_tree_yview(self, first, last):
        self.queue_tree_ys.set(first, last)
        try:
            need_scroll = not (float(first) <= 0.0 and float(last) >= 1.0)
        except Exception:
            need_scroll = True
        self._set_queue_tree_scrollbar_visible(need_scroll)

    def _refresh_queue_tree_scrollbar(self):
        self._queue_tree_scrollbar_after_id = None
        try:
            self.update_idletasks()
            first, last = self.queue_tree.yview()
            need_scroll = not (float(first) <= 0.0 and float(last) >= 1.0)
            self._set_queue_tree_scrollbar_visible(need_scroll)
            if need_scroll:
                self.queue_tree_ys.set(first, last)
        except Exception:
            self._set_queue_tree_scrollbar_visible(False)

    def _set_tree_scrollbar_visible(self, visible: bool):
        try:
            if visible:
                self.tree_ys.grid()
            else:
                self.tree_ys.grid_remove()
        except Exception:
            pass

    def _on_tree_yview(self, first, last):
        self.tree_ys.set(first, last)
        try:
            need_scroll = not (float(first) <= 0.0 and float(last) >= 1.0)
        except Exception:
            need_scroll = True
        self._set_tree_scrollbar_visible(need_scroll)

    def _refresh_tree_scrollbar(self):
        self._tree_scrollbar_after_id = None
        try:
            self.update_idletasks()
            first, last = self.tree.yview()
            need_scroll = not (float(first) <= 0.0 and float(last) >= 1.0)
            self._set_tree_scrollbar_visible(need_scroll)
            if need_scroll:
                self.tree_ys.set(first, last)
        except Exception:
            self._set_tree_scrollbar_visible(False)

    def _resize_left_tree_columns(self):
        try:
            total = self.tree.winfo_width()
            if total <= 120:
                return
            type_w = max(90, min(130, int(total * 0.18)))
            size_w = max(80, min(120, int(total * 0.16)))
            name_w = max(160, total - type_w - size_w - 6)
            self.tree.column("#0", width=name_w, minwidth=160, stretch=True)
            self.tree.column("type", width=type_w, minwidth=90, stretch=False)
            self.tree.column("size", width=size_w, minwidth=80, stretch=False)
        except Exception:
            pass

    def _resize_queue_tree_columns(self):
        try:
            total = self.queue_tree.winfo_width()
            if total <= 160:
                return
            name_w = max(120, int(total * 0.26))
            target_w = max(150, int(total * 0.36))
            status_w = max(90, int(total * 0.14))
            progress_w = max(90, int(total * 0.12))
            size_w = max(80, total - name_w - target_w - status_w - progress_w - 6)
            self.queue_tree.column("#0", width=name_w, minwidth=120, stretch=True)
            self.queue_tree.column("target", width=target_w, minwidth=150, stretch=True)
            self.queue_tree.column("status", width=status_w, minwidth=90, stretch=False)
            self.queue_tree.column("progress", width=progress_w, minwidth=90, stretch=False)
            self.queue_tree.column("size", width=size_w, minwidth=80, stretch=False)
            self._schedule_queue_tree_scrollbar_refresh()
        except Exception:
            pass

    def _update_status_wrap(self):
        try:
            wrap = max(180, self.progress_box.winfo_width() - 340)
            self.queue_status_label.configure(wraplength=wrap)
            self.fs_estimate_label.configure(wraplength=max(240, self.progress_box.winfo_width() - 40))
        except Exception:
            pass

    def _on_window_layout_change(self):
        self._schedule_tree_scrollbar_refresh()
        self._schedule_queue_tree_scrollbar_refresh()
        self._resize_left_tree_columns()
        self._resize_queue_tree_columns()
        self._update_status_wrap()

    def _apply_initial_layout(self):
        try:
            total = self.main_pane.winfo_width()
            if total > 0:
                self.main_pane.sashpos(0, int(total * 0.48))
        except Exception:
            pass
        self.after_idle(self._on_window_layout_change)


    def _localized_profile_label(self, key: str, label: str, kb: int | None) -> str:
        if self.lang == "EN":
            label = label.replace("Általános", "Generic").replace("Egyedi", "Custom").replace("Automatikus", "Automatic")
        return label

    def _fs_profile_options(self) -> list[tuple[str, str, int | None]]:
        return [(key, self._localized_profile_label(key, label, kb), kb) for key, label, kb in FS_PROFILE_CHOICES]

    def _set_fs_profile(self, key: str, name: str, kb: int | None):
        self.fs_profile_key = key
        if key == "auto":
            label = self._backend_display_name(self.detected_fs_backend) if self.detected_fs_backend else None
            if label:
                self.fs_profile_name = ("Automatikus" if self.lang == "HU" else "Auto") + f" ({label})"
            else:
                self.fs_profile_name = "Automatikus" if self.lang == "HU" else "Auto"
        else:
            self.fs_profile_name = name
        self.spiffs_capacity_kb = kb
        self.update_fs_estimate()
        if kb is None:
            self.set_status(self.tr("spiffs_capacity_disabled"))
        else:
            self.set_status(self.tr("spiffs_capacity_set").format(name=name, value=kb))

    def set_spiffs_capacity(self):
        self._prepare_dialog_parent()
        dialog = tk.Toplevel(self)
        dialog.title(self.tr("set_spiffs_capacity"))
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.configure(bg="#1e1e1e" if self._dark_mode else "#f0f0f0")

        result = {"ok": False}
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=self.tr("spiffs_capacity_prompt"), justify="left", wraplength=420).pack(fill="x")

        options = self._fs_profile_options()
        label_to_option = {label: (key, label, kb) for key, label, kb in options}
        initial_label = next((label for key, label, _ in options if key == self.fs_profile_key), options[0][1])
        profile_var = tk.StringVar(value=initial_label)
        combo = ttk.Combobox(frame, textvariable=profile_var, values=[label for _, label, _ in options], state="readonly", width=34)
        combo.pack(fill="x", pady=(12, 8))

        custom_var = tk.StringVar(value="" if self.spiffs_capacity_kb is None else str(self.spiffs_capacity_kb))
        custom_row = ttk.Frame(frame)
        custom_row.pack(fill="x")
        ttk.Label(custom_row, text=self.tr("spiffs_capacity_custom")).pack(side="left")
        custom_entry = ttk.Entry(custom_row, textvariable=custom_var, width=10)
        custom_entry.pack(side="left", padx=(8, 0))

        def update_custom_state(*_):
            selected = label_to_option.get(profile_var.get(), options[0])
            state = tk.NORMAL if selected[0] == "custom" else tk.DISABLED
            custom_entry.configure(state=state)

        def close_ok():
            selected = label_to_option.get(profile_var.get(), options[0])
            key, name, kb = selected
            if key == "custom":
                kb = parse_positive_int_or_none(custom_var.get())
                if kb is None:
                    self.show_warning(self.tr("warning"), self.tr("spiffs_capacity_custom"))
                    return
                name = self._localized_profile_label(key, "Egyedi", kb)
            result["ok"] = True
            result["value"] = (key, name, kb)
            dialog.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(16, 0))
        ttk.Button(buttons, text="OK", command=close_ok, width=12).pack(side="right")
        ttk.Button(buttons, text="Mégse" if self.lang == "HU" else "Cancel", command=dialog.destroy, width=12).pack(side="right", padx=(0, 8))
        profile_var.trace_add("write", update_custom_state)
        update_custom_state()

        dialog.update_idletasks()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - dialog.winfo_reqwidth()) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()
        combo.focus_set()
        dialog.wait_window()

        if result.get("ok"):
            key, name, kb = result["value"]
            self._set_fs_profile(key, name, kb)

    def _backend_display_name(self, backend: str | None) -> str:
        b = (backend or "").strip().lower()
        if b == "littlefs":
            return "LittleFS"
        if b == "spiffs":
            return "SPIFFS"
        return (backend or "unknown").upper()

    def _apply_remote_fs_info(self, info: dict[str, int | str] | None):
        if not info:
            return
        try:
            total = int(info.get("total", 0) or 0)
        except Exception:
            return
        if total <= 0:
            return

        backend = str(info.get("backend", "")).strip().lower() or "unknown"
        self.detected_fs_total_bytes = total
        self.detected_fs_backend = backend
        label = self._backend_display_name(backend)
        self.fs_profile_key = "auto"
        self.fs_profile_name = ("Automatikus" if self.lang == "HU" else "Auto") + f" ({label})"
        self.spiffs_capacity_kb = max(1, total // 1024)

    def toggle_lang(self):
        self.lang = "EN" if self.lang == "HU" else "HU"
        self.title(f"{self.tr('title')} v{APP_VERSION}")
        self.lbl_ip.config(text=self.tr("radio_ip"))
        self.btn_maint.config(text=self.tr("connect"))
        self.btn_lang.config(text=self.tr("lang"))
        self.btn_capacity.config(text=self.tr("spiffs_capacity"))
        self.btn_connect_cancel.config(text=self.tr("connect_cancel"))
        for key, label, _ in self._fs_profile_options():
            if key == self.fs_profile_key and key != "custom":
                self.fs_profile_name = label
                break
        if self.fs_profile_key == "auto":
            label = self._backend_display_name(self.detected_fs_backend)
            self.fs_profile_name = ("Automatikus" if self.lang == "HU" else "Auto") + f" ({label})"
        if self.fs_profile_key == "custom":
            self.fs_profile_name = "Egyedi" if self.lang == "HU" else "Custom"
        self.btn_list.config(text=self.tr("list"))
        self.btn_backup.config(text=self.tr("backup"))
        self.chk_backup_verify.config(text=self.tr("backup_verify"))
        self.btn_restore.config(text=self.tr("restore"))
        self.btn_download.config(text=self.tr("download"))
        self.btn_mkdir.config(text=self.tr("mkdir"))
        self.btn_delete.config(text=self.tr("delete"))
        self.btn_reboot.config(text=self.tr("reboot"))
        self.connection_progress_label.config(text=self.tr("status_connecting"))
        self.btn_queue_add_files.config(text=self.tr("queue_add_files"))
        self.btn_queue_add_folder.config(text=self.tr("queue_add_folder"))
        self.btn_queue_start.config(text=self.tr("queue_start"))
        self.btn_queue_cancel.config(text=self.tr("queue_cancel"))
        self.btn_queue_remove.config(text=self.tr("queue_remove"))
        self.tree.heading("#0", text=self.tr("tree"))
        self.tree.heading("type", text=self.tr("type"))
        self.tree.heading("size", text=self.tr("size"))
        self.tree.heading("modified", text=self.tr("modified"))
        self.tree.tag_configure("root_link")
        self.left_panel.config(text=self.tr("tree"))
        self.queue_panel.config(text=self.tr("queue"))
        self.progress_box.config(text=self.tr("queue_progress"))
        self.lbl_queue_file.config(text=self.tr("queue_file"))
        self.lbl_queue_index.config(text=self.tr("queue_index"))
        self.lbl_queue_speed.config(text=self.tr("queue_speed"))
        self.lbl_queue_eta.config(text=self.tr("queue_eta"))
        self.lbl_queue_failures.config(text=self.tr("queue_failures"))
        self.lbl_queue_overall.config(text=self.tr("queue_overall"))
        self.queue_tree.heading("#0", text=self.tr("queue_name"))
        self.queue_tree.heading("target", text=self.tr("queue_target"))
        self.queue_tree.heading("status", text=self.tr("queue_status"))
        self.queue_tree.heading("progress", text=self.tr("queue_progress"))
        self.queue_tree.heading("size", text=self.tr("queue_size"))
        current_status = self.status_var.get()
        for key in ("status_ready", "maintenance_ok", "queue_idle", "queue_running", "queue_finished", "queue_cancelled_done"):
            other = TEXT["EN" if self.lang == "HU" else "HU"][key]
            if current_status == other or current_status == TEXT[self.lang][key]:
                self.status_var.set(self.tr(key))
                break
        apply_theme(self, self._dark_mode)
        self.update_fs_estimate()
        self.populate_tree(restore_state=self._capture_tree_state())
        self.refresh_queue_tree()
        self.after_idle(self._on_window_layout_change)

    def _start_connection_progress(self):
        try:
            self.connecting = True
            self.connect_cancel_event.clear()
            self.connection_progress_label.config(text=self.tr("status_connecting"))
            self.connection_progress_row.pack(fill="x", before=self.main_pane)
            self.connection_progress.start(12)
            self.btn_connect_cancel.config(state=tk.NORMAL)
        except Exception:
            pass

    def _stop_connection_progress(self):
        try:
            self.connecting = False
            self.connect_cancel_event.clear()
            self.connection_progress.stop()
            self.connection_progress_row.pack_forget()
            self.btn_connect_cancel.config(state=tk.DISABLED)
        except Exception:
            pass

    def cancel_connect(self):
        if not self.connecting:
            return
        self.connect_cancel_event.set()
        self.set_status(self.tr("status_connect_cancelled"))

    def set_status(self, text: str):
        self.after(0, lambda: self.status_var.set(text))

    def _set_busy_cursor(self, busy: bool):
        cursor = "watch" if busy else ""

        def apply_cursor():
            try:
                self.configure(cursor=cursor)
                self.update_idletasks()
            except Exception:
                pass

        self.after(0, apply_cursor)

    def _localize_error(self, text: str) -> str:
        if self.lang != "HU":
            return text
        replacements = {
            "could not enter maintenance mode": "Nem sikerült belépni a karbantartó módba",
            "unexpected BEGIN reply": "Váratlan BEGIN válasz",
            "protocol timeout": "Kommunikációs időtúllépés",
            "protocol line too long": "Túl hosszú protokollsor",
            "not connected": "Nincs kapcsolat",
            "bad DELETE reply": "Hibás törlési válasz",
            "delete verification failed": "A törlés ellenőrzése sikertelen",
            "bad RMDIR reply": "Hibás mappatörlési válasz",
            "rmdir_failed": "a mappa törlése sikertelen (rmdir_failed)",
            "bad MKDIR reply": "Hibás mappalétrehozási válasz",
            "bad WRITE_BEGIN reply": "Hibás íráskezdési válasz",
            "bad WRITE_DATA reply": "Hibás írási adatválasz",
            "bad WRITE_END reply": "Hibás írászárási válasz",
            "bad READ_END reply": "Hibás olvasási záróválasz",
            "bad REBOOT reply": "Hibás újraindítási válasz",
            "pyserial not installed": "A pyserial nincs telepítve",
            "write failed after retries for": "Az írás többszöri próbálkozás után is sikertelen ennél:",
            "write failed after safe fallback for": "Az írás a gyors mód és a biztonsági visszaesés után is sikertelen ennél:",
            "ERR|WRITE_BEGIN|open_failed": "Hibás íráskezdési válasz: a fájl írásra nem nyitható meg (open_failed)",
            "open_failed": "a fájl írásra nem nyitható meg (open_failed)",
        }
        out = text
        for src, dst in replacements.items():
            out = out.replace(src, dst)
        return out

    def run_job(self, fn, done=None, on_finally=None):
        if self.worker and self.worker.is_alive():
            self.show_warning(self.tr("warning"), self.tr("queue_running"))
            return False

        def wrap():
            try:
                result = fn()
                if done:
                    self.after(0, lambda: done(result))
            except UserCancelled:
                self.set_status(self.tr("status_connect_cancelled"))
            except Exception as e:
                last_step = self.status_var.get()
                self.after(0, lambda: self.show_error(self.tr("error"), f"{self._localize_error(str(e))}\n\n{self.tr('last_step')}: {last_step}"))
                self.set_status(self.tr("error"))
                self.after(0, self._reset_queue_runtime_labels)
            finally:
                self.after(0, self._stop_connection_progress)
                if on_finally:
                    self.after(0, on_finally)

        self.worker = threading.Thread(target=wrap, daemon=True)
        self.worker.start()
        return True

    def _new_client_for_selected_mode(self):
        return HttpSpiFFSClient()

    def ensure_connected(self):
        if not self.client.ser:
            raise ProtoError(self.tr("connect_first"))

    def connect(self):
        def job():
            self.set_status(self.tr("status_connecting"))
            self.client.disconnect()
            self.client = self._new_client_for_selected_mode()
            self.client.connect(self.ip_var.get(), cancel_event=self.connect_cancel_event)
            if self.connect_cancel_event.is_set():
                raise UserCancelled("connect cancelled")
            self.client.ping()
            fs_info = self.client.get_fs_info()
            self.set_status(self.tr("status_listing"))
            return self.client.list_files(), fs_info

        def done(result):
            files, fs_info = result
            self._apply_remote_fs_info(fs_info)
            files = self._apply_known_remote_paths(files)
            self.files = files
            self._rebuild_known_remote_dirs(files)
            self.populate_tree()
            self.update_fs_estimate()
            self.set_status(self.tr("wifi_connected"))

        self._start_connection_progress()
        if not self.run_job(job, done):
            self._stop_connection_progress()

    def disconnect(self):
        if self.queue_running:
            self.cancel_queue()
        self.client.disconnect()
        self.detected_fs_total_bytes = None
        self.detected_fs_backend = None
        self.set_status(self.tr("status_ready"))
        self._reset_queue_runtime_labels()

    def refresh_list(self):
        def job():
            self.ensure_connected()
            self.set_status(self.tr("status_listing"))
            return self.client.list_files(), self.client.get_fs_info()

        def done(result):
            files, fs_info = result
            self._apply_remote_fs_info(fs_info)
            files = self._apply_known_remote_paths(files)
            self.files = files
            self._rebuild_known_remote_dirs(files)
            self.populate_tree()
            self.update_fs_estimate()
            self.set_status(f"{len(files)} {self.tr('file')}")

        self.run_job(job, done)

    def _remember_remote_path(self, path: str, size: int = 0, is_dir: bool = False):
        path = normalize_remote_path(path)
        if path == "/":
            self.known_remote_dir_paths.add("/")
            return
        if is_dir:
            self.known_remote_dir_paths.add(path)
        else:
            name = Path(path).name.lower()
            self.known_remote_file_paths[(name, int(size))] = path
            self.known_remote_file_paths[(name, -1)] = path
        current = ""
        parts = [part for part in path.strip("/").split("/") if part]
        dir_parts = parts if is_dir else parts[:-1]
        for part in dir_parts:
            current += "/" + part
            self.known_remote_dir_paths.add(current)

    def _forget_remote_path_tree(self, path: str):
        path = normalize_remote_path(path)
        if path == "/":
            self.known_remote_file_paths.clear()
            self.known_remote_dir_paths = {"/"}
            return
        prefix = path.rstrip("/") + "/"
        self.known_remote_dir_paths = {
            d for d in self.known_remote_dir_paths
            if d == "/" or (d != path and not d.startswith(prefix))
        }
        self.known_remote_file_paths = {
            key: remembered_path
            for key, remembered_path in self.known_remote_file_paths.items()
            if remembered_path != path and not remembered_path.startswith(prefix)
        }

    def _guess_folder_for_basename_only_file(self, name: str) -> str | None:
        """
        Some maintenance firmwares report files inside folders as basename-only
        entries through the LIST protocol, even though the real filesystem path
        is e.g. /fonts/test_24.vlw.  ESPConnect shows those paths correctly,
        but this serial protocol can lose the parent folder.  Keep the GUI useful
        by restoring well-known myRadio asset folders for basename-only entries.
        """
        low = (name or "").lower()
        if low.endswith(".vlw"):
            return "/fonts"
        return None

    def _apply_known_remote_paths(self, files: list[RemoteFile]) -> list[RemoteFile]:
        out: list[RemoteFile] = []
        seen: set[tuple[str, bool]] = set()
        for rf in files:
            path = normalize_remote_path(rf.path)
            is_dir = getattr(rf, "is_dir", False)
            size = int(getattr(rf, "size", 0))
            if is_dir:
                fixed_path = path
            elif path.count("/") <= 1:
                # LIST returned a root-level basename. If we have seen the same file
                # uploaded into a folder, restore that folder path for display/actions.
                # If this is a known myRadio asset type (for example VLW fonts),
                # restore the conventional folder even after restarting the manager.
                basename = Path(path).name
                lookup_name = basename.lower()
                remembered = self.known_remote_file_paths.get((lookup_name, size)) or self.known_remote_file_paths.get((lookup_name, -1))
                guessed_folder = self._guess_folder_for_basename_only_file(basename)
                fixed_path = remembered or (normalize_remote_path(f"{guessed_folder}/{basename}") if guessed_folder else path)
                if fixed_path != path:
                    self._remember_remote_path(fixed_path, size, False)
            else:
                fixed_path = path
                self._remember_remote_path(fixed_path, size, False)
            key = (fixed_path, is_dir)
            if key not in seen:
                out.append(RemoteFile(fixed_path, size, is_dir, getattr(rf, "modified_ts", None)))
                seen.add(key)
        for d in sorted(self.known_remote_dir_paths, key=lambda x: (x.count("/"), x.lower())):
            if d != "/" and (d, True) not in seen:
                out.append(RemoteFile(d, 0, True))
                seen.add((d, True))
        return sorted(out, key=lambda x: (x.path.lower(), not x.is_dir))

    def _rebuild_known_remote_dirs(self, files: list[RemoteFile]):
        dirs = {"/"}
        for rf in files:
            path = normalize_remote_path(rf.path)
            parts = [p for p in path.strip('/').split('/') if p]
            current = ""
            end = len(parts) if rf.is_dir else max(0, len(parts) - 1)
            for part in parts[:end]:
                current += "/" + part
                dirs.add(current)
        self.known_remote_dirs = dirs

    def _capture_tree_state(self) -> dict:
        state = {
            "open_paths": set(),
            "selected_paths": [],
            "focus_path": None,
            "yview": 0.0,
        }
        try:
            for item_id in self.tree.selection():
                path, _ = self._item_remote_path(item_id)
                state["selected_paths"].append(path)
        except Exception:
            pass
        try:
            focus_id = self.tree.focus()
            if focus_id:
                state["focus_path"], _ = self._item_remote_path(focus_id)
        except Exception:
            pass
        try:
            state["yview"] = float(self.tree.yview()[0])
        except Exception:
            pass

        def walk(parent=""):
            for child in self.tree.get_children(parent):
                try:
                    path, is_file = self._item_remote_path(child)
                    if not is_file and self.tree.item(child, "open"):
                        state["open_paths"].add(path)
                except Exception:
                    pass
                walk(child)

        walk("")
        return state

    def populate_tree(self, restore_state: dict | None = None):
        self.tree.delete(*self.tree.get_children())
        self.tree_item_info = {}
        root_item_id = self.tree.insert("", "end", text="..", values=(self.tr("root"), "", ""), tags=("root_link",))
        self.tree_item_info[root_item_id] = ("/", False)

        # Some ESP32 SPIFFS/LittleFS list implementations return only FILE rows,
        # even when the file path contains folders.  Build a real visual folder
        # tree from every slash-separated path, and only mark the final segment as
        # a file when the remote entry itself is not a directory.
        nodes = {"/": ""}
        entry_by_path: dict[str, RemoteFile] = {}
        for rf in self.files:
            path = normalize_remote_path(rf.path)
            if path == "/":
                continue
            entry_by_path[path] = RemoteFile(path, rf.size, getattr(rf, "is_dir", False), getattr(rf, "modified_ts", None))

        def ensure_dir(path: str) -> str:
            path = normalize_remote_path(path)
            if path in nodes:
                return nodes[path]
            parent_path = normalize_remote_path("/".join(path.rstrip("/").split("/")[:-1]) or "/")
            parent_id = ensure_dir(parent_path) if parent_path != path else ""
            name = path.rstrip("/").split("/")[-1]
            item_id = self.tree.insert(parent_id, "end", text=name, values=(self.tr("folder"), "", ""))
            nodes[path] = item_id
            self.tree_item_info[item_id] = (path, False)
            return item_id

        for path in sorted(entry_by_path, key=lambda x: (x.count("/"), x.lower())):
            rf = entry_by_path[path]
            parts = [part for part in path.strip("/").split("/") if part]
            if not parts:
                continue

            parent_path = "/"
            for part in parts[:-1] if not rf.is_dir else parts:
                parent_path = normalize_remote_path(parent_path.rstrip("/") + "/" + part)
                ensure_dir(parent_path)

            if rf.is_dir:
                continue

            parent_path = normalize_remote_path("/".join(path.split("/")[:-1]) or "/")
            parent_id = ensure_dir(parent_path)
            name = parts[-1]
            item_id = self.tree.insert(parent_id, "end", text=name, values=(self.tr("file"), fmt_size(rf.size), fmt_mtime(getattr(rf, "modified_ts", None))))
            nodes[path] = item_id
            self.tree_item_info[item_id] = (path, True)

        if restore_state:
            for path in restore_state.get("open_paths", set()):
                item_id = nodes.get(path)
                if item_id:
                    self.tree.item(item_id, open=True)

            selected_ids = []
            for path in restore_state.get("selected_paths", []):
                item_id = root_item_id if path == "/" else nodes.get(path)
                if item_id:
                    selected_ids.append(item_id)
            if selected_ids:
                self.tree.selection_set(selected_ids)

            focus_path = restore_state.get("focus_path")
            if focus_path:
                focus_id = root_item_id if focus_path == "/" else nodes.get(focus_path)
                if focus_id:
                    self.tree.focus(focus_id)

            def restore_view():
                try:
                    yview = float(restore_state.get("yview", 0.0))
                    self.tree.yview_moveto(yview)
                    selected = self.tree.selection()
                    if selected:
                        self.tree.see(selected[0])
                except Exception:
                    pass
                self._schedule_tree_scrollbar_refresh()

            self.after_idle(restore_view)
        else:
            self._schedule_tree_scrollbar_refresh()

    def _item_remote_path(self, item_id: str) -> tuple[str, bool]:
        info = self.tree_item_info.get(item_id)
        if info:
            return info
        parts = []
        current = item_id
        while current:
            parts.append(self.tree.item(current, "text"))
            current = self.tree.parent(current)
        parts.reverse()
        path = normalize_remote_path("/" + "/".join(parts))
        is_file = self.tree.set(item_id, "type") == self.tr("file")
        return path, is_file

    def _selected_upload_target_root(self) -> str:
        selection = self.tree.selection()
        if not selection:
            return "/"
        selected_remote, selected_is_file = self._item_remote_path(selection[0])
        if selected_is_file:
            return normalize_remote_path("/".join(selected_remote.split("/")[:-1]) or "/")
        return normalize_remote_path(selected_remote)

    def _queue_append(self, task: UploadTask):
        with self.queue_lock:
            self.upload_queue.append(task)
        self.after(0, self.refresh_queue_tree)

    def queue_add_files(self):
        paths = filedialog.askopenfilenames(parent=self._prepare_dialog_parent())
        if not paths:
            return
        target_root = self._selected_upload_target_root()
        for file_path in paths:
            p = Path(file_path)
            task = UploadTask(local_path=p, remote_path=normalize_remote_path(f"{target_root}/{p.name}"), size=p.stat().st_size)
            self._queue_append(task)
        self.set_status(self.tr("queue_added"))

    def queue_add_folder(self):
        folder = filedialog.askdirectory(parent=self._prepare_dialog_parent())
        if not folder:
            return
        root = Path(folder)
        files = [p for p in root.rglob("*") if p.is_file()]
        if not files:
            self.show_warning(self.tr("warning"), self.tr("empty_folder"))
            return
        selection = self.tree.selection()
        selected_remote = None
        selected_is_file = False
        if selection:
            selected_remote, selected_is_file = self._item_remote_path(selection[0])
        if selected_remote:
            if selected_is_file:
                target_root = normalize_remote_path("/".join(selected_remote.split("/")[:-1]) or "/")
                preserve_local_folder_name = False
            else:
                target_root = normalize_remote_path(selected_remote)
                preserve_local_folder_name = True
        else:
            target_root = "/"
            preserve_local_folder_name = True
        root_name = root.name.strip("/\\")
        remote_base = normalize_remote_path(f"{target_root}/{root_name}" if root_name else target_root)
        for p in files:
            rel = p.relative_to(root).as_posix()
            remote_path = normalize_remote_path(f"{remote_base}/{rel}")
            task = UploadTask(local_path=p, remote_path=remote_path, size=p.stat().st_size)
            self._queue_append(task)
        self.set_status(self.tr("queue_added"))

    def refresh_queue_tree(self):
        selected = set(self.queue_tree.selection())
        self.queue_tree.delete(*self.queue_tree.get_children())
        failures = 0
        with self.queue_lock:
            tasks = list(self.upload_queue)
        for task in tasks:
            if task.status == "failed":
                failures += 1
            item = self.queue_tree.insert(
                "",
                "end",
                iid=task.task_id,
                text=task.local_path.name,
                values=(task.remote_path, self._task_status_label(task.status), f"{task.progress_pct:.0f}%", fmt_size(task.size)),
            )
            if item in selected:
                self.queue_tree.selection_add(item)
        self.failures_var.set(str(failures))
        self.update_fs_estimate()
        self.after_idle(self._resize_queue_tree_columns)
        self._schedule_queue_tree_scrollbar_refresh()
        if not tasks:
            self.current_file_var.set("-")
            self.overall_var.set("0 / 0")
            if not self.queue_running:
                self.set_status(self.tr("queue_idle"))

    def _task_status_label(self, status: str) -> str:
        mapping = {
            "waiting": self.tr("queue_waiting"),
            "uploading": self.tr("queue_uploading"),
            "done": self.tr("queue_done"),
            "failed": self.tr("queue_failed"),
            "cancelled": self.tr("queue_cancelled"),
            "retrying": self.tr("queue_retrying"),
        }
        return mapping.get(status, status)

    def remove_selected_tasks(self):
        if self.queue_running:
            self.show_warning(self.tr("warning"), self.tr("queue_running"))
            return
        selected = set(self.queue_tree.selection())
        if not selected:
            return
        with self.queue_lock:
            self.upload_queue = [t for t in self.upload_queue if t.task_id not in selected]
        self.refresh_both_views()

    def clear_completed_tasks(self):
        if self.queue_running:
            self.show_warning(self.tr("warning"), self.tr("queue_running"))
            return
        self._clear_completed_tasks_now()
        self.refresh_queue_tree()

    def _clear_completed_tasks_now(self):
        with self.queue_lock:
            self.upload_queue = [t for t in self.upload_queue if t.status not in {"done", "cancelled"}]

    def retry_failed_tasks(self):
        if self.queue_running:
            self.show_warning(self.tr("warning"), self.tr("queue_running"))
            return
        changed = False
        with self.queue_lock:
            for task in self.upload_queue:
                if task.status == "failed":
                    task.status = "waiting"
                    task.progress_pct = 0.0
                    task.uploaded_bytes = 0
                    task.error = ""
                    changed = True
        if changed:
            self.refresh_queue_tree()
            self.set_status(self.tr("queue_added"))

    def cancel_queue(self):
        if not self.queue_running:
            return
        self.cancel_event.set()
        self.set_status(self.tr("queue_cancel_requested"))


    def _current_used_bytes(self) -> int:
        return sum(rf.size for rf in self.files)

    def _estimated_total_bytes(self) -> int | None:
        if self.detected_fs_total_bytes is not None and self.detected_fs_total_bytes > 0:
            return self.detected_fs_total_bytes
        if self.spiffs_capacity_kb is None:
            return None
        return self.spiffs_capacity_kb * 1024

    def _estimated_free_bytes(self) -> int | None:
        total = self._estimated_total_bytes()
        if total is None:
            return None
        used = self._current_used_bytes()
        return max(0, total - used)

    def _pending_queue_bytes(self) -> int:
        with self.queue_lock:
            return sum(t.size for t in self.upload_queue if t.status in {"waiting", "retrying"})

    def update_fs_estimate(self):
        total = self._estimated_total_bytes()
        if total is None:
            self.fs_estimate_var.set(self.tr("fs_estimate_unknown"))
            return
        used = self._current_used_bytes()
        free = max(0, total - used)
        queue = self._pending_queue_bytes()
        if queue > free:
            key = "fs_estimate_full"
        elif free - queue < FS_SAFETY_FLOOR_BYTES:
            key = "fs_estimate_low"
        else:
            key = "fs_estimate_ok"
        self.fs_estimate_var.set(self.tr(key).format(
            profile=self.fs_profile_name,
            total=fmt_size(total),
            used=fmt_size(used),
            free=fmt_size(free),
            queue=fmt_size(queue),
        ))

    def _preflight_check_available_space(self) -> bool:
        free_bytes = self._estimated_free_bytes()
        pending_bytes = self._pending_queue_bytes()
        if free_bytes is None or pending_bytes <= 0:
            return True
        if pending_bytes > free_bytes:
            self.show_warning(
                self.tr("warning"),
                self.tr("space_check_insufficient").format(
                    free=fmt_size(free_bytes),
                    need=fmt_size(pending_bytes),
                ),
            )
            return False
        if free_bytes - pending_bytes < FS_SAFETY_FLOOR_BYTES:
            return self.ask_yes_no(
                self.tr("warning"),
                self.tr("space_check_low").format(
                    free=fmt_size(free_bytes),
                    need=fmt_size(pending_bytes),
                ),
            )
        return True

    def _is_critical_spiffs_write_error(self, error_text: str) -> bool:
        return is_probable_spiffs_open_failed(error_text)

    def _recover_wifi_connection(self, max_wait_seconds: float = RESTORE_RECOVERY_TIMEOUT) -> bool:
        deadline = time.time() + max(2.0, max_wait_seconds)
        while time.time() < deadline:
            try:
                self.client._request("GET", "/api/fs/ping", timeout=3.0)
                return True
            except Exception:
                pass
            try:
                connect_timeout = min(8.0, max(2.0, deadline - time.time()))
                self.client.connect(self.ip_var.get(), timeout=connect_timeout)
                self.client._request("GET", "/api/fs/ping", timeout=3.0)
                return True
            except Exception:
                time.sleep(0.6)
        return False

    def _prepare_radio_for_restore(self) -> bool:
        # Stop active playback so files (especially fonts/assets) are less likely
        # to stay open while restore is replacing them.
        try:
            self.client._request("GET", "/?stop=1", timeout=5.0)
            time.sleep(0.35)
            return True
        except Exception:
            return False

    def _resume_radio_after_restore(self):
        try:
            self.client._request("GET", "/?start=1", timeout=6.0)
        except Exception:
            pass

    def start_queue(self):
        if self.queue_running:
            self.show_warning(self.tr("warning"), self.tr("queue_running"))
            return
        with self.queue_lock:
            pending = [t for t in self.upload_queue if t.status in {"waiting", "retrying"}]
        if not pending:
            self.show_warning(self.tr("warning"), self.tr("queue_empty_start"))
            return
        if not self._preflight_check_available_space():
            return

        self.queue_stop_reason = None
        self.queue_running = True
        self.cancel_event.clear()
        self._set_queue_controls_enabled(False)
        self.set_status(self.tr("status_uploading"))

        def job():
            stop_sent = False
            try:
                self.ensure_connected()
                stop_sent = self._prepare_radio_for_restore()
                self._run_upload_queue()
                return stop_sent
            finally:
                self.queue_running = False

        def restore_controls_after_job():
            # If queue startup fails before done() runs (for example not connected),
            # make sure controls are not left in a disabled state.
            if not self.queue_running:
                self._set_queue_controls_enabled(True)

        def done(stop_sent):
            self._set_queue_controls_enabled(True)
            self._clear_completed_tasks_now()
            self.refresh_queue_tree()
            if self.queue_stop_reason:
                self.set_status(self.queue_stop_reason)
                self.show_warning(self.tr("warning"), self.queue_stop_reason)
            elif self.cancel_event.is_set():
                self.set_status(self.tr("queue_cancelled_done"))
            else:
                self.set_status(self.tr("queue_finished"))
            if AUTO_RESUME_AFTER_RESTORE and stop_sent:
                self._resume_radio_after_restore()
            self.cancel_event.clear()
            self.after(50, lambda: self.refresh_both_views(background=True))
            self._reset_queue_runtime_labels(keep_status=True)

        started = self.run_job(job, done, on_finally=restore_controls_after_job)
        if not started:
            self.queue_running = False
            self._set_queue_controls_enabled(True)

    def _set_queue_controls_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.after(0, lambda: self.btn_queue_add_files.config(state=state))
        self.after(0, lambda: self.btn_queue_add_folder.config(state=state))
        self.after(0, lambda: self.btn_queue_start.config(state=state))
        self.after(0, lambda: self.btn_queue_cancel.config(state=tk.NORMAL if not enabled else tk.DISABLED))
        self.after(0, lambda: self.btn_queue_remove.config(state=state))

    def _reset_queue_runtime_labels(self, keep_status: bool = False):
        self.queue_stop_reason = None
        self.progress_var.set(0.0)
        self.overall_progress_var.set(0.0)
        self.current_file_var.set("-")
        self.overall_var.set("0 / 0")
        self.speed_var.set("0 KB/s")
        self.eta_var.set("--:--")
        if not keep_status:
            self.set_status(self.tr("status_ready"))

    def _ensure_remote_parent_dirs(self, remote_path: str):
        parent = "/".join(normalize_remote_path(remote_path).split("/")[:-1]) or "/"
        if parent == "/":
            return
        current_path = ""
        for part in [p for p in parent.strip("/").split("/") if p]:
            current_path += "/" + part
            if current_path in self.known_remote_dirs:
                continue
            try:
                self.client.mkdir(current_path)
            except Exception as e:
                msg = str(e).lower()
                if not any(token in msg for token in ("exists", "exist", "already", "mkdir", "bad mkdir reply")):
                    raise
            self.known_remote_dirs.add(current_path)

    def _run_upload_queue(self):
        with self.queue_lock:
            tasks = [t for t in self.upload_queue if t.status in {"waiting", "retrying"}]
            total_bytes = sum(t.size for t in tasks)
        sent_before = 0
        queue_start = time.time()
        total_count = len(tasks)
        current_index = 0
        for task in tasks:
            current_index += 1
            if self.cancel_event.is_set():
                self._mark_waiting_as_cancelled()
                break
            self.current_queue_task_id = task.task_id
            self.after(0, lambda n=task.local_path.name: self.current_file_var.set(n))
            self.after(0, lambda i=current_index, tc=total_count: self.overall_var.set(f"{i} / {tc}"))
            ok = self._upload_single_task(task, current_index, total_count, sent_before, total_bytes, queue_start)
            sent_before += task.size if ok else task.uploaded_bytes
        self.current_queue_task_id = None

    def _mark_waiting_as_cancelled(self):
        with self.queue_lock:
            for task in self.upload_queue:
                if task.status in {"waiting", "retrying"}:
                    task.status = "cancelled"
        self.after(0, self.refresh_queue_tree)

    def _set_transfer_metrics(self, current_name: str, current_index: int, total_count: int, bytes_done: int, bytes_total: int, start_time: float):
        elapsed = max(0.25, time.time() - start_time)
        speed = bytes_done / elapsed if bytes_done > 0 else 0.0
        eta = (max(0, bytes_total - bytes_done) / speed) if speed > 0 and bytes_done >= 512 else None
        pct = 100.0 if bytes_total == 0 else (bytes_done / bytes_total) * 100.0
        self.after(0, lambda n=current_name: self.current_file_var.set(n))
        self.after(0, lambda i=current_index, tc=total_count: self.overall_var.set(f"{i} / {tc}"))
        self.after(0, lambda p=pct: self.progress_var.set(p))
        self.after(0, lambda p=pct: self.overall_progress_var.set(p))
        self.after(0, lambda s=human_speed(speed): self.speed_var.set(s))
        self.after(0, lambda e=format_eta(eta): self.eta_var.set(e))

    def _reset_transfer_metrics(self):
        self.progress_var.set(0.0)
        self.overall_progress_var.set(0.0)
        self.current_file_var.set("-")
        self.overall_var.set("0 / 0")
        self.speed_var.set("0 KB/s")
        self.eta_var.set("--:--")

    def _upload_single_task(self, task: UploadTask, current_index: int, total_count: int, sent_before: int, total_bytes: int, queue_start: float) -> bool:
        local_bytes = task.local_path.read_bytes()
        last_error = None
        for attempt in range(task.retries_done, task.max_retries + 1):
            if self.cancel_event.is_set():
                task.status = "cancelled"
                self.after(0, self.refresh_queue_tree)
                return False
            task.status = "uploading" if attempt == 0 else "retrying"
            task.error = ""
            task.progress_pct = 0.0
            task.uploaded_bytes = 0
            self.after(0, self.refresh_queue_tree)
            try:
                self._ensure_remote_parent_dirs(task.remote_path)
                file_start = time.time()
                for chunk_idx, chunk_total, uploaded in self.client.write_file(task.remote_path, local_bytes):
                    if self.cancel_event.is_set():
                        try:
                            self.client.abort_write()
                        except Exception:
                            pass
                        task.status = "cancelled"
                        self.after(0, self.refresh_queue_tree)
                        return False
                    task.uploaded_bytes = uploaded
                    task.progress_pct = 100.0 if task.size == 0 else (uploaded / max(1, task.size)) * 100.0
                    elapsed = max(0.001, time.time() - queue_start)
                    total_sent_now = sent_before + uploaded
                    speed = total_sent_now / elapsed
                    remaining = max(0, total_bytes - total_sent_now)
                    eta = remaining / speed if speed > 0 else None
                    self.after(0, lambda p=task.progress_pct: self.progress_var.set(p))
                    overall_pct = 100.0 if total_bytes == 0 else (total_sent_now / total_bytes) * 100.0
                    self.after(0, lambda p=overall_pct: self.overall_progress_var.set(p))
                    self.after(0, lambda s=human_speed(speed): self.speed_var.set(s))
                    self.after(0, lambda e=format_eta(eta): self.eta_var.set(e))
                    self.set_status(f"{self.tr('status_uploading')} {current_index}/{total_count} - {task.remote_path}")
                    self.after(0, self.refresh_queue_tree)
                task.status = "done"
                task.progress_pct = 100.0
                task.uploaded_bytes = task.size
                self._remember_remote_path(task.remote_path, task.size, False)
                self.after(0, self.refresh_queue_tree)
                return True
            except Exception as e:
                task.retries_done = attempt + 1
                raw_error = str(e)
                if self._is_critical_spiffs_write_error(raw_error):
                    localized = build_open_failed_hint(self._localize_error(raw_error), self.tr("open_failed_hint"))
                    task.error = localized
                    task.status = "failed"
                    self.queue_stop_reason = self.tr("critical_spiffs_write_error") + "\n\n" + localized
                    self.cancel_event.set()
                    self.after(0, self.refresh_queue_tree)
                    return False
                task.error = self._localize_error(raw_error)
                last_error = e
                if attempt < task.max_retries and not self.cancel_event.is_set():
                    if is_probable_transient_upload_disconnect(raw_error):
                        self._recover_wifi_connection()
                    task.status = "retrying"
                    self.set_status(f"{self.tr('queue_retrying')}: {task.remote_path} | {self._localize_error(raw_error)}")
                    self.after(0, self.refresh_queue_tree)
                    time.sleep(0.5 * (attempt + 1))
                    continue
                task.status = "failed"
                self.after(0, self.refresh_queue_tree)
                return False
        if last_error:
            task.error = str(last_error)
        task.status = "failed"
        self.after(0, self.refresh_queue_tree)
        return False

    def refresh_both_views(self, background: bool = False):
        def job():
            if self.client.ser:
                files = self.client.list_files()
            else:
                files = self.files
            return files

        tree_state = self._capture_tree_state()

        def done(files):
            files = self._apply_known_remote_paths(files)
            self.files = files
            self._rebuild_known_remote_dirs(files)
            self.populate_tree(restore_state=tree_state)
            self.refresh_queue_tree()

        if background:
            if self.worker and self.worker.is_alive():
                self.after(100, lambda: self.refresh_both_views(background=True))
                return
            self.run_job(job, done)
        else:
            done(self.client.list_files() if self.client.ser else self.files)

    def backup_zip(self):
        stamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        initial_name = f"radio_FS_mentes_{stamp}.zip" if self.lang == "HU" else f"radio_FS_backup_{stamp}.zip"
        out = filedialog.asksaveasfilename(
            title=self.tr("save_backup_title"),
            defaultextension=".zip",
            filetypes=[("ZIP", "*.zip")],
            initialfile=initial_name,
            parent=self._prepare_dialog_parent(),
        )
        if not out:
            return
        out_path = Path(out)

        def job():
            self.ensure_connected()
            stop_sent = self._prepare_radio_for_restore()
            try:
                files = self._apply_known_remote_paths(self.client.list_files())
                if not files:
                    raise ProtoError(self.tr("no_files"))
                self.set_status(self.tr("status_saving"))
                backup_files = [rf for rf in files if not getattr(rf, "is_dir", False)]
                if not backup_files:
                    raise ProtoError(self.tr("no_files"))
                backup_dirs = {normalize_remote_path(rf.path) for rf in files if getattr(rf, "is_dir", False)}
                for rf in backup_files:
                    parts = [part for part in normalize_remote_path(rf.path).strip("/").split("/") if part]
                    current = ""
                    for part in parts[:-1]:
                        current += "/" + part
                        backup_dirs.add(current)
                total_files = len(backup_files)
                total_bytes = sum(rf.size for rf in backup_files)
                transferred = 0
                start = time.time()
                manifest = []
                self.after(0, self._reset_transfer_metrics)
                with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for dir_path in sorted(backup_dirs, key=lambda x: (x.count("/"), x.lower())):
                        arcname = dir_path.strip("/")
                        if arcname:
                            zf.writestr(arcname.rstrip("/") + "/", b"")
                    for idx, rf in enumerate(backup_files, 1):
                        remote_path = normalize_remote_path(rf.path)
                        expected_size = int(getattr(rf, "size", 0))
                        arcname = remote_path.lstrip("/")
                        data = self.client.read_file_retry(remote_path, expected_size=expected_size)
                        zf.writestr(arcname, data)
                        manifest.append((remote_path, arcname, expected_size))
                        transferred += len(data)
                        self._set_transfer_metrics(Path(remote_path).name, idx, total_files, transferred, total_bytes, start)
                        self.set_status(f"{self.tr('status_saving')} {idx}/{total_files} - {remote_path}")

                if self.verify_backup_var.get():
                    transferred = 0
                    start = time.time()
                    self.after(0, self._reset_transfer_metrics)
                    with zipfile.ZipFile(out_path, "r") as zf:
                        for idx, (remote_path, arcname, expected_size) in enumerate(manifest, 1):
                            saved_data = zf.read(arcname)
                            live_data = self.client.read_file_retry(remote_path, expected_size=expected_size)
                            if live_data != saved_data:
                                raise ProtoError(self.tr("backup_verify_failed").format(path=remote_path))
                            transferred += len(saved_data)
                            self._set_transfer_metrics(Path(remote_path).name, idx, total_files, transferred, total_bytes, start)
                            self.set_status(f"{self.tr('status_verifying')} {idx}/{total_files} - {remote_path}")
                    return "verified"
                return "done"
            finally:
                if AUTO_RESUME_AFTER_RESTORE and stop_sent:
                    self._resume_radio_after_restore()

        def done(result):
            self._reset_transfer_metrics()
            self.refresh_both_views(background=True)
            message = self.tr("backup_verified") if result == "verified" else self.tr("backup_done")
            self.set_status(message)
            self.show_info(self.tr("done"), message)

        self.run_job(job, done)

    def restore_zip(self):
        zpath = filedialog.askopenfilename(title=self.tr("open_backup_title"), filetypes=[("ZIP", "*.zip")], parent=self._prepare_dialog_parent())
        if not zpath:
            return
        zp = Path(zpath)

        def job():
            self.ensure_connected()
            self.set_status(self.tr("status_restoring"))
            stop_sent = self._prepare_radio_for_restore()
            current = self._apply_known_remote_paths(self.client.list_files())
            current_files = {normalize_remote_path(rf.path) for rf in current if not getattr(rf, "is_dir", False)}
            current_dirs = {normalize_remote_path(rf.path) for rf in current if getattr(rf, "is_dir", False)}
            with zipfile.ZipFile(zp, "r") as zf:
                infos = [info for info in zf.infolist() if not info.is_dir()]
                names = [info.filename for info in infos]
                restore_paths = {normalize_remote_path("/" + name) for name in names}
                total_files = max(1, len(names))
                total_bytes = sum(int(info.file_size) for info in infos) if infos else 0
                transferred = 0
                start = time.time()
                self.after(0, self._reset_transfer_metrics)
                for idx, info in enumerate(infos, 1):
                    name = info.filename
                    data = zf.read(name)
                    remote_path = normalize_remote_path("/" + name)
                    self._ensure_remote_parent_dirs(remote_path)
                    uploaded = 0
                    for attempt in range(TRANSIENT_UPLOAD_RETRIES + 1):
                        chunk_size = RESTORE_UPLOAD_ATTEMPT_CHUNKS[min(attempt, len(RESTORE_UPLOAD_ATTEMPT_CHUNKS) - 1)]
                        try:
                            for _, _, uploaded in self.client.write_file(
                                remote_path,
                                data,
                                chunk_sizes=(chunk_size,),
                                write_data_timeout=90.0,
                                inter_chunk_delay=0.0,
                            ):
                                self._set_transfer_metrics(Path(name).name, idx, total_files, transferred + uploaded, total_bytes, start)
                                self.set_status(f"{self.tr('status_restoring')} {idx}/{total_files} - {remote_path}")
                            break
                        except Exception as e:
                            raw_error = str(e)
                            transient = is_probable_transient_upload_disconnect(raw_error)
                            if not transient or attempt >= TRANSIENT_UPLOAD_RETRIES:
                                raise
                            self.set_status(
                                f"{self.tr('queue_retrying')}: {remote_path} ({attempt + 1}/{TRANSIENT_UPLOAD_RETRIES}) | {self._localize_error(raw_error)}"
                            )
                            recovered = self._recover_wifi_connection()
                            if recovered:
                                self._prepare_radio_for_restore()
                            time.sleep(0.4 * (attempt + 1))
                    # Remember the exact restored path immediately.  Some firmwares
                    # briefly return basename-only rows right after a restore; this keeps
                    # the first GUI refresh in the same folder structure as the ZIP.
                    self._remember_remote_path(remote_path, len(data), False)
                    time.sleep(RESTORE_FILE_SETTLE_DELAY)
                    transferred += len(data)
                    current_files.discard(remote_path)

            extra_files = current_files - restore_paths
            for target in sorted(extra_files, key=lambda x: (x.count("/"), x.lower()), reverse=True):
                try:
                    self.client.delete_file(target)
                    self._forget_remote_path_tree(target)
                except Exception:
                    pass
            for target in sorted(current_dirs, key=lambda x: (x.count("/"), x.lower()), reverse=True):
                if target == "/":
                    continue
                prefix = target.rstrip("/") + "/"
                if any(path == target or path.startswith(prefix) for path in restore_paths):
                    continue
                try:
                    self.client.rmdir(target)
                    self._forget_remote_path_tree(target)
                except Exception:
                    pass
            # Give the ESP32 webserver/filesystem a short moment to finish exposing
            # the final directory view, then return a fresh list for the GUI.
            time.sleep(0.4)
            try:
                return self.client.list_files(), stop_sent
            except Exception:
                return list(self.files), stop_sent

        def done(result):
            files, stop_sent = result
            self._reset_transfer_metrics()
            files = self._apply_known_remote_paths(files)
            self.files = files
            self._rebuild_known_remote_dirs(files)
            self.populate_tree()
            self.refresh_queue_tree()
            self.update_fs_estimate()
            if AUTO_RESUME_AFTER_RESTORE and stop_sent:
                self._resume_radio_after_restore()
            self.show_info(self.tr("done"), self.tr("restore_done"))

        self.run_job(job, done)

    def create_directory(self):
        base = self._selected_upload_target_root()
        name = simpledialog.askstring(
            self.tr("mkdir"),
            self.tr("enter_dir_name"),
            parent=self._prepare_dialog_parent(),
        )
        if name is None:
            return
        name = name.strip().strip("/\\")
        if not name:
            return
        remote_path = normalize_remote_path(base.rstrip("/") + "/" + name if base != "/" else "/" + name)

        def job():
            self.ensure_connected()
            self.set_status(self.tr("status_mkdir"))
            self.client.mkdir(remote_path)
            return True

        def done(_):
            self._remember_remote_path(remote_path, 0, True)
            self.refresh_both_views(background=True)
            self.show_info(self.tr("done"), self.tr("mkdir_done"))

        self.run_job(job, done)

    def download_selected(self):
        selection = self.tree.selection()
        if not selection:
            self.show_warning(self.tr("warning"), self.tr("download_select_file"))
            return
        path, is_file = self._item_remote_path(selection[0])
        if not is_file:
            self.show_warning(self.tr("warning"), self.tr("download_select_file"))
            return
        out = filedialog.asksaveasfilename(title=self.tr("save_selected_title"), initialfile=Path(path).name, parent=self._prepare_dialog_parent())
        if not out:
            return
        out_path = Path(out)

        def job():
            self.ensure_connected()
            self.set_status(self.tr("status_downloading"))
            expected_size = next((rf.size for rf in self.files if normalize_remote_path(rf.path) == normalize_remote_path(path)), None)
            data = self.client.read_file_retry(path, expected_size=expected_size)
            out_path.write_bytes(data)
            return True

        def done(_):
            self.refresh_both_views(background=True)
            self.show_info(self.tr("done"), self.tr("download_done"))

        self.run_job(job, done)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            self.show_warning(self.tr("warning"), self.tr("tree_no_selection"))
            return

        selected_items = [self._item_remote_path(item_id) for item_id in selection]
        if any(path == "/" for path, _ in selected_items):
            self.show_warning(self.tr("warning"), self.tr("root_delete_blocked"))
            return

        preview_paths = [normalize_remote_path(path) for path, _ in selected_items]
        preview_limit = 6
        preview_lines = preview_paths[:preview_limit]
        if len(preview_paths) > preview_limit:
            preview_lines.append("...")
        preview_text = "\n".join(preview_lines)
        if not self.ask_yes_no(
            self.tr("warning"),
            self.tr("delete_confirm").format(count=len(preview_paths), items=preview_text),
        ):
            return

        def job():
            self.ensure_connected()
            stop_sent = self._prepare_radio_for_restore()
            self.set_status(self.tr("status_deleting"))
            try:
                files = self._apply_known_remote_paths(self.client.list_files())
                all_file_paths = [f.path for f in files if not getattr(f, "is_dir", False)]
                all_dir_paths = [f.path for f in files if getattr(f, "is_dir", False)]
                target_files = set()
                target_dirs = set()
                requested_paths = []
                for path, is_file in selected_items:
                    path = normalize_remote_path(path)
                    requested_paths.append((path, is_file))
                    if is_file:
                        target_files.add(path)
                    else:
                        prefix = path.rstrip("/") + "/"
                        for file_path in all_file_paths:
                            if file_path == path or file_path.startswith(prefix):
                                target_files.add(file_path)
                        for dir_path in all_dir_paths:
                            if dir_path == path or dir_path.startswith(prefix):
                                target_dirs.add(dir_path)
                        target_dirs.add(path)

                for target in sorted(target_files, key=lambda x: (x.count("/"), x.lower()), reverse=True):
                    self.client.delete_file(target)

                dir_errors = []
                for target in sorted(target_dirs, key=lambda x: (x.count("/"), x.lower()), reverse=True):
                    if target == "/":
                        continue
                    try:
                        self.client.delete_file(target)
                    except Exception as delete_error:
                        try:
                            self.client.rmdir(target)
                        except Exception as rmdir_error:
                            dir_errors.append(f"{target}: {rmdir_error or delete_error}")

                for path, _ in requested_paths:
                    self._forget_remote_path_tree(path)
                remaining = self._apply_known_remote_paths(self.client.list_files())
                remaining_paths = [f.path for f in remaining]
                still_present = []
                for path, is_file in requested_paths:
                    if is_file:
                        if path in remaining_paths:
                            still_present.append(path)
                    else:
                        prefix = path.rstrip("/") + "/"
                        for remote_path in remaining_paths:
                            if remote_path == path or remote_path.startswith(prefix):
                                still_present.append(remote_path)
                                break
                if still_present:
                    detail = still_present[0]
                    if dir_errors:
                        detail += " | " + dir_errors[0]
                    raise ProtoError(f"delete verification failed: {detail}")
                return True
            finally:
                if AUTO_RESUME_AFTER_RESTORE and stop_sent:
                    self._resume_radio_after_restore()

        def done(_):
            self.refresh_both_views(background=True)
            self.show_info(self.tr("done"), self.tr("delete_done"))

        self._set_busy_cursor(True)
        self.run_job(job, done, on_finally=lambda: self._set_busy_cursor(False))

    def reboot_radio(self):
        def job():
            self.ensure_connected()
            self.set_status(self.tr("status_rebooting"))
            self.client.reboot()
            return True

        def done(_):
            self.disconnect()
            self.show_info(self.tr("done"), self.tr("reboot_done"))

        self.run_job(job, done)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
