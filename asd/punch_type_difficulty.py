from __future__ import annotations

import shutil
import sys
import time

import punch_type_menu as m
from sound.punch_type_sound import play_sfx
from punch_type_menu import (
    BOLD, CLEAR, CLEAR_EOL, FPS, HIDE_CURSOR, HOME, PORTRAIT_W, RESET,
    SHOW_CURSOR, c, enable_ansi_on_windows, poll_key, portrait_art,
    portrait_box, raw_input_mode, _row,
)

HEIGHT = 26

FONT = dict(m.FONT)
FONT.update({
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
})

DIFFICULTIES = [
    {"name": "EASY", "stars": "*", "color": 46, "hp": 500, "dmg": 10, "time": "3s", "win": 500,
     "keys": "QWERTY"},
    {"name": "MEDIUM", "stars": "**", "color": 220, "hp": 1000, "dmg": 25, "time": "2s", "win": 800,
     "keys": "QWERTYASDFGH"},
    {"name": "HARD", "stars": "***", "color": 196, "hp": 1500, "dmg": 50, "time": "1.5s", "win": 1000,
     "keys": "QWERTYASDFGHZXCVB"},
]
DIFF_BTN_W = 31
BACK_BTN_W = 15

_reason = ""


def block_text(text):
    return [" ".join(FONT[ch][row] for ch in text) for row in range(5)]


def _diff_button(label, stars, inner, kind):
    if kind != 1:
        return "+" + "-" * inner + "+"
    if stars:
        text = (" " + stars.ljust(3)).ljust(4) + label.center(inner - 8) + " " * 4
    else:
        text = label.center(inner)
    return "|" + text + "|"


def _button_parts(text, style, active, kind, box_left, pulse, arrow_color):
    if active and kind == 1:
        a = box_left - 4 + pulse
        arrow = arrow_color + BOLD
        return [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
    return [(" " * box_left, ""), (text, style)]


def _frame(lines):
    size = m._sync_size()
    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        top = extra // 4
        middle = extra // 4
        lines = (lines[:2] + [blank] * top + lines[2:8] + [blank] * middle + lines[8:-3]
                 + [blank] * (extra - top - middle) + lines[-3:])
    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


def _render_difficulty(t, sel, flash, punching):
    m._sync_size()
    inner = m.INNER
    lines = [c(208) + "+" + "=" * inner + "+" + RESET]

    label = "S E L E C T"
    lines.append(_row([(" " * ((inner - len(label)) // 2), ""), (label, c(250) + BOLD)]))

    rows = block_text("DIFFICULTY")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.5 * tw))
    pad = (inner - tw) // 2
    sweep = int(t * 30) % (tw + 30) - 10
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                hot = 0 <= (i - sweep + r) < 5
                parts.append(("#", (c(196) if hot else c(255)) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    uline = []
    for i in range(tw):
        hot = 0 <= (i - sweep) < 8
        uline.append(("=" if i < reveal else " ", c(196) + BOLD if hot else c(250)))
    lines.append(_row([(" " * pad, "")] + uline))

    left_w = min(inner - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (inner - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, inner - lead - left_w - PORTRAIT_W - 2)
    pulse = int(t * 3) % 2
    art = portrait_art(t, punching)
    if sel == 2:
        art = [l.replace("(o) (o)", "(>) (<)").replace("(-) (-)", "(>) (<)") for l in art]
    portrait = portrait_box(art=art)

    for k in range(15):
        j, kind = divmod(k, 4)
        left = []
        if k <= 10 and kind != 3 and t >= 0.5 + 0.12 * j:
            d = DIFFICULTIES[j]
            box_left = (left_w - (DIFF_BTN_W + 2)) // 2
            text = _diff_button(d["name"], d["stars"], DIFF_BTN_W, kind)
            active = j == sel
            if active:
                if kind != 1:
                    text = "+" + "=" * DIFF_BTN_W + "+"
                style = (c(15) if flash else c(d["color"])) + BOLD
            else:
                style = c(240)
            left = _button_parts(text, style, active, kind, box_left, pulse, c(d["color"]))
        elif k >= 12 and t >= 0.5 + 0.12 * 3:
            kind = k - 12
            box_left = (left_w - (BACK_BTN_W + 2)) // 2
            text = _diff_button("<- BACK", "", BACK_BTN_W, kind)
            active = sel == 3
            if active:
                if kind != 1:
                    text = "+" + "=" * BACK_BTN_W + "+"
                style = (c(15) if flash else c(250)) + BOLD
            else:
                style = c(240)
            left = _button_parts(text, style, active, kind, box_left, pulse, c(250))
        left = m._fit(left, left_w)

        if k <= 10 and t >= 0.8:
            p = portrait[k]
            edge = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    if sel < 3:
        d = DIFFICULTIES[sel]
        info = f"HP {d['hp']} | DMG {d['dmg']} | REACT {d['time']} | WIN +{d['win']} G | KEYS {d['keys']}"
        info_style = c(d["color"]) + BOLD
    else:
        info = "Return to the main menu"
        info_style = c(250)
    lines.append(_row([(" " * ((inner - len(info)) // 2), ""), (info, info_style)]))

    hint = "W/S or UP/DOWN to move   ENTER to select   1 2 3 pick   4 or ESC back"
    lines.append(_row([(" " * ((inner - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * inner + "+" + RESET)
    return _frame(lines)


def _can_animate():
    global _reason
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _reason = ("this is not a real terminal. Open Command Prompt / PowerShell / "
                   "Windows Terminal and run:  python punch_type.py")
        return False
    size = shutil.get_terminal_size((80, 30))
    if size.columns < 80 or size.lines < HEIGHT + 2:
        _reason = (f"your terminal is {size.columns}x{size.lines}; this screen needs at least "
                   f"80x{HEIGHT + 2}. Maximize the terminal or reduce its font size, then restart.")
        return False
    m.WIDTH = max(78, size.columns)
    m.INNER = m.WIDTH - 2
    return True


def _static_difficulty():
    print(f"(Animation is off: {_reason})")
    print("CONTROLS FOR EASY MODE IS QWERTY. FOR MEDIUM AND HARD, MORE LETTERS ARE ADDED.")
    print("=====================")
    print("Select Difficulty")
    print("1.EASY")
    print("2.MEDIUM")
    print("3.HARD")
    print("4.BACK")
    print("=====================")
    try:
        return int(input())
    except ValueError:
        return 0
    except EOFError:
        return 4


def run_difficulty_menu():
    enable_ansi_on_windows()
    if not _can_animate():
        return _static_difficulty()

    sel, result = 0, 4
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if m._too_small(out, HEIGHT + 2):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % 4
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % 4
                    play_sfx("move")
                elif key in ("1", "2", "3", "4"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 4
                    play_sfx("back")
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("back" if sel == 3 else "select")
                    for i in range(8):
                        out.write(_render_difficulty(t + i * 0.05, sel, i % 2 == 0, sel < 3))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_difficulty(t, sel, False, False))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 4
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result


if __name__ == "__main__":
    print("You chose:", run_difficulty_menu())
