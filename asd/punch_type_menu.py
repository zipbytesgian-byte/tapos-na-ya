from __future__ import annotations

import os
import shutil
import sys
import time
from contextlib import contextmanager

from sound.punch_type_sound import play_sfx

WIDTH = 78
INNER = WIDTH - 2
HEIGHT = 26
FPS = 30

FONT = {
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    # CHANGE: letters L and S added so the lose screen can write "YOU LOSE"
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}
TITLE = "PUNCH TYPE"


def block_text(text):
    return [" ".join(FONT[ch][row] for ch in text) for row in range(5)]


PORTRAIT_W = 22

FRAME_IDLE = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    "   |  (o) (o)  |    ",
    "    \\    ^    /     ",
    "     \\  ===  /      ",
    "  (@)==\\_____/==(@)  ",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]
FRAME_GUARD = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    " (@)|  (o) (o)  |(@) ",
    "    \\    ^    /     ",
    "     \\  ===  /      ",
    "     /\\_____/\\      ",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]
FRAME_PUNCH = [
    "     .-\"\"\"\"\"-.      ",
    "    /  ,   ,  \\     ",
    "   |  (>) (<)  |    ",
    "    \\    O    /     ",
    "     \\  ===  /      ",
    "  (@)=\\_____/=====(@)",
    "      /|  *  |\\      ",
    "     / |     | \\     ",
    "       |_____|       ",
]


def portrait_art(t=0.0, punching=False):
    if punching or 5.0 <= (t % 6.0) < 5.3:
        frame = FRAME_PUNCH
    else:
        frame = FRAME_IDLE if int(t * 2) % 2 == 0 else FRAME_GUARD
        if (t % 3.2) < 0.15:
            frame = [l.replace("(o) (o)", "(-) (-)") for l in frame]
    return [l.center(PORTRAIT_W)[:PORTRAIT_W] for l in frame]


def portrait_box(title="FIGHTER", art=None):
    art = art or portrait_art()
    top = "+" + f" {title} ".center(PORTRAIT_W, "-") + "+"
    return [top, *["|" + l + "|" for l in art], "+" + "-" * PORTRAIT_W + "+"]


BUTTONS = [("1", "START"), ("2", "SHOP"), ("3", "EXIT")]
BUTTON_W = 19


def button_text(index, kind):
    num, name = BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"


def draw_main_menu(gold=0):
    def row(text=""):
        return "|" + text.ljust(INNER)[:INNER] + "|"

    border = "+" + "=" * INNER + "+"
    stars = "*" * INNER

    lines = [border, row(f"  GOLD: {gold} [o]"), row()]
    lines += [row(l.center(INNER)) for l in block_text(TITLE)]
    lines += [row(), row(stars), row()]

    buttons = []
    for i in range(len(BUTTONS)):
        buttons += [button_text(i, 0), button_text(i, 1), button_text(i, 2)]
        if i < len(BUTTONS) - 1:
            buttons.append("")
    portrait = portrait_box()

    right_margin = 4
    left_w = INNER - PORTRAIT_W - 2 - right_margin
    for b, p in zip(buttons, portrait):
        lines.append(row(b.center(left_w) + p.ljust(PORTRAIT_W + 2) + " " * right_margin))

    lines += [row(), row(stars), row("Type 1, 2 or 3 and press ENTER".center(INNER)), border]
    return "\n".join(lines)


RESET = "\x1b[0m"
BOLD = "\x1b[1m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"
CLEAR_EOL = "\x1b[K"

FIRE = [196, 202, 208, 214, 220, 226, 220, 214, 208, 202]


def c(n):
    return f"\x1b[38;5;{n}m"


def enable_ansi_on_windows():
    if os.name != "nt":
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if k32.GetConsoleMode(handle, ctypes.byref(mode)):
            k32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        os.system("")


def _normalize(ch):
    ch = ch.lower()
    if ch.isdigit():
        return ch
    return {"w": "up", "s": "down", "\r": "enter", "\n": "enter",
            "q": "quit", "\x03": "quit", "\x04": "quit"}.get(ch, "")


if os.name == "nt":
    import msvcrt

    @contextmanager
    def raw_input_mode():
        yield

    def poll_key():
        if not msvcrt.kbhit():
            return ""
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        if ch == "\x1b":
            return "quit"
        return _normalize(ch)

