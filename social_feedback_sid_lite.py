#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Social Feedback SID-Lite
========================

README
------
This is a coder-style PsychoPy experiment script for an EEG-friendly social
feedback task inspired by the Social Incentive Delay (SID) paradigm.

Required folder structure
-------------------------
Place this script in a project folder that optionally contains:

    stimuli/
        self/
        other/
        avatars/

This cleaner EEG version does not use participant photos. Self-relevance is
created using the participant nickname plus a short self-written post entered
at the beginning of the session.

The task will still run if these folders are missing or empty. In that case,
the script automatically falls back to text-only placeholder posts.

How to run
----------
1. Install PsychoPy 2024.2.x if possible.
2. Open this file in PsychoPy Coder or run it with Python from a PsychoPy
   environment.
3. Start the experiment and complete the participant dialog.
4. If avatar files are available, the participant can choose which avatar
   represents their account before the task begins.

Where to edit common settings
-----------------------------
- Timings: search for "TIMING CONSTANTS"
- Response keys: search for "RESPONSE SETTINGS"
- Feedback comments: search for "COMMENT POOLS"
- Trigger behavior: search for "EEG / EVENT TRIGGER SETTINGS"
- Screen layout and colors: search for "VISUAL DESIGN SETTINGS"
- Self avatar selection: search for "run_self_selection"

Notes
-----
- This script does NOT use Builder-generated code.
- Self trials use the participant nickname plus a typed self-post and chosen avatar.
- Other trials use sampled other usernames plus standardized other-user text.
- The design is a fully within-subject 2 x 2 x 2 factorial design:
  post relevance (self vs other) x cue type (reward vs punishment) x
  outcome (win vs loss, determined online by reaction time threshold).
- Main task: 96 trials total, 3 blocks of 32, balanced across the 8 design
  cells (4 trials per cell per block; 12 trials per cell overall).
