"""Modern cross-platform GUI for GeoTagCopy using CustomTkinter."""

import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox
from io import BytesIO
from typing import Optional

import customtkinter as ctk
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    from tkintermapview import TkinterMapView
except ImportError:
    TkinterMapView = None

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    # The app still runs without HEIC support; HEIC previews will use placeholders.
    pass

from geotagcopy.core import (
    LocationGroup,
    GeoMatch,
    MediaFile,
    apply_gps_tags,
    check_exiftool,
    format_time_diff,
    group_matches,
    match_files,
    read_metadata,
    scan_folder,
)
from geotagcopy.support import open_support_page, should_show_support

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE = ("", 22, "bold")
FONT_HEADING = ("", 15, "bold")
FONT_BODY = ("", 13)
FONT_SMALL = ("", 12)
FONT_BADGE = ("", 11, "bold")
FONT_MONO = ("Courier", 12)

COLOR_GROUP_BG = ("#e8ecf1", "#2a2d32")
COLOR_CARD_BG = ("#f6f7f9", "#22252a")
COLOR_LOCATION = ("#1a6dcc", "#5da4f0")
COLOR_DONOR = ("#555555", "#b0b0b0")
COLOR_TIMEDIFF = ("#996600", "#e6a800")
COLOR_SUCCESS = ("#1a8c1a", "#3dcc3d")
COLOR_BADGE_TEXT = ("#101418", "#101418")

DONOR_ACCENTS = [
    ("#b7791f", "#f2b705"),
    ("#0f8f78", "#1fc7a6"),
    ("#c24141", "#f06a6a"),
    ("#4f74c8", "#8ab4ff"),
    ("#9b4ec4", "#d17aff"),
    ("#5f9d3d", "#91d36e"),
    ("#c76522", "#ff8f3d"),
]

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "tif", "tiff"}
VIDEO_EXTENSIONS = {"mov", "mp4", "m4v", "avi"}

_UNIT_HOURS_FACTOR = {"min": 1 / 60, "hour": 1.0, "day": 24.0}
_UNIT_SLIDER_MAX = {"min": 43200, "hour": 720, "day": 30}
_UNIT_SLIDER_STEPS = {"min": 720, "hour": 720, "day": 60}