else:
    import select
    import termios
    import tty

    @contextmanager
    def raw_input_mode():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _ready():
        return bool(select.select([sys.stdin], [], [], 0)[0])

    def poll_key():
        if not _ready():
            return ""
        ch = os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
        if ch == "\x1b":
            seq = ""
            time.sleep(0.01)
            while _ready() and len(seq) < 2:
                seq += os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
            if not seq:
                return "quit"
            return {"[A": "up", "[B": "down"}.get(seq, "")
        return _normalize(ch)


EDGE = c(208) + "|" + RESET


_last_size = None


def _sync_size():
    global WIDTH, INNER
    size = shutil.get_terminal_size((80, 28))
    WIDTH = max(78, size.columns)
    INNER = WIDTH - 2
    return size


def _too_small(out, min_rows=None):
    global _last_size
    size = shutil.get_terminal_size((80, 28))
    if size != _last_size:
        _last_size = size
        out.write(CLEAR)
    need = min_rows or HEIGHT + 2
    if size.columns >= 80 and size.lines >= need:
        return False
    out.write(HOME + f"TERMINAL TOO SMALL: NEED 80x{need}, YOU HAVE "
              f"{size.columns}x{size.lines}. ENLARGE THE WINDOW." + CLEAR_EOL)
    out.flush()
    time.sleep(0.2)
    return True


def _plain_len(parts):
    return sum(len(text) for text, _ in parts)


def _fit(parts, width):
    extra = width - _plain_len(parts)
    return parts + [(" " * extra, "")] if extra > 0 else parts


def _paint(parts):
    return "".join(f"{style}{text}{RESET}" if style and text else text for text, style in parts)


def _row(parts):
    return EDGE + _paint(_fit(parts, INNER)) + EDGE