- Practice: 8 trials, one trial per design cell.
- The adaptive RT threshold is intentionally simple and transparent.
"""

from __future__ import annotations

import csv
import math
import os
import random
from pathlib import Path

from psychopy import core, data, event, gui, logging, visual
import psychopy


# ---------------------------------------------------------------------------
# VERSION PINNING / COMPATIBILITY CHECK
# ---------------------------------------------------------------------------
# PsychoPy Builder scripts usually pin a specific version in generated code.
# Here we do a lighter coder-style check and warn if the version is not from
# the requested family.
RECOMMENDED_PSYCHOPY_PREFIX = "2024.2"


# ---------------------------------------------------------------------------
# EXPERIMENT IDENTITY
# ---------------------------------------------------------------------------
EXPERIMENT_NAME = "Social Feedback SID-Lite"
TASK_VERSION = "1.0"
MAX_SELF_POST_CHARS = 50


# ---------------------------------------------------------------------------
# PATH SETTINGS
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
STIMULI_DIR = SCRIPT_DIR / "stimuli"
SELF_STIM_DIR = STIMULI_DIR / "self"
OTHER_STIM_DIR = STIMULI_DIR / "other"
AVATAR_STIM_DIR = STIMULI_DIR / "avatars"
DATA_DIR = SCRIPT_DIR / "data"


# ---------------------------------------------------------------------------
# RESPONSE SETTINGS
# ---------------------------------------------------------------------------
LEFT_KEY = "left"
RIGHT_KEY = "right"
CONTINUE_KEY = "space"
QUIT_KEY = "escape"
ALLOWED_RESPONSE_KEYS = [LEFT_KEY, RIGHT_KEY]


# ---------------------------------------------------------------------------
# TIMING CONSTANTS (SECONDS)
# ---------------------------------------------------------------------------
FIXATION_DUR = 0.500
POST_DUR = 1.200
CUE_DUR = 1.000
ANTICIPATION_MIN = 0.800
ANTICIPATION_MAX = 1.200
TARGET_TIMEOUT = 1.000
FEEDBACK1_DUR = 0.800
BETWEEN_FEEDBACK_DUR = 0.400
FEEDBACK2_DUR = 1.200
ITI_MIN = 0.800
ITI_MAX = 1.200


# ---------------------------------------------------------------------------
# TASK SIZE SETTINGS
# ---------------------------------------------------------------------------
PRACTICE_TRIALS = 8
MAIN_TRIALS_TOTAL = 96
MAIN_BLOCKS = 3
TRIALS_PER_BLOCK = 32
TRIALS_PER_CELL_PER_BLOCK = 4
INITIAL_RT_THRESHOLD = 0.500  # 500 ms
MIN_RT_THRESHOLD = 0.250
MAX_RT_THRESHOLD = 0.900
TARGET_WIN_RATE = 0.60

# Simple transparent adaptive rule:
# - win: threshold gets slightly tighter
# - loss: threshold gets slightly easier
# These values are chosen so the "balance point" is near 60% wins:
#   0.6 * (-0.010) + 0.4 * (+0.015) = 0
THRESHOLD_STEP_AFTER_WIN = -0.010
THRESHOLD_STEP_AFTER_LOSS = 0.015


# ---------------------------------------------------------------------------
# VISUAL DESIGN SETTINGS
# ---------------------------------------------------------------------------
WINDOW_SIZE = [1280, 800]
FULLSCREEN = False
BG_COLOR = [-0.85, -0.85, -0.85]  # dark grey in PsychoPy's -1 to 1 space
TEXT_COLOR = "white"
SECONDARY_TEXT_COLOR = "#C8C8C8"
POST_PANEL_COLOR = "#12171D"
POST_BORDER_COLOR = "#2D3945"
COMMENT_BUBBLE_COLOR = "#232A33"
COMMENT_BORDER_COLOR = "#606A75"
REWARD_COLOR = "#46C06F"
PUNISHMENT_COLOR = "#E3A541"
TARGET_COLOR = "white"
FIXATION_COLOR = "white"

# Stable screen positions support EEG / eye tracking / ECG friendly design.
USERNAME_POS = (-0.16, 0.18)
USERMETA_POS = (-0.16, 0.145)
AVATAR_POS = (-0.24, 0.17)
CUE_POS = (0.0, -0.33)
COMMENT_POS = (0.0, -0.40)
FIXATION_POS = (0.0, 0.0)
TARGET_POS = (0.0, 0.0)
POST_TEXT_POS = (-0.16, 0.05)


# ---------------------------------------------------------------------------
# COMMENT POOLS
# ---------------------------------------------------------------------------
POSITIVE_COMMENTS = [
    "Nice post",
    "Love this",
    "So cool",
    "Looks great",
    "Really nice",
    "Well done",
]

NEGATIVE_COMMENTS = [
    "Not my thing",
    "Meh",
    "Boring",
    "Nothing special",
    "Not for me",
    "Doesn't stand out",
]


# ---------------------------------------------------------------------------
# OTHER-USER NAME POOL
# ---------------------------------------------------------------------------
OTHER_USERNAMES = [
    "@user_17",
    "@anna23",
    "@bluecat",
    "@noah88",
    "@skyline",
    "@milo_4",
    "@leahpix",
    "@oceanjay",
    "@riverfox",
    "@poppygram",
    "@urbanmint",
    "@solstice_5",
]


# ---------------------------------------------------------------------------
# STANDARDIZED OTHER-POST TEXT POOL
# ---------------------------------------------------------------------------
OTHER_POST_TEXTS = [
    "Trying to stay focused today.",
    "Long day, but getting things done.",
    "Just taking a short break.",
    "Quiet morning and catching up.",
    "Small wins today still count.",
    "Keeping things simple today.",
    "Trying to stay productive.",
    "A calm day so far.",
    "Taking things one step at a time.",
    "A little progress is still progress.",
    "Finally getting started on things.",
    "Just a regular day today.",
]


# ---------------------------------------------------------------------------
# EEG / EVENT TRIGGER SETTINGS
# ---------------------------------------------------------------------------
USE_TRIGGERS = False

TRIGGER_MAP = {
    "self_post_onset": 11,
    "other_post_onset": 12,
    "reward_cue": 21,
    "punishment_cue": 22,
    "target_onset": 31,
    "response_left": 41,
    "response_right": 42,
    "response_missed": 43,
    "outcome_win": 51,
    "outcome_loss": 52,
    "feedback1_onset": 61,
    "feedback2_onset": 62,
    "block_start": 71,
    "block_end": 72,
    "experiment_end": 99,
}


# ---------------------------------------------------------------------------
# GLOBAL STATE CONTAINERS
# ---------------------------------------------------------------------------
PARTICIPANT_INFO = {}
TRIAL_DATA = []
CURRENT_DATA_FILE = None


class ExperimentAbort(Exception):
    """Custom exception used for a clean participant-triggered abort."""


def clamp(value, minimum, maximum):
    """Keep a value within a specified inclusive range."""
    return max(minimum, min(maximum, value))


def safe_mkdir(path_obj):
    """Create a directory if needed."""
    path_obj.mkdir(parents=True, exist_ok=True)


def check_psychopy_version():
    """
    Print a version note at startup.

    We do not hard-stop, because labs may still want to run this under a very
    similar PsychoPy build, but we make the intended version explicit.
    """
    installed = psychopy.__version__
    print(f"[INFO] Running with PsychoPy version: {installed}")
    if not installed.startswith(RECOMMENDED_PSYCHOPY_PREFIX):
        print(
            "[WARNING] This script was designed for PsychoPy "
            f"{RECOMMENDED_PSYCHOPY_PREFIX}.x. Current version: {installed}"
        )


def get_participant_info():
    """
    Collect participant/session information.

    The nickname and a short typed self-post drive the self-relevance
    manipulation without any personal photo uploads.
    """
    dlg = gui.Dlg(title=EXPERIMENT_NAME)
    dlg.addText("Participant setup")
    dlg.addField("participant_id:", initial="")
    dlg.addField("session:", initial="001")
    dlg.addField("nickname:", initial="")
    dlg.addField("age:", initial="")
    dlg.addText(
        f"Write a short post about what you think today.\n"
        f"Keep it brief, like a social app post. Maximum {MAX_SELF_POST_CHARS} characters."
    )
    dlg.addField("self_post_text:", initial="")
    values = dlg.show()

    if not dlg.OK:
        raise SystemExit("Participant cancelled the dialog.")

    exp_info = {
        "participant_id": values[0],
        "session": values[1],
        "nickname": values[2],
        "age": values[3],
        "self_post_text": values[4],
    }

    # Clean and normalize a few fields.
    exp_info["participant_id"] = str(exp_info["participant_id"]).strip() or "TEST"
    exp_info["session"] = str(exp_info["session"]).strip() or "001"

    nickname = str(exp_info["nickname"]).strip().replace(" ", "")
    if not nickname:
        nickname = exp_info["participant_id"]
    exp_info["nickname"] = nickname

    self_post_text = str(exp_info["self_post_text"]).strip()
    if not self_post_text:
        self_post_text = "Just getting through the day."
    exp_info["self_post_text"] = self_post_text[:MAX_SELF_POST_CHARS]

    # Reproducible random seed: deterministic from participant/session.
    seed_string = f"{exp_info['participant_id']}_{exp_info['session']}"
    seed_value = sum(ord(ch) for ch in seed_string) % 1000000
    exp_info["random_seed"] = seed_value
    exp_info["date_time"] = data.getDateStr(format="%Y-%m-%d_%H-%M-%S")
    exp_info["self_username"] = f"@{nickname}"

    return exp_info


def list_image_files(folder_path):
    """
    Return a sorted list of supported image files in a folder.

    This function is deliberately defensive: if the folder is missing, we
    return an empty list rather than failing.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    allowed_suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    files = [
        p for p in folder_path.iterdir()
        if p.is_file() and p.suffix.lower() in allowed_suffixes
    ]
    return sorted(files)