class GeoTagCopyApp(ctk.CTk):
    def __init__(self, tagged_folder: str = "", untagged_folder: str = ""):
        super().__init__()

        self.title("GeoTagCopy")
        self.geometry("960x720")
        self.minsize(750, 550)

        self.groups: list[LocationGroup] = []
        self._source_matches: list[GeoMatch] = []
        self.match_vars: dict[str, tk.BooleanVar] = {}
        self._group_widgets: list[ctk.CTkFrame] = []
        self._thumbnail_cache: dict[tuple[str, int, int], ctk.CTkImage] = {}
        self._filter_refresh_after_id: Optional[str] = None
        self._suppress_time_filter_refresh = False
        self.page_size = 60
        self.current_page = 0
        self.total_pages = 1

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_input_section()
        self._build_status_section()
        self._build_results_section()
        self._build_action_section()

        if tagged_folder:
            self.tagged_var.set(tagged_folder)
        if untagged_folder:
            self.untagged_var.set(untagged_folder)

    # -- UI construction -------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            title_frame, text="GeoTagCopy", font=FONT_TITLE
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Copy GPS coordinates from geotagged photos to untagged ones",
            font=FONT_SMALL,
            text_color=("gray50", "gray60"),
        ).pack(anchor="w")

        if should_show_support():
            ctk.CTkButton(
                header,
                text="Support",
                width=96,
                height=34,
                command=open_support_page,
            ).grid(row=0, column=1, padx=(12, 0), sticky="e")
            self._build_support_menu()

    def _build_support_menu(self):
        menu_bar = tk.Menu(self)
        support_menu = tk.Menu(menu_bar, tearoff=False)
        support_menu.add_command(label="Support GeoTagCopy", command=open_support_page)
        menu_bar.add_cascade(label="Support", menu=support_menu)
        self.configure(menu=menu_bar)

    def _build_input_section(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Tagged photos folder:", font=FONT_BODY).grid(
            row=0, column=0, padx=(16, 8), pady=(12, 4), sticky="w"
        )
        self.tagged_var = tk.StringVar()
        tagged_entry = ctk.CTkEntry(
            frame, textvariable=self.tagged_var, font=FONT_BODY, height=32
        )
        tagged_entry.grid(row=0, column=1, padx=4, pady=(12, 4), sticky="ew")
        ctk.CTkButton(
            frame,
            text="Browse",
            width=80,
            height=32,
            command=lambda: self._browse(self.tagged_var),
        ).grid(row=0, column=2, padx=(4, 16), pady=(12, 4))

        ctk.CTkLabel(frame, text="Untagged photos folder:", font=FONT_BODY).grid(
            row=1, column=0, padx=(16, 8), pady=4, sticky="w"
        )
        self.untagged_var = tk.StringVar()
        untagged_entry = ctk.CTkEntry(
            frame, textvariable=self.untagged_var, font=FONT_BODY, height=32
        )
        untagged_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            frame,
            text="Browse",
            width=80,
            height=32,
            command=lambda: self._browse(self.untagged_var),
        ).grid(row=1, column=2, padx=(4, 16), pady=4)

        time_row = ctk.CTkFrame(frame, fg_color="transparent")
        time_row.grid(row=2, column=0, columnspan=3, padx=16, pady=(4, 4), sticky="ew")

        ctk.CTkLabel(time_row, text="Max time diff:", font=FONT_BODY).pack(
            side="left"
        )

        self._max_diff_hours = 24.0

        self._time_diff_entry = ctk.CTkEntry(
            time_row, width=72, height=32, font=FONT_BODY, justify="right"
        )
        self._time_diff_entry.pack(side="left", padx=(8, 4))
        self._time_diff_entry.insert(0, "24")
        self._time_diff_entry.bind("<Return>", self._on_time_entry_confirm)
        self._time_diff_entry.bind("<FocusOut>", self._on_time_entry_confirm)

        self._time_unit_btn = ctk.CTkSegmentedButton(
            time_row,
            values=["min", "hour", "day"],
            command=self._on_time_unit_change,
            font=FONT_SMALL,
        )
        self._time_unit_btn.set("hour")
        self._time_unit_btn.pack(side="left", padx=(0, 8))

        self._time_diff_slider = ctk.CTkSlider(
            time_row,
            from_=0,
            to=720,
            number_of_steps=720,
            command=self._on_time_slider_change,
        )
        self._time_diff_slider.set(24)
        self._time_diff_slider.pack(side="left", fill="x", expand=True)

        self.scan_btn = ctk.CTkButton(
            frame,
            text="Scan & Match",
            font=FONT_HEADING,
            height=40,
            command=self._scan_and_match,
        )
        self.scan_btn.grid(
            row=3, column=0, columnspan=3, padx=16, pady=(8, 14), sticky="ew"
        )

        session_actions = ctk.CTkFrame(frame, fg_color="transparent")
        session_actions.grid(
            row=4, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="ew"
        )
        session_actions.grid_columnconfigure(0, weight=1)

        self.load_results_btn = ctk.CTkButton(
            session_actions,
            text="Load Results",
            width=120,
            height=32,
            command=self._load_results,
        )
        self.load_results_btn.grid(row=0, column=0, sticky="w")

        self.save_results_btn = ctk.CTkButton(
            session_actions,
            text="Save Results",
            width=120,
            height=32,
            state="disabled",
            command=self._save_results,
        )
        self.save_results_btn.grid(row=0, column=1, sticky="e")

    def _build_status_section(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=20, pady=2, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            frame, text="Ready", font=FONT_SMALL, anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.progress = ctk.CTkProgressBar(frame, height=6)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.progress.set(0)

    def _build_results_section(self):
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.results_frame.grid(row=3, column=0, padx=20, pady=8, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)

        self.placeholder = ctk.CTkLabel(
            self.results_frame,
            text="Select two folders and click Scan & Match to begin",
            font=FONT_BODY,
            text_color=("gray50", "gray60"),
        )
        self.placeholder.grid(row=0, column=0, pady=40)

    def _build_action_section(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=4, column=0, padx=20, pady=(4, 16), sticky="ew")

        self.select_all_btn = ctk.CTkButton(
            frame,
            text="Select All",
            width=110,
            height=36,
            state="disabled",
            command=self._select_all,
        )
        self.select_all_btn.pack(side="left", padx=(0, 6))

        self.deselect_all_btn = ctk.CTkButton(
            frame,
            text="Deselect All",
            width=110,
            height=36,
            state="disabled",
            command=self._deselect_all,
        )
        self.deselect_all_btn.pack(side="left", padx=6)

        self.prev_page_btn = ctk.CTkButton(
            frame,
            text="< Prev",
            width=88,
            height=32,
            state="disabled",
            command=self._prev_page,
        )
        self.prev_page_btn.pack(side="left", padx=(12, 4))

        self.page_label = ctk.CTkLabel(
            frame,
            text="Page 1/1",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
        )
        self.page_label.pack(side="left", padx=4)

        self.next_page_btn = ctk.CTkButton(
            frame,
            text="Next >",
            width=88,
            height=32,
            state="disabled",
            command=self._next_page,
        )
        self.next_page_btn.pack(side="left", padx=(4, 0))

        self.apply_btn = ctk.CTkButton(
            frame,
            text="Apply GPS Tags",
            width=160,
            height=40,
            font=FONT_HEADING,
            fg_color=("#1a8c1a", "#2d7a2d"),
            hover_color=("#147014", "#236023"),
            state="disabled",
            command=self._apply_tags,
        )
        self.apply_btn.pack(side="right", padx=(6, 0))

    # -- Actions ---------------------------------------------------------

    def _browse(self, var: tk.StringVar):
        folder = filedialog.askdirectory(
            initialdir=var.get() or "~",
            title="Select folder",
        )
        if folder:
            var.set(folder)

    def _set_status(self, text: str, progress: Optional[float] = None):
        self.status_label.configure(text=text)
        if progress is not None:
            self.progress.set(progress)

    def _on_time_slider_change(self, value: float):
        unit = self._time_unit_btn.get()
        self._max_diff_hours = value * _UNIT_HOURS_FACTOR[unit]
        self._update_time_entry_display(value, unit)
        self._schedule_refilter_results()

    def _on_time_entry_confirm(self, _event=None):
        try:
            value = float(self._time_diff_entry.get())
        except ValueError:
            return
        value = max(0.0, value)
        unit = self._time_unit_btn.get()
        self._max_diff_hours = value * _UNIT_HOURS_FACTOR[unit]
        clamped = min(value, _UNIT_SLIDER_MAX[unit])
        self._time_diff_slider.set(clamped)
        self._schedule_refilter_results()

    def _on_time_unit_change(self, new_unit: str):
        display = self._max_diff_hours / _UNIT_HOURS_FACTOR[new_unit]
        self._time_diff_slider.configure(
            to=_UNIT_SLIDER_MAX[new_unit],
            number_of_steps=_UNIT_SLIDER_STEPS[new_unit],
        )
        self._time_diff_slider.set(min(display, _UNIT_SLIDER_MAX[new_unit]))
        self._update_time_entry_display(display, new_unit)
        self._schedule_refilter_results()

    def _update_time_entry_display(self, value: float, unit: str):
        if unit == "min":
            text = str(int(round(value)))
        elif value == int(value):
            text = str(int(value))
        else:
            text = f"{value:.1f}"
        self._time_diff_entry.delete(0, "end")
        self._time_diff_entry.insert(0, text)

    def _set_time_filter_display(self, hours: float, unit: str):
        if unit not in _UNIT_HOURS_FACTOR:
            unit = "day" if hours >= 24 else "hour"
        self._max_diff_hours = max(0.0, hours)
        display = self._max_diff_hours / _UNIT_HOURS_FACTOR[unit]
        self._suppress_time_filter_refresh = True
        try:
            self._time_unit_btn.set(unit)
            self._time_diff_slider.configure(
                to=_UNIT_SLIDER_MAX[unit],
                number_of_steps=_UNIT_SLIDER_STEPS[unit],
            )
            self._time_diff_slider.set(min(display, _UNIT_SLIDER_MAX[unit]))
            self._update_time_entry_display(display, unit)
        finally:
            self._suppress_time_filter_refresh = False

    def _schedule_refilter_results(self):
        if self._suppress_time_filter_refresh:
            return
        if not self._source_matches:
            return
        if self._filter_refresh_after_id is not None:
            self.after_cancel(self._filter_refresh_after_id)
        self._filter_refresh_after_id = self.after(250, self._refilter_results)

    def _refilter_results(self):
        self._filter_refresh_after_id = None
        if not self._source_matches:
            return

        self.groups = group_matches(self._filtered_source_matches())
        self.current_page = 0
        self._display_groups()

        shown = len(self._all_matches())
        total = len(self._source_matches)
        self._set_status(
            f"Showing {shown}/{total} matches within {format_time_diff(self._max_diff_hours)}",
            1.0,
        )

    def _filtered_source_matches(self) -> list[GeoMatch]:
        return [
            match
            for match in self._source_matches
            if match.time_diff_hours <= self._max_diff_hours
        ]

    def _scan_and_match(self):
        tagged_folder = self.tagged_var.get().strip()
        untagged_folder = self.untagged_var.get().strip()

        if not tagged_folder or not untagged_folder:
            messagebox.showwarning(
                "Missing folders", "Please select both tagged and untagged folders."
            )
            return

        if not check_exiftool():
            messagebox.showerror(
                "ExifTool not found",
                "ExifTool must be bundled with GeoTagCopy or available on PATH.\n"
                "Install from https://exiftool.org/",
            )
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.apply_btn.configure(state="disabled")
        self.select_all_btn.configure(state="disabled")
        self.deselect_all_btn.configure(state="disabled")
        self.save_results_btn.configure(state="disabled")
        self._source_matches = []
        self.groups = []

        max_time_diff_hours = self._max_diff_hours
        thread = threading.Thread(
            target=self._scan_worker,
            args=(tagged_folder, untagged_folder, max_time_diff_hours),
            daemon=True,
        )
        thread.start()

    def _scan_worker(
        self,
        tagged_folder: str,
        untagged_folder: str,
        max_time_diff_hours: float,
    ):
        try:
            self.after(0, self._set_status, "Scanning tagged folder...", 0.05)
            tagged_paths = scan_folder(tagged_folder)

            self.after(0, self._set_status, "Scanning untagged folder...", 0.10)
            untagged_paths = scan_folder(untagged_folder)

            if not tagged_paths:
                self.after(
                    0, self._set_status, "No media files found in tagged folder.", 0.0
                )
                self.after(0, self._reset_scan_btn)
                return

            if not untagged_paths:
                self.after(
                    0, self._set_status, "No media files found in untagged folder.", 0.0
                )
                self.after(0, self._reset_scan_btn)
                return

            def tagged_progress(done, _total):
                frac = 0.10 + 0.35 * (done / len(tagged_paths))
                self.after(
                    0,
                    self._set_status,
                    f"Reading tagged metadata... {done}/{len(tagged_paths)}",
                    frac,
                )

            tagged_files = read_metadata(tagged_paths, tagged_progress)

            def untagged_progress(done, _total):
                frac = 0.45 + 0.35 * (done / len(untagged_paths))
                self.after(
                    0,
                    self._set_status,
                    f"Reading untagged metadata... {done}/{len(untagged_paths)}",
                    frac,
                )

            untagged_files = read_metadata(untagged_paths, untagged_progress)

            self.after(0, self._set_status, "Matching files...", 0.85)
            matches = match_files(
                tagged_files, untagged_files,
                max_time_diff_hours=max_time_diff_hours,
            )

            self.after(0, self._set_status, "Grouping by location...", 0.95)
            self._source_matches = matches
            self.groups = group_matches(self._filtered_source_matches())
            self.current_page = 0

            n_matches = sum(len(g.matches) for g in self.groups)
            total_matches = len(self._source_matches)
            msg = (
                f"Done: showing {n_matches}/{total_matches} file(s) within "
                f"{format_time_diff(self._max_diff_hours)} across "
                f"{len(self.groups)} location group(s)"
            )
            self.after(0, self._set_status, msg, 1.0)
            self.after(0, self._display_groups)
            self.after(0, self._reset_scan_btn)

        except Exception as e:
            self.after(0, self._set_status, f"Error: {e}", 0.0)
            self.after(0, self._reset_scan_btn)

    def _reset_scan_btn(self):
        self.scan_btn.configure(state="normal", text="Scan & Match")

    # -- Results display -------------------------------------------------

    def _clear_results_widgets(self):
        for w in self._group_widgets:
            w.destroy()
        self._group_widgets.clear()
        self.match_vars.clear()
        self._thumbnail_cache.clear()

        if hasattr(self, "placeholder") and self.placeholder.winfo_exists():
            self.placeholder.destroy()

    def _display_groups(self):
        self._clear_results_widgets()

        if not self.groups:
            if self._source_matches:
                text = (
                    f"No matches within {format_time_diff(self._max_diff_hours)}.\n"
                    "Increase Max time diff to show more saved matches."
                )
            else:
                text = (
                    "No matches found. The tagged folder may lack GPS data,\n"
                    "or untagged files may have no date information."
                )
            lbl = ctk.CTkLabel(
                self.results_frame,
                text=text,
                font=FONT_BODY,
                text_color=("gray50", "gray60"),
            )
            lbl.grid(row=0, column=0, pady=40)
            self._group_widgets.append(lbl)
            self._update_pagination_controls(total_matches=0, start_idx=0, end_idx=0)
            self.select_all_btn.configure(state="disabled")
            self.deselect_all_btn.configure(state="disabled")
            self.apply_btn.configure(state="disabled")
            self.save_results_btn.configure(state="disabled")
            return

        all_matches = self._all_matches()
        total_matches = len(all_matches)
        self.total_pages = max(1, (total_matches + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_matches)
        visible_matches = all_matches[start_idx:end_idx]
        visible_groups = group_matches(visible_matches)

        for local_idx, group in enumerate(visible_groups):
            global_idx = self._group_display_index(group.donor.path)
            card = self._create_group_card(group, global_idx)
            card.grid(row=local_idx, column=0, padx=4, pady=6, sticky="ew")
            self._group_widgets.append(card)

        has_matches = total_matches > 0
        state = "normal" if has_matches else "disabled"
        self.select_all_btn.configure(state=state)
        self.deselect_all_btn.configure(state=state)
        self.apply_btn.configure(state=state)
        self.save_results_btn.configure(state=state)
        self._update_pagination_controls(total_matches, start_idx + 1, end_idx)

    def _update_pagination_controls(
        self,
        total_matches: int,
        start_idx: int,
        end_idx: int,
    ):
        if total_matches == 0:
            self.page_label.configure(text="Page 0/0")
            self.prev_page_btn.configure(state="disabled")
            self.next_page_btn.configure(state="disabled")
            return

        self.page_label.configure(
            text=(
                f"Page {self.current_page + 1}/{self.total_pages}  "
                f"(matches {start_idx}-{end_idx} of {total_matches})"
            )
        )
        self.prev_page_btn.configure(
            state="normal" if self.current_page > 0 else "disabled"
        )
        self.next_page_btn.configure(
            state="normal" if self.current_page < self.total_pages - 1 else "disabled"
        )

    def _prev_page(self):
        if self.current_page <= 0:
            return
        self.current_page -= 1
        self._display_groups()

    def _next_page(self):
        if self.current_page >= self.total_pages - 1:
            return
        self.current_page += 1
        self._display_groups()

    def _all_matches(self) -> list[GeoMatch]:
        return [m for group in self.groups for m in group.matches]

    def _group_display_index(self, donor_path: str) -> int:
        for idx, group in enumerate(self.groups):
            if group.donor.path == donor_path:
                return idx
        return 0

    def _create_group_card(self, group: LocationGroup, idx: int) -> ctk.CTkFrame:
        accent = self._accent_for_index(idx)
        donor_badge = f"GPS DONOR {idx + 1:02d}"
        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=COLOR_GROUP_BG,
            corner_radius=10,
            border_width=1,
            border_color=accent,
        )
        card.grid_columnconfigure(0, weight=1)

        accent_strip = ctk.CTkFrame(card, height=5, fg_color=accent, corner_radius=4)
        accent_strip.grid(row=0, column=0, padx=3, pady=(3, 0), sticky="ew")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=1, column=0, padx=14, pady=(12, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        donor_preview = self._create_preview_widget(header, group.donor, (92, 92))
        donor_preview.grid(row=0, column=0, rowspan=4, padx=(0, 12), sticky="nw")

        ctk.CTkLabel(
            header,
            text=donor_badge,
            font=FONT_BADGE,
            fg_color=accent,
            text_color=COLOR_BADGE_TEXT,
            corner_radius=999,
            padx=8,
            pady=3,
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            header,
            text=f"Location: {group.location_label}",
            font=FONT_HEADING,
            text_color=COLOR_LOCATION,
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        donor_date = (
            group.donor.date.strftime("%Y-%m-%d %H:%M") if group.donor.date else "?"
        )
        ctk.CTkLabel(
            header,
            text=f"GPS from: {group.donor.filename}",
            font=FONT_BODY,
            text_color=COLOR_DONOR,
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        ctk.CTkLabel(
            header,
            text=f"Taken: {donor_date}",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
        ).grid(row=3, column=1, sticky="w")

        side_panel = ctk.CTkFrame(header, fg_color="transparent")
        side_panel.grid(row=0, column=2, rowspan=4, padx=(12, 0), sticky="ne")
        side_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            side_panel,
            text=f"{len(group.matches)} file(s)",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
        ).grid(row=0, column=0, pady=(0, 4), sticky="e")

        donor_actions = ctk.CTkFrame(side_panel, fg_color="transparent")
        donor_actions.grid(row=1, column=0, pady=(0, 8), sticky="e")

        ctk.CTkButton(
            donor_actions,
            text="Select donor",
            width=92,
            height=28,
            command=lambda: self._set_group_approval(group, True),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            donor_actions,
            text="Deselect donor",
            width=108,
            height=28,
            command=lambda: self._set_group_approval(group, False),
        ).pack(side="left")

        donor_map = self._create_donor_map_widget(side_panel, group.donor, (220, 120))
        donor_map.grid(row=2, column=0, sticky="e")

        gallery = ctk.CTkFrame(card, fg_color="transparent")
        gallery.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")
        for col in range(3):
            gallery.grid_columnconfigure(col, weight=1, uniform=f"group-{idx}")

        for mi, match in enumerate(group.matches):
            row = mi // 3
            col = mi % 3
            match_card = self._create_match_card(gallery, match, donor_badge, accent)
            match_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        return card

    def _create_match_card(
        self,
        parent: ctk.CTkFrame,
        match: GeoMatch,
        donor_badge: str,
        accent: tuple[str, str],
    ) -> ctk.CTkFrame:
        var = tk.BooleanVar(value=match.approved)
        self.match_vars[match.untagged.path] = var

        def on_toggle():
            match.approved = var.get()

        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BG,
            corner_radius=10,
            border_width=2,
            border_color=accent,
        )
        card.grid_columnconfigure(0, weight=1)

        accent_strip = ctk.CTkFrame(card, height=4, fg_color=accent, corner_radius=4)
        accent_strip.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))

        cb = ctk.CTkCheckBox(
            card,
            text="",
            variable=var,
            command=on_toggle,
            width=24,
        )
        cb.grid(row=1, column=0, padx=8, pady=(8, 0), sticky="nw")

        ctk.CTkLabel(
            card,
            text=donor_badge,
            font=FONT_BADGE,
            fg_color=accent,
            text_color=COLOR_BADGE_TEXT,
            corner_radius=999,
            padx=7,
            pady=2,
        ).grid(row=1, column=0, padx=8, pady=(8, 0), sticky="ne")

        preview = self._create_preview_widget(card, match.untagged, (180, 130))
        preview.grid(row=2, column=0, padx=8, pady=(2, 6), sticky="n")
        self._bind_open_detail(preview, match)

        filename = self._shorten(match.untagged.filename, 26)
        name_label = ctk.CTkLabel(
            card,
            text=filename,
            font=FONT_BODY,
            justify="center",
            wraplength=185,
        )
        name_label.grid(row=3, column=0, padx=8, sticky="ew")
        self._bind_open_detail(name_label, match)

        taken_label = ctk.CTkLabel(
            card,
            text=f"Taken: {self._format_media_datetime(match.untagged)}",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
            wraplength=185,
        )
        taken_label.grid(row=4, column=0, padx=8, pady=(2, 0), sticky="ew")
        self._bind_open_detail(taken_label, match)

        donor_label = ctk.CTkLabel(
            card,
            text=f"GPS from: {self._shorten(match.donor.filename, 26)}",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
            wraplength=185,
        )
        donor_label.grid(row=5, column=0, padx=8, pady=(2, 0), sticky="ew")
        self._bind_open_detail(donor_label, match)

        ctk.CTkLabel(
            card,
            text=f"Time diff: {format_time_diff(match.time_diff_hours)}",
            font=FONT_MONO,
            text_color=COLOR_TIMEDIFF,
        ).grid(row=6, column=0, padx=8, pady=(2, 6), sticky="ew")

        ctk.CTkButton(
            card,
            text="Review",
            height=28,
            command=lambda: self._open_detail_window(match),
        ).grid(row=7, column=0, padx=8, pady=(0, 8), sticky="ew")

        self._bind_open_detail(card, match)
        return card

    @staticmethod
    def _accent_for_index(idx: int) -> tuple[str, str]:
        return DONOR_ACCENTS[idx % len(DONOR_ACCENTS)]

    def _create_donor_map_widget(
        self, parent: ctk.CTkFrame, donor: MediaFile, size: tuple[int, int]
    ) -> tk.Widget:
        if donor.has_gps and TkinterMapView is not None:
            map_widget = TkinterMapView(
                parent,
                width=size[0],
                height=size[1],
                corner_radius=0,
            )
            map_widget.set_position(donor.latitude, donor.longitude, marker=True)
            map_widget.set_zoom(14)
            return map_widget

        return self._create_map_fallback(parent, donor, size)

    def _create_map_fallback(
        self, parent: ctk.CTkFrame, donor: MediaFile, size: tuple[int, int]
    ) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            width=size[0],
            height=size[1],
            fg_color=("#d9dde3", "#3a3d43"),
            corner_radius=8,
        )
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        if donor.has_gps:
            message = (
                "Map preview unavailable\n"
                f"{self._format_coordinates(donor)}\n"
                "Install tkintermapview for embedded maps."
            )
        else:
            message = "No GPS coordinates\navailable for this donor"

        ctk.CTkLabel(
            frame,
            text=message,
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
            justify="center",
        ).grid(row=0, column=0, padx=8, pady=(8, 4), sticky="s")

        if donor.has_gps:
            ctk.CTkButton(
                frame,
                text="Open map",
                width=92,
                height=26,
                command=lambda: self._open_map_in_browser(donor),
            ).grid(row=1, column=0, padx=8, pady=(0, 8), sticky="n")

        return frame

    @staticmethod
    def _format_coordinates(media_file: MediaFile) -> str:
        if not media_file.has_gps:
            return "?"
        return f"{media_file.latitude:.5f}, {media_file.longitude:.5f}"

    @staticmethod
    def _open_map_in_browser(media_file: MediaFile):
        if not media_file.has_gps:
            return
        webbrowser.open(
            "https://www.openstreetmap.org/"
            f"?mlat={media_file.latitude}&mlon={media_file.longitude}"
            f"#map=16/{media_file.latitude}/{media_file.longitude}"
        )

    def _bind_open_detail(self, widget: tk.Widget, match: GeoMatch):
        widget.bind("<Button-1>", lambda _event: self._open_detail_window(match))

    # -- Thumbnails ------------------------------------------------------

    def _create_preview_widget(
        self, parent: ctk.CTkFrame, media_file: MediaFile, size: tuple[int, int]
    ) -> ctk.CTkBaseClass:
        image = self._get_thumbnail(media_file.path, size)
        if image is not None:
            return ctk.CTkLabel(parent, image=image, text="")

        ext = self._file_extension(media_file.path).upper() or "FILE"
        placeholder = ctk.CTkFrame(
            parent,
            width=size[0],
            height=size[1],
            fg_color=("#d9dde3", "#3a3d43"),
            corner_radius=8,
        )
        placeholder.grid_propagate(False)
        placeholder.grid_rowconfigure(0, weight=1)
        placeholder.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            placeholder,
            text=f"{ext}\npreview\nnot available",
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
            justify="center",
        ).grid(row=0, column=0, padx=8, pady=8)
        return placeholder

    def _get_thumbnail(
        self, path: str, size: tuple[int, int]
    ) -> Optional[ctk.CTkImage]:
        ext = self._file_extension(path)

        cache_key = (path, size[0], size[1])
        if cache_key in self._thumbnail_cache:
            return self._thumbnail_cache[cache_key]

        if ext in IMAGE_EXTENSIONS:
            image = self._get_image_thumbnail(path, size)
        elif ext in VIDEO_EXTENSIONS:
            image = self._get_video_thumbnail(path, size)
        else:
            image = None

        if image is not None:
            self._thumbnail_cache[cache_key] = image

        return image

    def _get_image_thumbnail(
        self, path: str, size: tuple[int, int]
    ) -> Optional[ctk.CTkImage]:
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)
                return self._pil_to_ctk_thumbnail(img, size)
        except (OSError, UnidentifiedImageError):
            return None

    def _get_video_thumbnail(
        self, path: str, size: tuple[int, int]
    ) -> Optional[ctk.CTkImage]:
        image = self._get_video_thumbnail_with_ffmpeg(path, size)
        if image is not None:
            return image

        return self._get_video_thumbnail_with_opencv(path, size)

    def _get_video_thumbnail_with_ffmpeg(
        self, path: str, size: tuple[int, int]
    ) -> Optional[ctk.CTkImage]:
        ffmpeg = self._get_ffmpeg_exe()
        if not ffmpeg:
            return None

        duration = self._get_video_duration(path)
        seek_seconds = duration / 2 if duration and duration > 0 else 1

        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seek_seconds:.3f}",
            "-i",
            path,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=20)
            if result.returncode != 0 or not result.stdout:
                return None
            image = Image.open(BytesIO(result.stdout))
            return self._pil_to_ctk_thumbnail(image, size)
        except (OSError, subprocess.TimeoutExpired, UnidentifiedImageError):
            return None

    @staticmethod
    def _get_ffmpeg_exe() -> Optional[str]:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg

        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return None

    @staticmethod
    def _get_video_duration(path: str) -> Optional[float]:
        try:
            import cv2
        except ImportError:
            return None

        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            return None

        try:
            frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
            if frame_count > 0 and fps > 0:
                return frame_count / fps
            return None
        finally:
            capture.release()

    def _get_video_thumbnail_with_opencv(
        self, path: str, size: tuple[int, int]
    ) -> Optional[ctk.CTkImage]:
        try:
            import cv2
        except ImportError:
            return None

        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            return None

        try:
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if frame_count > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, max(frame_count // 2, 0))

            success, frame = capture.read()
            if not success or frame is None:
                return None

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)
            return self._pil_to_ctk_thumbnail(image, size)
        finally:
            capture.release()

    @staticmethod
    def _pil_to_ctk_thumbnail(
        img: Image.Image, size: tuple[int, int]
    ) -> ctk.CTkImage:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, (24, 26, 30))
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        if img.mode in ("RGBA", "LA"):
            rgba = img.convert("RGBA")
            canvas.paste(rgba, (x, y), rgba)
        else:
            canvas.paste(img.convert("RGB"), (x, y))

        return ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)

    @staticmethod
    def _file_extension(path: str) -> str:
        return os.path.splitext(path)[1].lstrip(".").lower()

    @staticmethod
    def _shorten(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return f"{text[: max_len - 1]}..."

    @staticmethod
    def _format_media_datetime(media_file: MediaFile) -> str:
        if media_file.date is None:
            return "?"
        return media_file.date.strftime("%Y-%m-%d %H:%M")

    # -- Detail view -----------------------------------------------------

    def _open_detail_window(self, match: GeoMatch):
        detail = ctk.CTkToplevel(self)
        detail.title(f"Review match - {match.untagged.filename}")
        detail.geometry("920x620")
        detail.minsize(760, 520)
        detail.transient(self)
        detail.grab_set()

        detail.grid_columnconfigure(0, weight=1)
        detail.grid_columnconfigure(1, weight=1)
        detail.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            detail,
            text=f"Review GPS copy: {match.untagged.filename}",
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, padx=20, pady=(18, 8), sticky="w")

        target_panel = self._create_detail_panel(
            detail,
            "Target file (will receive GPS)",
            match.untagged,
            match,
            is_donor=False,
        )
        target_panel.grid(row=1, column=0, padx=(20, 8), pady=8, sticky="nsew")

        donor_panel = self._create_detail_panel(
            detail,
            "GPS donor file",
            match.donor,
            match,
            is_donor=True,
        )
        donor_panel.grid(row=1, column=1, padx=(8, 20), pady=8, sticky="nsew")

        footer = ctk.CTkFrame(detail, fg_color="transparent")
        footer.grid(row=2, column=0, columnspan=2, padx=20, pady=(4, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        var = self.match_vars.get(match.untagged.path)
        if var is None:
            var = tk.BooleanVar(value=match.approved)
            self.match_vars[match.untagged.path] = var

        def on_detail_toggle():
            match.approved = var.get()

        ctk.CTkCheckBox(
            footer,
            text="Approve this GPS copy",
            variable=var,
            command=on_detail_toggle,
            font=FONT_BODY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            footer,
            text=f"Time difference: {format_time_diff(match.time_diff_hours)}",
            font=FONT_MONO,
            text_color=COLOR_TIMEDIFF,
        ).grid(row=0, column=1, padx=12)

        ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            command=detail.destroy,
        ).grid(row=0, column=2, sticky="e")

        detail.focus()

    def _create_detail_panel(
        self,
        parent: ctk.CTkToplevel,
        title: str,
        media_file: MediaFile,
        match: GeoMatch,
        is_donor: bool,
    ) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=12)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panel, text=title, font=FONT_HEADING).grid(
            row=0, column=0, padx=16, pady=(14, 8), sticky="w"
        )

        preview = self._create_preview_widget(panel, media_file, (380, 300))
        preview.grid(row=1, column=0, padx=16, pady=8)

        info = [
            f"File: {media_file.filename}",
            f"Date: {media_file.date.strftime('%Y-%m-%d %H:%M:%S') if media_file.date else '?'}",
        ]
        if is_donor:
            info.extend(
                [
                    f"Latitude: {media_file.latitude}",
                    f"Longitude: {media_file.longitude}",
                    f"Altitude: {media_file.altitude if media_file.altitude is not None else '?'}",
                ]
            )
        else:
            info.append(f"GPS will be copied from: {match.donor.filename}")

        ctk.CTkLabel(
            panel,
            text="\n".join(info),
            font=FONT_SMALL,
            text_color=COLOR_DONOR,
            justify="left",
            wraplength=360,
        ).grid(row=2, column=0, padx=16, pady=(8, 14), sticky="w")

        return panel

    # -- Bulk selection --------------------------------------------------

    def _set_group_approval(self, group: LocationGroup, approved: bool):
        for match in group.matches:
            match.approved = approved
            var = self.match_vars.get(match.untagged.path)
            if var is not None:
                var.set(approved)

    def _select_all(self):
        for var in self.match_vars.values():
            var.set(True)
        for group in self.groups:
            for m in group.matches:
                m.approved = True

    def _deselect_all(self):
        for var in self.match_vars.values():
            var.set(False)
        for group in self.groups:
            for m in group.matches:
                m.approved = False

    # -- Save / load results --------------------------------------------

    @staticmethod
    def _media_to_dict(media: MediaFile) -> dict:
        return {
            "path": media.path,
            "filename": media.filename,
            "date": media.date.isoformat() if media.date else None,
            "latitude": media.latitude,
            "longitude": media.longitude,
            "altitude": media.altitude,
        }

    @staticmethod
    def _optional_float(value) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _media_from_dict(raw: dict) -> MediaFile:
        date_raw = raw.get("date")
        parsed_date: Optional[datetime] = None
        if isinstance(date_raw, str) and date_raw.strip():
            try:
                parsed_date = datetime.fromisoformat(date_raw)
            except ValueError:
                parsed_date = None

        return MediaFile(
            path=str(raw.get("path", "")),
            filename=str(raw.get("filename", "")),
            date=parsed_date,
            latitude=GeoTagCopyApp._optional_float(raw.get("latitude")),
            longitude=GeoTagCopyApp._optional_float(raw.get("longitude")),
            altitude=GeoTagCopyApp._optional_float(raw.get("altitude")),
        )

    def _save_results(self):
        all_matches = self._all_matches()
        if not all_matches:
            messagebox.showinfo("Nothing to save", "There are no matched results to save yet.")
            return

        # On some macOS Tk builds (8.6.16), complex file filters can crash
        # inside Tk's native bridge. Use safer dialog setup on macOS and normalize
        # the saved extension in Python.
        if os.name == "posix" and sys.platform == "darwin":
            save_path = filedialog.asksaveasfilename(
                title="Save scan results",
                defaultextension=".json",
                initialfile="geotagcopy-results.geotagcopy.json",
            )
        else:
            save_path = filedialog.asksaveasfilename(
                title="Save scan results",
                defaultextension=".geotagcopy.json",
                filetypes=[
                    ("GeoTagCopy Results", "*.geotagcopy.json"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*"),
                ],
            )
        if not save_path:
            return
        if not save_path.lower().endswith(".geotagcopy.json"):
            save_path = f"{save_path}.geotagcopy.json"

        payload = {
            "format": "geotagcopy-results-v1",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "tagged_folder": self.tagged_var.get().strip(),
            "untagged_folder": self.untagged_var.get().strip(),
            "max_time_diff_hours": self._max_diff_hours,
            "time_diff_unit": self._time_unit_btn.get(),
            "matches": [
                {
                    "untagged": self._media_to_dict(m.untagged),
                    "donor": self._media_to_dict(m.donor),
                    "time_diff_hours": m.time_diff_hours,
                    "approved": m.approved,
                }
                for m in all_matches
            ],
        }

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=True)
            self._set_status(
                f"Saved {len(all_matches)} matches to {os.path.basename(save_path)}",
                1.0,
            )
            messagebox.showinfo("Saved", f"Saved {len(all_matches)} matches.")
        except OSError as e:
            messagebox.showerror("Save failed", f"Could not save results:\n{e}")

    def _load_results(self):
        if os.name == "posix" and sys.platform == "darwin":
            load_path = filedialog.askopenfilename(title="Load scan results")
        else:
            load_path = filedialog.askopenfilename(
                title="Load scan results",
                filetypes=[
                    ("GeoTagCopy Results", "*.geotagcopy.json"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*"),
                ],
            )
        if not load_path:
            return

        try:
            with open(load_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("Load failed", f"Could not read results file:\n{e}")
            return

        if payload.get("format") != "geotagcopy-results-v1":
            messagebox.showerror(
                "Unsupported file",
                "This file is not a supported GeoTagCopy results export.",
            )
            return

        raw_matches = payload.get("matches")
        if not isinstance(raw_matches, list):
            messagebox.showerror(
                "Invalid file", "Results file does not contain a valid match list."
            )
            return

        restored: list[GeoMatch] = []
        for item in raw_matches:
            if not isinstance(item, dict):
                continue
            untagged_raw = item.get("untagged")
            donor_raw = item.get("donor")
            if not isinstance(untagged_raw, dict) or not isinstance(donor_raw, dict):
                continue

            untagged = self._media_from_dict(untagged_raw)
            donor = self._media_from_dict(donor_raw)
            if not untagged.path or not donor.path:
                continue

            try:
                time_diff = float(item.get("time_diff_hours", 0.0))
            except (TypeError, ValueError):
                time_diff = 0.0

            restored.append(
                GeoMatch(
                    untagged=untagged,
                    donor=donor,
                    time_diff_hours=time_diff,
                    approved=bool(item.get("approved", True)),
                )
            )

        if not restored:
            messagebox.showwarning("No data", "No valid matches were found in this file.")
            return

        tagged_folder = payload.get("tagged_folder")
        untagged_folder = payload.get("untagged_folder")
        if isinstance(tagged_folder, str):
            self.tagged_var.set(tagged_folder)
        if isinstance(untagged_folder, str):
            self.untagged_var.set(untagged_folder)

        saved_max_diff = self._optional_float(payload.get("max_time_diff_hours"))
        saved_unit = payload.get("time_diff_unit")
        if saved_max_diff is not None:
            self._set_time_filter_display(
                saved_max_diff,
                saved_unit if isinstance(saved_unit, str) else "hour",
            )

        self._source_matches = restored
        self.groups = group_matches(self._filtered_source_matches())
        self.current_page = 0
        self._display_groups()

        total_matches = len(restored)
        shown_matches = len(self._all_matches())
        self._set_status(
            f"Loaded {total_matches} matches from {os.path.basename(load_path)}; "
            f"showing {shown_matches} within {format_time_diff(self._max_diff_hours)}",
            1.0,
        )
        messagebox.showinfo(
            "Loaded",
            f"Loaded {total_matches} matched file(s).\n"
            f"Showing {shown_matches} within current Max time diff.",
        )

    # -- Apply tags ------------------------------------------------------

    def _apply_tags(self):
        all_matches = self._all_matches()

        approved_count = sum(1 for m in all_matches if m.approved)
        if approved_count == 0:
            messagebox.showinfo("Nothing to apply", "No files are selected for tagging.")
            return

        ok = messagebox.askyesno(
            "Confirm",
            f"Apply GPS tags to {approved_count} file(s)?\n\n"
            "This will modify the files' metadata in place.",
        )
        if not ok:
            return

        self.apply_btn.configure(state="disabled", text="Applying...")
        self.scan_btn.configure(state="disabled")

        thread = threading.Thread(
            target=self._apply_worker, args=(all_matches,), daemon=True
        )
        thread.start()

    def _apply_worker(self, matches: list[GeoMatch]):
        try:
            approved_count = sum(1 for m in matches if m.approved)

            def progress(done, total):
                frac = done / total if total > 0 else 1.0
                self.after(
                    0,
                    self._set_status,
                    f"Applying GPS tags... {done}/{total}",
                    frac,
                )

            success, errors = apply_gps_tags(matches, progress)

            if errors:
                msg = f"Applied {success}/{approved_count} tags. Errors:\n" + "\n".join(
                    errors[:10]
                )
                self.after(0, self._set_status, msg, 1.0)
                self.after(
                    0,
                    lambda: messagebox.showwarning("Partial success", msg),
                )
            else:
                msg = f"Successfully applied GPS tags to {success} file(s)"
                self.after(0, self._set_status, msg, 1.0)
                self.after(
                    0,
                    lambda: messagebox.showinfo("Done", msg),
                )
        except Exception as e:
            self.after(0, self._set_status, f"Error: {e}", 0.0)
        finally:
            self.after(0, lambda: self.apply_btn.configure(state="normal", text="Apply GPS Tags"))
            self.after(0, lambda: self.scan_btn.configure(state="normal"))


def run_app(tagged_folder: str = "", untagged_folder: str = ""):
    """Launch the GeoTagCopy application."""
    app = GeoTagCopyApp(tagged_folder=tagged_folder, untagged_folder=untagged_folder)
    app.mainloop()