def _render(t, intro, sel, shown_gold, flash, punching):
    def visible(start):
        return (not intro) or t >= start

    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET]

    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(int(shown_gold)), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))
    lines.append(_row([]))

    rows = block_text(TITLE)
    tw = len(rows[0])
    reveal = tw if not intro else min(tw, int(t / 0.9 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    lines += [_row([]), stars(), _row([])]

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(art=portrait_art(t, punching))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or not visible(1.0 + 0.15 * j):
            left = []
        else:
            text = button_text(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if visible(1.5):
            p = portrait[k]
            border_style = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, border_style)]
            else:
                right = [(p[0], border_style), (p[1:-1], c(252)), (p[-1], border_style)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    mid_end = len(lines)
    lines += [_row([]), stars()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2 3"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:3] + [blank] * gap_top + lines[3:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


_intro_done = False
_shown_gold = 0.0
_note_shown = False


_reason = ""


def _try_resize(cols=100, rows=35):
    try:
        if os.name == "nt":
            os.system(f"mode con: cols={cols} lines={rows}")
        else:
            sys.stdout.write(f"\x1b[8;{rows};{cols}t")
            sys.stdout.flush()
        time.sleep(0.2)
    except Exception:
        pass


def _can_animate():
    global _reason, WIDTH, INNER
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _reason = ("this is not a real terminal (IDLE, Thonny, an IDE 'Run' panel or piped "
                   "input can't redraw the screen). Open Command Prompt / PowerShell / "
                   "Windows Terminal and run:  python punch_type.py")
        return False

    size = shutil.get_terminal_size((80, 28))
    if size.columns < 80 or size.lines < HEIGHT + 2:
        _reason = (f"your terminal is {size.columns}x{size.lines}; the animated menu needs "
                   f"at least 80x{HEIGHT + 2}. Maximize the terminal or reduce its font size, then restart.")
        return False

    WIDTH = max(78, size.columns)
    INNER = WIDTH - 2
    return True


def _static_menu(gold):
    global _note_shown
    print(draw_main_menu(gold))
    if not _note_shown:
        _note_shown = True
        print(f"(Animation is off: {_reason})")
    try:
        return int(input("ENTER CHOICE: "))
    except ValueError:
        return 0
    except EOFError:
        return 3


def run_main_menu(gold=0):
    global _intro_done, _shown_gold
    enable_ansi_on_windows()
    if not _can_animate():
        return _static_menu(gold)

    intro = not _intro_done
    shown = float(gold) if _shown_gold > gold else _shown_gold
    rate = max(1.0, (gold - shown) / 0.8)
    sel, typed, result = 0, "", 3
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = last = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                dt, last, t = now - last, now, now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel, typed = (sel - 1) % len(BUTTONS), ""
                    play_sfx("move")
                elif key == "down":
                    sel, typed = (sel + 1) % len(BUTTONS), ""
                    play_sfx("move")
                elif key.isdigit():
                    typed = (typed + key)[-3:]
                    if key in "123":
                        sel = int(key) - 1
                        play_sfx("move")
                elif key == "quit":
                    result = 3
                    break
                elif key == "enter":
                    result = 110 if typed.endswith("110") else sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render(t + i * 0.05, intro, sel, shown, i % 2 == 0, True))
                        out.flush()
                        time.sleep(0.05)
                    break

                if shown < gold:
                    shown = min(float(gold), shown + rate * dt)
                out.write(_render(t, intro, sel, shown, False, False))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 3
    finally:
        _intro_done = True
        _shown_gold = float(gold)
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result


def _render_exit(t, punching):
    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET, _row([]), _row([])]

    rows = block_text("THANK YOU")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))

    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    lines += [_row([]), stars(), _row([])]

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(art=portrait_art(t, punching))
    texts = {1: ("FOR PLAYING!", c(15) + BOLD),
             3: ("SEE YOU NEXT TIME,", c(250)),
             4: ("FIGHTER!", c(226) + BOLD)}

    for k in range(11):
        left = []
        if k in texts:
            text, style = texts[k]
            left = [(" " * ((left_w - len(text)) // 2), ""), (text, style)]
        elif 6 <= k <= 8:
            kind = k - 6
            if kind == 1:
                text = "|" + "PRESS ENTER".center(BUTTON_W) + "|"
            else:
                text = "+" + "=" * BUTTON_W + "+"
            style = c(226) + BOLD
            if kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        p = portrait[k]
        edge = c(45)
        if k in (0, len(portrait) - 1):
            right = [(p, edge)]
        else:
            right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))

    mid_end = len(lines)
    lines += [_row([]), stars()]
    hint = "THANK YOU FOR PLAYING!   PRESS ENTER TO EXIT"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:3] + [blank] * gap_top + lines[3:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


VICTORY_BUTTONS = [("1", "RETRY"), ("2", "MENU"), ("3", "EXIT")]


def _victory_button(index, kind):
    num, name = VICTORY_BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"


def _render_victory(t, sel, flash, punching, info):
    size = _sync_size()
    lines = [c(208) + "+" + "=" * INNER + "+" + RESET]

    grow = min(1.0, max(0.0, (t - 0.8) / 1.0))
    shown_gold = info["gold"] - info["earned"] + int(info["earned"] * grow)
    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(shown_gold), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))

    rows = block_text("YOU WIN")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    title_end = len(lines)

    def stars():
        shift = int(t * 10)
        return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                     for i in range(INNER)])

    note = info["note"]
    if note and t >= 1.0:
        style = c(FIRE[int(t * 8) % len(FIRE)]) + BOLD
        lines.append(_row([(" " * ((INNER - len(note)) // 2), ""), (note, style)]))
    else:
        lines.append(_row([]))
    lines.append(stars())

    count = min(1.0, max(0.0, (t - 1.0) / 0.8))
    stats = [("HITS GIVEN", info["phit"], 46), ("HITS TAKEN", info["ehit"], 196),
             ("CRITICAL HITS", info["crits"], 208), ("GOLD EARNED", info["earned"], 226)]
    cell = INNER // 4
    label_parts = []
    value_parts = []
    for i, (label, value, color) in enumerate(stats):
        width = cell if i < 3 else INNER - 3 * cell
        text = str(int(value * count))
        if label == "GOLD EARNED":
            text = "+" + text + " G"
        label_parts.append((label.center(width), c(250)))
        value_parts.append((text.center(width), c(color) + BOLD))
    lines.append(_row(label_parts))
    lines.append(_row(value_parts))
    lines.append(stars())

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(title="WINNER", art=portrait_art(t, punching))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or t < 1.0 + 0.15 * j:
            left = []
        else:
            text = _victory_button(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(196) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if t >= 1.2:
            p = portrait[k]
            edge = c(45)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))
    mid_end = len(lines)

    lines += [_row([]), stars()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2 3"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(208) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:2] + [blank] * gap_top + lines[2:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


def run_victory_screen(gold, earned, phit, ehit, crits, note=""):
    enable_ansi_on_windows()
    if not _can_animate():
        return None
    info = {"gold": gold, "earned": earned, "phit": phit, "ehit": ehit,
            "crits": crits, "note": note}
    sel, result = 0, 3
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % len(VICTORY_BUTTONS)
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % len(VICTORY_BUTTONS)
                    play_sfx("move")
                elif key in ("1", "2", "3"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 3
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_victory(t + i * 0.05, sel, i % 2 == 0, True, info))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_victory(t, sel, False, False, info))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 3
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result


# ======================================================================
# CHANGE: NEW LOSE SCREEN. It is built the same way as the victory screen
# above (same helpers, same layout), but it is red, the title says
# "YOU LOSE", and the fighter is knocked out (x x eyes, wobbling).
# ======================================================================
DEFEAT_BUTTONS = [("1", "RETRY"), ("2", "MENU")]
DEFEAT_RED = [196, 160, 124, 160]          # dark red colors for the title flicker


def _defeat_button(index, kind):
    num, name = DEFEAT_BUTTONS[index]
    if kind == 1:
        return "|" + f"{num}  [ {name:^7} ]".center(BUTTON_W) + "|"
    return "+" + "=" * BUTTON_W + "+"


def _defeat_art(t):
    # take the normal fighter picture and make it look knocked out
    art = [l.replace("(o) (o)", "(x) (x)").replace("(>) (<)", "(x) (x)") for l in FRAME_IDLE]
    art[3] = art[3].replace("^", "~")      # sad mouth
    art[5] = art[5].replace("(@)==", "(@)  ").replace("==(@)", "  (@)")   # gloves drop
    if int(t * 2) % 2 == 1:                # little wobble: slide the fighter 1 space
        art = [" " + l[:-1] for l in art]
    return [l.ljust(PORTRAIT_W)[:PORTRAIT_W] for l in art]   # keep the box edges straight


def _render_defeat(t, sel, flash, info):
    size = _sync_size()
    lines = [c(196) + "+" + "=" * INNER + "+" + RESET]

    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines.append(_row([("  GOLD: ", c(220) + BOLD), (str(info["gold"]), c(226) + BOLD),
                       (" ", ""), (coin, c(220) + BOLD)]))

    rows = block_text("YOU LOSE")
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                shade = DEFEAT_RED[(i // 2 + r - int(t * 6)) % len(DEFEAT_RED)]
                parts.append(("#", c(shade) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    title_end = len(lines)

    def dots():
        shift = int(t * 6)
        return _row([("x", c(196) + BOLD) if (i + shift) % 6 == 0 else (".", c(238))
                     for i in range(INNER)])

    msg = "DON'T GIVE UP, FIGHTER!"
    if t >= 1.0:
        lines.append(_row([(" " * ((INNER - len(msg)) // 2), ""), (msg, c(250) + BOLD)]))
    else:
        lines.append(_row([]))
    lines.append(dots())

    count = min(1.0, max(0.0, (t - 1.0) / 0.8))
    stats = [("HITS GIVEN", info["phit"], 46), ("HITS TAKEN", info["ehit"], 196),
             ("CRITICAL HITS", info["crits"], 208), ("GOLD EARNED", info["earned"], 226)]
    cell = INNER // 4
    label_parts = []
    value_parts = []
    for i, (label, value, color) in enumerate(stats):
        width = cell if i < 3 else INNER - 3 * cell
        text = str(int(value * count))
        if label == "GOLD EARNED":
            text = "+" + text + " G"
        label_parts.append((label.center(width), c(250)))
        value_parts.append((text.center(width), c(color) + BOLD))
    lines.append(_row(label_parts))
    lines.append(_row(value_parts))
    lines.append(dots())

    left_w = min(INNER - PORTRAIT_W - 2 - 4, 46)
    lead = max(0, (INNER - left_w - PORTRAIT_W - 2) // 2)
    right_margin = max(0, INNER - lead - left_w - PORTRAIT_W - 2)
    box_left = (left_w - (BUTTON_W + 2)) // 2
    pulse = int(t * 3) % 2
    portrait = portrait_box(title="KNOCKED OUT", art=_defeat_art(t))

    for k in range(11):
        j, kind = divmod(k, 4)
        if kind == 3 or j >= len(DEFEAT_BUTTONS) or t < 1.0 + 0.15 * j:
            left = []
        else:
            text = _defeat_button(j, kind)
            active = j == sel
            style = (c(15) + BOLD if flash else c(196) + BOLD) if active else c(245)
            if active and kind == 1:
                a = box_left - 4 + pulse
                arrow = c(226) + BOLD
                left = [(" " * a, ""), (">>", arrow), (" " * (2 - pulse), ""),
                        (text, style), (" " * (2 - pulse), ""), ("<<", arrow)]
            else:
                left = [(" " * box_left, ""), (text, style)]
        left = _fit(left, left_w)

        if t >= 1.2:
            p = portrait[k]
            edge = c(196)
            if k in (0, len(portrait) - 1):
                right = [(p, edge)]
            else:
                right = [(p[0], edge), (p[1:-1], c(250)), (p[-1], edge)]
        else:
            right = [(" " * (PORTRAIT_W + 2), "")]
        lines.append(_row([(" " * lead, "")] + left + right + [(" " * right_margin, "")]))
    mid_end = len(lines)

    lines += [_row([]), dots()]
    hint = "W/S or UP/DOWN to move   ENTER to select   or press 1 2"
    lines.append(_row([(" " * ((INNER - len(hint)) // 2), ""), (hint, c(245))]))
    lines.append(c(196) + "+" + "=" * INNER + "+" + RESET)

    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        gap_top = extra // 4
        gap_title = extra // 4
        gap_mid = extra - gap_top - gap_title
        lines = (lines[:2] + [blank] * gap_top + lines[2:title_end] + [blank] * gap_title
                 + lines[title_end:mid_end] + [blank] * gap_mid + lines[mid_end:])

    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


def run_defeat_screen(gold, earned, phit, ehit, crits):
    """Show the animated lose screen. Returns 1 = RETRY, 2 = MENU.
    Returns None if the terminal can't animate (the old text screen is used then)."""
    enable_ansi_on_windows()
    if not _can_animate():
        return None
    info = {"gold": gold, "earned": earned, "phit": phit, "ehit": ehit, "crits": crits}
    sel, result = 0, 2
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()

                if key == "up":
                    sel = (sel - 1) % len(DEFEAT_BUTTONS)
                    play_sfx("move")
                elif key == "down":
                    sel = (sel + 1) % len(DEFEAT_BUTTONS)
                    play_sfx("move")
                elif key in ("1", "2"):
                    sel = int(key) - 1
                    play_sfx("move")
                elif key == "quit":
                    result = 2
                    break
                elif key == "enter":
                    result = sel + 1
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_defeat(t + i * 0.05, sel, i % 2 == 0, info))
                        out.flush()
                        time.sleep(0.05)
                    break

                out.write(_render_defeat(t, sel, False, info))
                out.flush()

                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        result = 2
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
    return result


def _static_exit():
    print("+" + "-" * 44 + "+")
    print("|" + "THANK YOU FOR PLAYING!".center(44) + "|")
    print("|" + "SEE YOU NEXT TIME, FIGHTER!".center(44) + "|")
    print("+" + "-" * 44 + "+")
    try:
        input("Press ENTER to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def run_exit_screen():
    enable_ansi_on_windows()
    if not _can_animate():
        _static_exit()
        return
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                t = now - t0
                if _too_small(out):
                    continue
                key = poll_key()
                if key in ("enter", "quit"):
                    play_sfx("select")
                    for i in range(8):
                        out.write(_render_exit(t + i * 0.05, True))
                        out.flush()
                        time.sleep(0.05)
                    break
                out.write(_render_exit(t, False))
                out.flush()
                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        pass
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()


if __name__ == "__main__":
    print("You chose:", run_main_menu(500))