def load_stimuli(rng):
    """
    Load available image paths.

    The experiment still runs if these lists are empty. In that case,
    placeholder text/shape elements are shown instead of images.
    """
    self_images = list_image_files(SELF_STIM_DIR)
    other_images = list_image_files(OTHER_STIM_DIR)
    avatar_images = list_image_files(AVATAR_STIM_DIR)

    stimuli = {
        "self_images": self_images,
        "other_images": other_images,
        "avatars": avatar_images,
        "placeholder_mode": not (self_images or other_images or avatar_images),
    }

    print(
        "[INFO] Stimulus counts | "
        f"self: {len(self_images)} | other: {len(other_images)} | "
        f"avatars: {len(avatar_images)} | placeholder_mode: {stimuli['placeholder_mode']}"
    )

    # Shuffle copies to prevent deterministic first-image overuse.
    rng.shuffle(stimuli["self_images"])
    rng.shuffle(stimuli["other_images"])
    rng.shuffle(stimuli["avatars"])
    return stimuli


def build_selection_positions(n_items):
    """Return thumbnail positions for 1-8 choices arranged in up to 4 columns."""
    cols = min(4, max(1, n_items))
    x_positions = [-0.42, -0.14, 0.14, 0.42][:cols]
    positions = []
    for index in range(n_items):
        row = index // cols
        col = index % cols
        y = 0.10 if row == 0 else -0.20
        positions.append((x_positions[col], y))
    return positions


def wait_for_mouse_release(mouse):
    """Pause briefly until the mouse button is released."""
    while any(mouse.getPressed()):
        check_for_abort()
        core.wait(0.01)


def choose_image_option(
    win,
    title_text,
    prompt_text,
    image_paths,
    image_size,
    empty_message,
    allow_none=False,
    none_label="No image",
):
    """
    Let the participant choose one image by clicking on a visible thumbnail.

    If no images are available, show a short message and continue with None.
    """
    if not image_paths:
        message = visual.TextStim(
            win,
            text=f"{title_text}\n\n{empty_message}\n\nPress {CONTINUE_KEY} to continue.",
            color=TEXT_COLOR,
            height=0.032,
            wrapWidth=1.0,
        )
        while True:
            check_for_abort()
            message.draw()
            win.flip()
            keys = event.getKeys()
            if CONTINUE_KEY in keys:
                event.clearEvents()
                return None
            if QUIT_KEY in keys:
                raise ExperimentAbort("Experiment aborted by user.")

    win.mouseVisible = True
    mouse = event.Mouse(win=win)
    title_stim = visual.TextStim(
        win, text=title_text, color=TEXT_COLOR, height=0.04, pos=(0.0, 0.40)
    )
    prompt_stim = visual.TextStim(
        win, text=prompt_text, color=SECONDARY_TEXT_COLOR, height=0.026, pos=(0.0, 0.33)
    )
    footer_stim = visual.TextStim(
        win,
        text="Click one picture, then press space, return, or click Continue",
        color=SECONDARY_TEXT_COLOR,
        height=0.024,
        pos=(0.0, -0.43),
    )
    continue_button = visual.Rect(
        win,
        width=0.22,
        height=0.07,
        pos=(0.0, -0.33),
        fillColor="#2E6FEE",
        lineColor="#8FB2FF",
        lineWidth=2,
    )
    continue_label = visual.TextStim(
        win,
        text="Continue",
        color="white",
        height=0.028,
        pos=(0.0, -0.33),
    )

    option_paths = list(image_paths)
    if allow_none:
        option_paths.append(None)

    positions = build_selection_positions(len(option_paths))
    image_stims = []
    border_stims = []
    label_stims = []

    for path, pos in zip(option_paths, positions):
        border_stims.append(
            visual.Rect(
                win,
                width=image_size[0] + 0.02,
                height=image_size[1] + 0.02,
                pos=pos,
                fillColor=None,
                lineColor="#5C6570",
                lineWidth=2,
            )
        )
        if path is None:
            image_stims.append(
                visual.Rect(
                    win,
                    width=image_size[0],
                    height=image_size[1],
                    pos=pos,
                    fillColor="#2A3038",
                    lineColor="#7A8591",
                    lineWidth=1.5,
                )
            )
            label_text = none_label
        else:
            image_stims.append(
                visual.ImageStim(win, image=str(path), size=image_size, pos=pos)
            )
            label_text = path.stem

        label_stims.append(
            visual.TextStim(
                win,
                text=label_text,
                color=SECONDARY_TEXT_COLOR,
                height=0.018,
                pos=(pos[0], pos[1] - image_size[1] / 2 - 0.04),
            )
        )

    selected_index = 0
    event.clearEvents()
    mouse.clickReset()
    wait_for_mouse_release(mouse)

    while True:
        check_for_abort()

        click_happened = mouse.getPressed()[0]
        if click_happened:
            for index, border in enumerate(border_stims):
                if border.contains(mouse):
                    selected_index = index
                    core.wait(0.15)
                    break
            if continue_button.contains(mouse):
                win.mouseVisible = False
                return option_paths[selected_index]

        keys = event.getKeys()
        if CONTINUE_KEY in keys or "return" in keys or "num_enter" in keys:
            event.clearEvents()
            win.mouseVisible = False
            return option_paths[selected_index]
        if QUIT_KEY in keys:
            raise ExperimentAbort("Experiment aborted by user.")

        title_stim.draw()
        prompt_stim.draw()
        footer_stim.draw()
        continue_button.draw()
        continue_label.draw()

        for index, (border, image_stim, label_stim) in enumerate(
            zip(border_stims, image_stims, label_stims)
        ):
            border.lineColor = "#FFFFFF" if index == selected_index else "#5C6570"
            border.lineWidth = 4 if index == selected_index else 2
            border.draw()
            image_stim.draw()
            label_stim.draw()

        win.flip()


def run_self_selection(win, participant_info, stimuli):
    """
    Let the participant choose their self avatar visually.

    Other-user content remains automated and randomized.
    """
    participant_info["self_avatar_path"] = choose_image_option(
        win=win,
        title_text="Choose Your Avatar",
        prompt_text="Click the avatar you want to use for your account.",
        image_paths=stimuli["avatars"],
        image_size=(0.16, 0.16),
        empty_message="No avatar files were found. The task will use a default placeholder avatar.",
        allow_none=True,
        none_label="No avatar",
    )

    participant_info["self_avatar_choice"] = (
        participant_info["self_avatar_path"].name
        if participant_info["self_avatar_path"] else ""
    )
    win.mouseVisible = False
    return participant_info


def build_main_trials():
    """
    Create the balanced main-task design.

    We balance the factorial bookkeeping per block.

    Important design note:
    the true win/loss outcome is generated online by reaction time relative to
    the current threshold, so it cannot be perfectly pre-scheduled and still
    remain a genuine adaptive SID-style task. To keep the requested 2 x 2 x 2
    structure visible in the saved data, we also store a balanced bookkeeping
    label called 'design_cell_outcome_label'. The real observed outcome is
    saved separately in 'actual_outcome'.
    """
    post_levels = ["self", "other"]
    cue_levels = ["reward", "punishment"]
    design_outcome_levels = ["win", "loss"]

    blocks = []
    for block_index in range(1, MAIN_BLOCKS + 1):
        block_trials = []
        for post_relevance in post_levels:
            for cue_type in cue_levels:
                for outcome_label in design_outcome_levels:
                    for rep in range(TRIALS_PER_CELL_PER_BLOCK):
                        block_trials.append(
                            {
                                "block_index": block_index,
                                "practice_or_main": "main",
                                "post_relevance": post_relevance,
                                "cue_type": cue_type,
                                "design_cell_outcome_label": outcome_label,
                                "expected_outcome_type": (
                                    "earn_positive_feedback"
                                    if cue_type == "reward"
                                    else "avoid_negative_feedback"
                                ),
                                "trial_rep": rep + 1,
                            }
                        )
        blocks.append(block_trials)

    return blocks


def build_practice_trials():
    """
    Create an 8-trial practice list with one trial per design cell.

    Practice is short but still demonstrates all conditions.
    """
    post_levels = ["self", "other"]
    cue_levels = ["reward", "punishment"]
    design_outcome_levels = ["win", "loss"]

    practice_trials = []
    for post_relevance in post_levels:
        for cue_type in cue_levels:
            for outcome_label in design_outcome_levels:
                practice_trials.append(
                    {
                        "block_index": 0,
                        "practice_or_main": "practice",
                        "post_relevance": post_relevance,
                        "cue_type": cue_type,
                        "design_cell_outcome_label": outcome_label,
                        "expected_outcome_type": (
                            "earn_positive_feedback"
                            if cue_type == "reward"
                            else "avoid_negative_feedback"
                        ),
                        "trial_rep": 1,
                    }
                )
    return practice_trials


def create_trial_list(rng):
    """
    Build and randomize practice and main trial lists.

    Randomization is done within block so balancing is preserved.
    """
    practice_trials = build_practice_trials()
    rng.shuffle(practice_trials)

    main_blocks = build_main_trials()
    for block in main_blocks:
        rng.shuffle(block)

    # Assign global running trial numbers now, in the exact order they will run.
    global_counter = 0
    for trial in practice_trials:
        global_counter += 1
        trial["trial_index"] = global_counter

    for block in main_blocks:
        for trial in block:
            global_counter += 1
            trial["trial_index"] = global_counter

    return practice_trials, main_blocks


def create_window():
    """Create the PsychoPy window."""
    win = visual.Window(
        size=WINDOW_SIZE,
        fullscr=FULLSCREEN,
        color=BG_COLOR,
        units="height",
        allowGUI=False,
    )
    win.mouseVisible = False
    return win


def create_visuals(win):
    """
    Pre-create visual objects so layout stays stable and code remains readable.

    Reusing the same objects trial after trial is also good practice for timing
    stability in EEG experiments.
    """
    visuals = {}

    visuals["fixation"] = visual.TextStim(
        win,
        text="+",
        color=FIXATION_COLOR,
        height=0.05,
        pos=FIXATION_POS,
    )

    visuals["post_panel"] = visual.Rect(
        win,
        width=0.56,
        height=0.24,
        fillColor=POST_PANEL_COLOR,
        lineColor=POST_BORDER_COLOR,
        lineWidth=1.5,
        pos=(0.0, 0.10),
    )

    visuals["avatar_circle"] = visual.Circle(
        win,
        radius=0.038,
        fillColor="#6D7C8A",
        lineColor="#9BA8B5",
        pos=AVATAR_POS,
    )

    visuals["avatar_image"] = visual.ImageStim(
        win,
        image=None,
        size=(0.085, 0.085),
        pos=AVATAR_POS,
    )

    visuals["username_text"] = visual.TextStim(
        win,
        text="@username",
        color=TEXT_COLOR,
        height=0.026,
        pos=USERNAME_POS,
        alignText="left",
        anchorHoriz="left",
    )

    visuals["usermeta_text"] = visual.TextStim(
        win,
        text="just now",
        color=SECONDARY_TEXT_COLOR,
        height=0.018,
        pos=USERMETA_POS,
        alignText="left",
        anchorHoriz="left",
    )

    visuals["post_text"] = visual.TextStim(
        win,
        text="",
        color=TEXT_COLOR,
        height=0.024,
        wrapWidth=0.34,
        pos=POST_TEXT_POS,
        alignText="left",
        anchorHoriz="left",
    )

    visuals["cue_reward"] = visual.Circle(
        win,
        radius=0.03,
        fillColor=REWARD_COLOR,
        lineColor=REWARD_COLOR,
        pos=CUE_POS,
    )

    visuals["cue_punishment"] = visual.Rect(
        win,
        width=0.06,
        height=0.06,
        fillColor=PUNISHMENT_COLOR,
        lineColor=PUNISHMENT_COLOR,
        pos=CUE_POS,
    )

    visuals["cue_label"] = visual.TextStim(
        win,
        text="",
        color=TEXT_COLOR,
        height=0.024,
        pos=(0.0, CUE_POS[1] - 0.055),
    )

    visuals["target"] = visual.Rect(
        win,
        width=0.05,
        height=0.05,
        fillColor=TARGET_COLOR,
        lineColor=TARGET_COLOR,
        pos=TARGET_POS,
    )

    visuals["feedback1_text"] = visual.TextStim(
        win,
        text="",
        color=TEXT_COLOR,
        height=0.045,
        pos=(0.0, 0.00),
    )

    visuals["comment_bubble"] = visual.Rect(
        win,
        width=0.56,
        height=0.12,
        fillColor=COMMENT_BUBBLE_COLOR,
        lineColor=COMMENT_BORDER_COLOR,
        lineWidth=1.5,
        pos=COMMENT_POS,
    )

    visuals["comment_text"] = visual.TextStim(
        win,
        text="",
        color=TEXT_COLOR,
        height=0.028,
        wrapWidth=0.48,
        pos=COMMENT_POS,
    )

    visuals["instruction_text"] = visual.TextStim(
        win,
        text="",
        color=TEXT_COLOR,
        height=0.032,
        wrapWidth=1.05,
        pos=(0.0, 0.03),
    )

    visuals["footer_text"] = visual.TextStim(
        win,
        text=f"Press {CONTINUE_KEY} to continue",
        color=SECONDARY_TEXT_COLOR,
        height=0.024,
        pos=(0.0, -0.34),
    )

    return visuals


def prepare_output_file(participant_info):
    """Create the data folder and choose an output CSV path."""
    safe_mkdir(DATA_DIR)
    filename = (
        f"{EXPERIMENT_NAME.replace(' ', '_')}_"
        f"{participant_info['participant_id']}_"
        f"{participant_info['session']}_"
        f"{participant_info['date_time']}.csv"
    )
    return DATA_DIR / filename


def send_trigger(label, trigger_log):
    """
    Send or log an event trigger.

    If USE_TRIGGERS is False, we simply print the trigger and record the label.
    If a lab later enables triggers, this function is the place to insert real
    parallel port, serial port, or LSL code.
    """
    if label not in TRIGGER_MAP:
        print(f"[WARNING] Unknown trigger label: {label}")

    code = TRIGGER_MAP.get(label, -1)
    if USE_TRIGGERS:
        # ------------------------------------------------------------------
        # Placeholder for real trigger hardware code.
        # Example future options:
        # - parallel port write
        # - serial write
        # - Lab Streaming Layer marker push
        # ------------------------------------------------------------------
        pass

    print(f"[TRIGGER] {label} ({code})")
    trigger_log.append(label)


def check_for_abort():
    """Abort immediately if escape has been pressed."""
    if QUIT_KEY in event.getKeys():
        raise ExperimentAbort("Experiment aborted by user.")


def wait_with_abort(seconds):
    """
    Wait while still checking for quit.

    Using short polling steps keeps the experiment responsive to ESC.
    """
    timer = core.Clock()
    while timer.getTime() < seconds:
        check_for_abort()
        core.wait(0.01)


def draw_post(visuals, username, post_text, avatar_path=None):
    """
    Draw the social-media-like post layout.

    Layout is intentionally simple and stable: avatar area, username,
    caption text, and a clean panel background.
    """
    visuals["post_panel"].draw()

    if avatar_path:
        visuals["avatar_image"].image = str(avatar_path)
        visuals["avatar_image"].draw()
    else:
        visuals["avatar_circle"].draw()

    visuals["username_text"].text = username
    visuals["username_text"].draw()

    visuals["usermeta_text"].draw()

    visuals["post_text"].text = post_text
    visuals["post_text"].draw()


def show_message_screen(win, visuals, message_text, footer_text=None):
    """Show a full-screen instruction/message page."""
    visuals["instruction_text"].text = message_text
    visuals["footer_text"].text = footer_text or f"Press {CONTINUE_KEY} to continue"

    while True:
        check_for_abort()
        visuals["instruction_text"].draw()
        visuals["footer_text"].draw()
        win.flip()
        keys = event.getKeys()
        if CONTINUE_KEY in keys:
            event.clearEvents()
            return
        if QUIT_KEY in keys:
            raise ExperimentAbort("Experiment aborted by user.")


def show_instructions(win, visuals, participant_info):
    """Present the required instruction sequence."""
    self_name = participant_info["self_username"]
    self_post = participant_info["self_post_text"]

    pages = [
        (
            "Welcome\n\n"
            f"In this task, you will see simple social-media-style posts and "
            "respond quickly to a target.\n\n"
            "Please try to keep still, look at the center of the screen, and "
            "respond as quickly and accurately as you can."
        ),
        (
            "Self vs Other Posts\n\n"
            f"Some posts will appear to belong to you, using the username {self_name}.\n"
            f"Your self-post text is:\n\"{self_post}\"\n\n"
            "Your selected avatar will stay with your account during self trials.\n\n"
            "Other posts will appear to belong to other users and will use standardized post text and avatars.\n\n"
            "Please pay attention to whether each post is presented as yours or someone else's."
        ),
        (
            "Reward vs Punishment Cues\n\n"
            "A circle means a reward trial.\n"
            "If you respond fast enough, you can earn positive social feedback.\n\n"
            "A square means a punishment trial.\n"
            "If you respond fast enough, you can avoid negative social feedback."
        ),
        (
            "Your Response Task\n\n"
            "After a short delay, a white target will appear in the center.\n\n"
            f"Press either the {LEFT_KEY} or {RIGHT_KEY} key as quickly as possible "
            "when the target appears.\n\n"
            "This is a speeded response task. You do not choose between posts."
        ),
        (
            "Practice\n\n"
            "You will now complete a short practice block.\n\n"
            "Use the practice to learn the sequence:\n"
            "post -> cue -> delay -> target -> feedback -> comment area."
        ),
    ]

    for page in pages:
        show_message_screen(win, visuals, page)


def choose_post_assets(trial, stimuli, rng, participant_info):
    """
    Select the username, post text, and avatar for a trial.

    Self trials use the participant nickname and typed post text.
    Other trials sample another user and a standardized post text.
    """
    if trial["post_relevance"] == "self":
        username = participant_info["self_username"]
        post_text = participant_info["self_post_text"]
        avatar_path = participant_info.get("self_avatar_path")
    else:
        username = rng.choice(OTHER_USERNAMES)
        post_text = rng.choice(OTHER_POST_TEXTS)
        avatar_path = rng.choice(stimuli["avatars"]) if stimuli["avatars"] else None

    return username, post_text, avatar_path


def get_feedback_phase1_text(cue_type, win_boolean):
    """Map outcome and cue type to the required phase 1 feedback."""
    if cue_type == "reward":
        return "Like +1" if win_boolean else "Like +0"
    return "Dislike 0" if win_boolean else "Dislike 1"


def get_feedback_phase2_comment(cue_type, win_boolean, rng):
    """Map outcome and cue type to the required comment behavior."""
    if cue_type == "reward" and win_boolean:
        return rng.choice(POSITIVE_COMMENTS)
    if cue_type == "punishment" and not win_boolean:
        return rng.choice(NEGATIVE_COMMENTS)
    return ""


def show_fixation(win, visuals, duration):
    """Draw central fixation for a fixed duration."""
    visuals["fixation"].draw()
    win.flip()
    wait_with_abort(duration)


def show_post_phase(win, visuals, username, post_text, avatar_path, trigger_label):
    """Show the post and send the corresponding trigger."""
    trigger_log = []
    draw_post(visuals, username, post_text, avatar_path)
    win.flip()
    send_trigger(trigger_label, trigger_log)
    wait_with_abort(POST_DUR)
    return trigger_log


def show_cue_phase(win, visuals, cue_type):
    """Show reward/punishment cue using simple stable shapes."""
    trigger_log = []
    if cue_type == "reward":
        visuals["cue_reward"].draw()
        visuals["cue_label"].text = "Reward"
        trigger_label = "reward_cue"
    else:
        visuals["cue_punishment"].draw()
        visuals["cue_label"].text = "Punishment"
        trigger_label = "punishment_cue"

    visuals["cue_label"].draw()
    win.flip()
    send_trigger(trigger_label, trigger_log)
    wait_with_abort(CUE_DUR)
    return trigger_log


def show_delay_phase(win, visuals, duration):
    """Use fixation during the anticipation delay."""
    visuals["fixation"].draw()
    win.flip()
    wait_with_abort(duration)


def run_target_phase(win, visuals):
    """
    Present the central target and collect a speeded response.

    RT is measured from target onset. Either response key is accepted.
    """
    trigger_log = []
    response_clock = core.Clock()
    event.clearEvents()

    visuals["target"].draw()
    win.flip()
    response_clock.reset()
    send_trigger("target_onset", trigger_log)

    responded = False
    response_key = ""
    rt = math.nan

    while response_clock.getTime() < TARGET_TIMEOUT:
        check_for_abort()
        keys = event.getKeys(keyList=ALLOWED_RESPONSE_KEYS + [QUIT_KEY], timeStamped=response_clock)
        if keys:
            first_key, key_time = keys[0]
            if first_key == QUIT_KEY:
                raise ExperimentAbort("Experiment aborted by user.")
            responded = True
            response_key = first_key
            rt = key_time
            if response_key == LEFT_KEY:
                send_trigger("response_left", trigger_log)
            elif response_key == RIGHT_KEY:
                send_trigger("response_right", trigger_log)
            break
        core.wait(0.001)

    if not responded:
        send_trigger("response_missed", trigger_log)

    return responded, response_key, rt, trigger_log


def show_feedback_phase1(win, visuals, feedback_text):
    """Show the first feedback phase (like/dislike count)."""
    trigger_log = []
    visuals["feedback1_text"].text = feedback_text
    visuals["feedback1_text"].draw()
    win.flip()
    send_trigger("feedback1_onset", trigger_log)
    wait_with_abort(FEEDBACK1_DUR)
    return trigger_log


def show_feedback_gap(win):
    """Brief neutral blank interval between feedback phases."""
    win.flip()
    wait_with_abort(BETWEEN_FEEDBACK_DUR)


def show_feedback_phase2(win, visuals, comment_text):
    """
    Show the comment area in a fixed location.

    Even when no comment is shown, we still present the same comment bubble
    region to keep the layout visually stable.
    """
    trigger_log = []
    visuals["comment_bubble"].draw()
    visuals["comment_text"].text = comment_text
    visuals["comment_text"].draw()
    win.flip()
    send_trigger("feedback2_onset", trigger_log)
    wait_with_abort(FEEDBACK2_DUR)
    return trigger_log


def update_threshold(current_threshold, win_boolean):
    """
    Update the adaptive RT threshold.

    This is a simple staircase rule:
    - win -> slightly harder next trial
    - loss or miss -> slightly easier next trial
    """
    step = THRESHOLD_STEP_AFTER_WIN if win_boolean else THRESHOLD_STEP_AFTER_LOSS
    next_threshold = current_threshold + step
    return clamp(next_threshold, MIN_RT_THRESHOLD, MAX_RT_THRESHOLD)


def trial_result_from_rt(rt, responded, threshold):
    """Determine win/loss based on whether RT beat the current threshold."""
    if responded and not math.isnan(rt) and rt <= threshold:
        return "win", True
    return "loss", False


def run_trial(
    win,
    visuals,
    trial,
    participant_info,
    stimuli,
    threshold_current,
    rng,
    global_clock,
):
    """
    Run one full trial from fixation through ITI.

    Returns:
        trial_record (dict), updated_threshold (float)
    """
    event.clearEvents()
    trial_trigger_labels = []
    trial_start_global = global_clock.getTime()

    username, post_text, avatar_path = choose_post_assets(
        trial, stimuli, rng, participant_info
    )

    # 1. Fixation
    show_fixation(win, visuals, FIXATION_DUR)

    # 2. Post display
    post_trigger = (
        "self_post_onset" if trial["post_relevance"] == "self" else "other_post_onset"
    )
    trial_trigger_labels.extend(
        show_post_phase(
            win, visuals, username, post_text, avatar_path, post_trigger
        )
    )

    # 3. Cue display
    trial_trigger_labels.extend(show_cue_phase(win, visuals, trial["cue_type"]))

    # 4. Anticipation delay
    anticipation_dur = rng.uniform(ANTICIPATION_MIN, ANTICIPATION_MAX)
    show_delay_phase(win, visuals, anticipation_dur)

    # 5. Target
    responded, response_key, rt, target_triggers = run_target_phase(win, visuals)
    trial_trigger_labels.extend(target_triggers)

    actual_outcome, win_boolean = trial_result_from_rt(rt, responded, threshold_current)
    send_trigger(f"outcome_{actual_outcome}", trial_trigger_labels)

    # 6. Feedback phase 1
    feedback1_text = get_feedback_phase1_text(trial["cue_type"], win_boolean)
    trial_trigger_labels.extend(show_feedback_phase1(win, visuals, feedback1_text))

    # 7. Gap between feedback phases
    show_feedback_gap(win)

    # 8. Feedback phase 2
    comment_text = get_feedback_phase2_comment(trial["cue_type"], win_boolean, rng)
    trial_trigger_labels.extend(show_feedback_phase2(win, visuals, comment_text))

    # 9. ITI
    iti_dur = rng.uniform(ITI_MIN, ITI_MAX)
    show_fixation(win, visuals, iti_dur)

    threshold_next = update_threshold(threshold_current, win_boolean)

    trial_record = {
        "participant_id": participant_info["participant_id"],
        "session": participant_info["session"],
        "nickname": participant_info["nickname"],
        "age": participant_info["age"],
        "self_post_text_input": participant_info["self_post_text"],
        "self_avatar_choice": participant_info.get("self_avatar_choice", ""),
        "random_seed": participant_info["random_seed"],
        "task_name": EXPERIMENT_NAME,
        "task_version": TASK_VERSION,
        "psychopy_version": psychopy.__version__,
        "trial_index": trial["trial_index"],
        "block_index": trial["block_index"],
        "practice_or_main": trial["practice_or_main"],
        "post_relevance": trial["post_relevance"],
        "cue_type": trial["cue_type"],
        "design_cell_outcome_label": trial["design_cell_outcome_label"],
        "expected_outcome_type": trial["expected_outcome_type"],
        "actual_outcome": actual_outcome,
        "win_boolean": int(win_boolean),
        "rt": "" if math.isnan(rt) else round(rt, 4),
        "responded": int(responded),
        "response_key": response_key,
        "threshold_current": round(threshold_current, 4),
        "threshold_next": round(threshold_next, 4),
        "post_username": username,
        "post_text": post_text,
        "avatar_filename": avatar_path.name if avatar_path else "",
        "comment_text": comment_text,
        "feedback1_text": feedback1_text,
        "trigger_labels": "|".join(trial_trigger_labels),
        "timestamp_global": round(global_clock.getTime(), 4),
        "timestamp_trial_start": round(trial_start_global, 4),
        "anticipation_delay": round(anticipation_dur, 4),
        "iti_delay": round(iti_dur, 4),
    }

    return trial_record, threshold_next


def save_data(rows, filepath):
    """
    Save all accumulated trial data to CSV.

    This function rewrites the full file each time it is called. That is a
    simple and robust approach for lab scripts because partial data remain
    recoverable if the run is interrupted.
    """
    if not rows:
        return

    safe_mkdir(filepath.parent)
    fieldnames = list(rows[0].keys())

    with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_practice(practice_rows):
    """Create a short human-readable practice summary."""
    if not practice_rows:
        return "Practice finished."

    responded_n = sum(row["responded"] for row in practice_rows)
    win_n = sum(row["win_boolean"] for row in practice_rows)
    valid_rts = [row["rt"] for row in practice_rows if row["rt"] != ""]
    mean_rt_ms = round(1000 * sum(valid_rts) / len(valid_rts), 1) if valid_rts else None

    lines = [
        "End of Practice\n",
        f"Trials completed: {len(practice_rows)}",
        f"Responses made: {responded_n}",
        f"Successful fast responses (wins): {win_n}",
    ]
    if mean_rt_ms is not None:
        lines.append(f"Mean RT: {mean_rt_ms} ms")

    lines.append(
        "\nIf anything was unclear, ask the experimenter now.\n\n"
        "The main task will begin next."
    )
    return "\n".join(lines)


def run_practice(
    win,
    visuals,
    practice_trials,
    participant_info,
    stimuli,
    starting_threshold,
    rng,
    global_clock,
):
    """Run the practice block and return rows plus updated threshold."""
    threshold = starting_threshold
    practice_rows = []

    for trial in practice_trials:
        row, threshold = run_trial(
            win=win,
            visuals=visuals,
            trial=trial,
            participant_info=participant_info,
            stimuli=stimuli,
            threshold_current=threshold,
            rng=rng,
            global_clock=global_clock,
        )
        practice_rows.append(row)
        TRIAL_DATA.append(row)
        save_data(TRIAL_DATA, CURRENT_DATA_FILE)

    return practice_rows, threshold


def run_main_blocks(
    win,
    visuals,
    main_blocks,
    participant_info,
    stimuli,
    starting_threshold,
    rng,
    global_clock,
):
    """Run the three main blocks."""
    threshold = starting_threshold

    show_message_screen(
        win,
        visuals,
        "Main Task\n\n"
        "The practice is complete.\n\n"
        "The main task will now begin. Keep your eyes near the center, stay as still as you can, "
        "and respond quickly when the target appears.",
    )

    for block_number, block_trials in enumerate(main_blocks, start=1):
        block_trigger_log = []
        send_trigger("block_start", block_trigger_log)

        for trial in block_trials:
            row, threshold = run_trial(
                win=win,
                visuals=visuals,
                trial=trial,
                participant_info=participant_info,
                stimuli=stimuli,
                threshold_current=threshold,
                rng=rng,
                global_clock=global_clock,
            )
            TRIAL_DATA.append(row)
            save_data(TRIAL_DATA, CURRENT_DATA_FILE)

        send_trigger("block_end", block_trigger_log)

        # Show block break after block 1 and 2, but not after the last block.
        if block_number < len(main_blocks):
            show_message_screen(
                win,
                visuals,
                f"Block {block_number} of {len(main_blocks)} complete\n\n"
                "You can take a short break.\n\n"
                "Please try to keep your body relaxed and minimize movement.\n\n"
                f"Press {CONTINUE_KEY} when you are ready to continue.",
                footer_text=f"Press {CONTINUE_KEY} when ready",
            )


def close_experiment(win):
    """Close PsychoPy objects cleanly."""
    try:
        if win is not None:
            win.close()
    finally:
        core.quit()


def main():
    """
    Main experiment function.

    This keeps setup, running, saving, and cleanup in one place.
    """
    global PARTICIPANT_INFO, CURRENT_DATA_FILE

    logging.console.setLevel(logging.WARNING)
    check_psychopy_version()

    win = None
    global_clock = core.Clock()

    try:
        PARTICIPANT_INFO = get_participant_info()
        random.seed(PARTICIPANT_INFO["random_seed"])
        rng = random.Random(PARTICIPANT_INFO["random_seed"])

        CURRENT_DATA_FILE = prepare_output_file(PARTICIPANT_INFO)
        stimuli = load_stimuli(rng)
        win = create_window()
        PARTICIPANT_INFO = run_self_selection(win, PARTICIPANT_INFO, stimuli)
        visuals = create_visuals(win)
        practice_trials, main_blocks = create_trial_list(rng)
        global_clock.reset()

        show_instructions(win, visuals, PARTICIPANT_INFO)

        practice_rows, threshold_after_practice = run_practice(
            win=win,
            visuals=visuals,
            practice_trials=practice_trials,
            participant_info=PARTICIPANT_INFO,
            stimuli=stimuli,
            starting_threshold=INITIAL_RT_THRESHOLD,
            rng=rng,
            global_clock=global_clock,
        )

        show_message_screen(win, visuals, summarize_practice(practice_rows))

        run_main_blocks(
            win=win,
            visuals=visuals,
            main_blocks=main_blocks,
            participant_info=PARTICIPANT_INFO,
            stimuli=stimuli,
            starting_threshold=threshold_after_practice,
            rng=rng,
            global_clock=global_clock,
        )

        end_trigger_log = []
        send_trigger("experiment_end", end_trigger_log)
        save_data(TRIAL_DATA, CURRENT_DATA_FILE)

        show_message_screen(
            win,
            visuals,
            "Thank You\n\n"
            "The task is now complete.\n\n"
            "Please wait for the experimenter.",
            footer_text="Press space to finish",
        )

    except ExperimentAbort:
        print("[INFO] Participant initiated abort.")
        if CURRENT_DATA_FILE is not None:
            save_data(TRIAL_DATA, CURRENT_DATA_FILE)
        if win is not None:
            abort_text = visual.TextStim(
                win,
                text="Experiment stopped.\n\nPartial data have been saved.",
                color=TEXT_COLOR,
                height=0.035,
                wrapWidth=1.0,
            )
            abort_text.draw()
            win.flip()
            core.wait(1.5)

    except Exception as exc:
        print(f"[ERROR] {exc}")
        if CURRENT_DATA_FILE is not None:
            save_data(TRIAL_DATA, CURRENT_DATA_FILE)
        raise

    finally:
        close_experiment(win)


if __name__ == "__main__":
    main()
