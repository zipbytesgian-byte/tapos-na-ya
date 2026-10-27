from __future__ import annotations

import os
import random
import shutil
import sys
import time
from contextlib import contextmanager

from sound.punch_type_sound import play_sfx   # <-- SOUND: bagong import

W = 78
H = 27
MIN_COLS = W + 2
MIN_ROWS = H + 2
FPS = 30

REASON = ""

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"
CLEAR_EOL = "\x1b[K"
CLEAR_DOWN = "\x1b[J"
FIRE = [196, 202, 208, 214, 220, 226, 220, 214, 208, 202]

ENEMY_NAMES = {1: "STREET THUG", 2: "IRON MIKE", 3: "THE CHAMPION"}
DIFF_NAMES = {1: "EASY", 2: "MEDIUM", 3: "HARD"}
HIT_WORDS = ["CLEAN HIT!", "PERFECT PUNCH!", "NICE!", "WELL TIMED!"]
ESAY = ["AYAAAAAN NAAAA", "NGAWNGAW", "ARAYKUPOOOOO", "MAMAAAAAAA"]
SAY = ["WOOOOOOW!!!!", "UNSTOPPABLE!!!", "UY BAGSAK!!"]


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


if os.name == "nt":
    import msvcrt

    @contextmanager
    def raw_input_mode():
        yield

    def read_key():
        if not msvcrt.kbhit():
            return ""
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
            return ""
        return ch.upper()

    def flush_keys():
        while msvcrt.kbhit():
            msvcrt.getwch()

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

    def read_key():
        if not select.select([sys.stdin], [], [], 0)[0]:
            return ""
        data = os.read(sys.stdin.fileno(), 32).decode(errors="ignore")
        if not data or data[0] == "\x1b":
            return ""
        return data[0].upper()

    def flush_keys():
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass


class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ch = [[" "] * w for _ in range(h)]
        self.st = [[""] * w for _ in range(h)]

    def put(self, x, y, text, style=""):
        if not 0 <= y < self.h:
            return
        for i, ch in enumerate(text):
            if 0 <= x + i < self.w:
                self.ch[y][x + i] = ch
                self.st[y][x + i] = style

    def put_solid(self, x, y, text, style):
        left = len(text) - len(text.lstrip())
        right = len(text.rstrip())
        for i in range(left, right):
            ch = text[i]
            s = style(ch) if callable(style) else style
            self.put(x + i, y, ch, s)

    def lines(self):
        out = []
        for y in range(self.h):
            row = []
            start = 0
            for x in range(1, self.w + 1):
                if x == self.w or self.st[y][x] != self.st[y][start]:
                    text = "".join(self.ch[y][start:x])
                    style = self.st[y][start]
                    row.append(style + text + RESET if style else text)
                    start = x
            out.append("".join(row))
        return out


LEVELS = [(6, 3), (4, 2), (3, 2), (2, 1), (1, 1)]
SX = 1
SY = 1
FLOOR = 15


def scale_art(rows, sx, sy):
    out = []
    for row in rows:
        out += ["".join(ch * sx for ch in row)] * sy
    return out


def set_layout(cols, rows):
    global W, H, SX, SY, FLOOR
    W = cols - 1
    H = rows - 1
    SX, SY = 1, 1
    for sx, sy in LEVELS:
        if ENEMY_W * sx + 16 <= W and 17 * sy <= H - 10:
            SX, SY = sx, sy
            break
    FLOOR = H - 6 - 6 * SY


def _sprite(w, h, parts):
    grid = [[" "] * w for _ in range(h)]
    for x, y, text in parts:
        for i, ch in enumerate(text):
            grid[y][x + i] = ch
    return ["".join(row) for row in grid]


ENEMY_W = 32
ENEMY_H = 11

ENEMY_IDLE = _sprite(ENEMY_W, ENEMY_H, [
    (11, 0, ".---------."),
    (9, 1, "/   ,     ,   \\"),
    (1, 2, ".---."), (8, 2, "|   (O)   (O)   |"), (26, 2, ".---."),
    (0, 3, "(@@@@@)"), (8, 3, "|       >       |"), (25, 3, "(@@@@@)"),
    (0, 4, "(@@@@@)"), (10, 4, "\\    ===    /"), (25, 4, "(@@@@@)"),
    (1, 5, "'---'"), (12, 5, "'-.___.-'"), (26, 5, "'---'"),
    (9, 6, "/|     #     |\\"),
    (8, 7, "/ |     #     | \\"),
    (7, 8, "/  |     #     |  \\"),
    (9, 9, "|_______#_______|"),
    (10, 10, "/ |   | |   | \\"),
])


def _swap_eyes(rows, left, right):
    return [r.replace("(O)", left, 1).replace("(O)", right, 1) for r in rows]


ENEMY_WINDUP = _swap_eyes(ENEMY_IDLE, "(>)", "(<)")
ENEMY_HURT = _swap_eyes(ENEMY_IDLE, "(X)", "(X)")

FIST_BIG = [
    r"   .-~~~~~~-.   ",
    r"  / @@@@@@@@ \  ",
    r" | @@@@@@@@@@ | ",
    r" | @@@@@@@@@@ | ",
    r"  \ @@@@@@@@ /  ",
    r"   '-.____.-'   ",
]

GLOVE_W = 14
GLOVE = [
    r"   .------.   ",
    r"  /  ,--,  \  ",
    r" |  ( () )  | ",
    r" |   '--'   | ",
    r"  \  ====  /  ",
    r"   '------'   ",
]
GLOVE_TOP = {
    2: r"  ^ ^ ^ ^ ^   ",
    3: r"   .--**--.   ",
    4: r"  ~^~^~^~^~   ",
}
GLOVE_COLOR = {1: 196, 2: 252, 3: 214}

ULT_NAMES = {1: "TWIN PUNCH", 2: "BERSERK", 3: "BLOODLUST BANG", 4: "LAVA MULTXXXX"}
ULT_SFX = {1: "ult", 2: "ult_berserk", 3: "ult_bloodlust", 4: "ult_lava"}

def enemy_style(ch):
    return c(196) + BOLD if ch == "@" else c(180)


crowd_cache = {}


def crowd_rows(width):
    if width not in crowd_cache:
        rng = random.Random(7)
        crowd_cache[width] = ["".join(rng.choice("oO.o.") for _ in range(width)) for _ in range(3)]
    return crowd_cache[width]


def _bricks(cv, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        offset = 0 if y % 2 == 0 else 2
        cv.put(x0, y, ("|###" * 20)[offset:offset + (x1 - x0 + 1)], c(238))


def _bg_street(cv, gt):
    bw = 10 + (W - 78) // 4
    _bricks(cv, 1, bw, 3, FLOOR - 1)
    _bricks(cv, W - 1 - bw, W - 2, 3, FLOOR - 1)
    sign_y = 3 + (FLOOR - 3) // 3
    cv.put(2, sign_y, "PUNCH", c(124) + BOLD)
    cv.put(2, sign_y + 1, "TYPE!", c(124) + BOLD)
    lamp_x = bw + 5
    lamp = c(226) + BOLD if int(gt * 7) % 23 else c(94)
    cv.put(lamp_x, 4, ".(*).", lamp)
    for y in range(5, FLOOR):
        cv.put(lamp_x + 2, y, "|", c(240))
    trash_x = W - bw - 15
    cv.put(trash_x, FLOOR - 3, ".-----------.", c(240))
    cv.put(trash_x, FLOOR - 2, "|   TRASH   |", c(240))
    cv.put(trash_x, FLOOR - 1, "'-----------'", c(240))


def _bg_underground(cv, gt):
    cv.put(1, 3, "=" * (W - 2), c(240))
    cv.put(1, 4, "=" * (W - 2), c(238))
    for x in (W * 12 // 78, W - 15):
        for y in range(5, FLOOR):
            cv.put(x, y, "[]", c(240))
    for x in (W * 22 // 78, W - 24):
        cv.put(x, 5, "|", c(240))
        cv.put(x - 1, 6, "(o)", c(226) + BOLD)
    cv.put(W * 32 // 78, 5 + int(gt * 8) % (FLOOR - 6), "'", c(39))


def _bg_ring(cv):
    for i, row in enumerate(crowd_rows(W - 2)):
        cv.put(1, 3 + i, row, c(238 + i))
    for x in (3, W - 6):
        for y in range(6, FLOOR):
            cv.put(x, y, "[#]", c(240))
    for y, color in ((FLOOR - 7, 196), (FLOOR - 5, 255), (FLOOR - 3, 33)):
        cv.put(1, y, "=" * (W - 2), c(color))


def draw_background(cv, map_id, gt):
    cv.put(1, FLOOR, "_" * (W - 2), c(240))
    for y in range(FLOOR + 1, H - 5):
        for x in range(1 + (y % 2) * 2, W - 1, 4):
            cv.put(x, y, ".", c(238))
    if map_id == 2:
        _bg_underground(cv, gt)
    elif map_id == 3:
        _bg_ring(cv)
    else:
        _bg_street(cv, gt)


def hp_bar(cv, x, y, shown, maximum, width=30):
    frac = max(0.0, min(1.0, shown / maximum)) if maximum else 0.0
    fill = int(frac * width + 0.5)
    if shown > 0 and fill == 0:
        fill = 1
    color = 46 if frac > 0.5 else (226 if frac > 0.25 else 196)
    cv.put(x, y, "[", c(250))
    cv.put(x + 1, y, "#" * fill, c(color) + BOLD)
    cv.put(x + 1 + fill, y, "-" * (width - fill), c(240))
    cv.put(x + width + 1, y, "]", c(250))


def number(v):
    return str(int(round(v)))


def hp_text(v, m):
    return f"{max(0, int(v + 0.999))}/{int(m)}"


def current_pose(s, gt):
    phase = s["phase"]
    if phase == "prompt":
        left = s["window"] - (gt - s["t0"])
        return "windup" if left <= s["window"] * 0.35 else "idle"
    if phase == "anim":
        p = (gt - s["t0"]) / s["dur"]
        if s["kind"] == "enemy":
            return "punch"
        return "hurt" if p >= 0.3 else "idle"
    if phase == "end" and s["won"]:
        return "hurt"
    return "idle"


def draw_enemy(cv, s, gt):
    pose = current_pose(s, gt)
    rows = ENEMY_IDLE
    dx = [-1, 0, 1, 0][int(gt * 3) % 4]
    dy = 0
    if pose == "windup":
        rows = ENEMY_WINDUP
        dx = (int(gt * 25) % 3) - 1
    elif pose == "punch":
        rows = ENEMY_WINDUP
        dx, dy = 0, 1
    elif pose == "hurt":
        rows = ENEMY_HURT
        dx = 0 if s["phase"] == "end" else (2 if int(gt * 24) % 2 else -2)
    x0 = (W - ENEMY_W * SX) // 2 + dx * SX
    y0 = FLOOR - ENEMY_H * SY + dy * SY
    for i, row in enumerate(scale_art(rows, SX, SY)):
        cv.put_solid(x0, y0 + i, row, enemy_style)
    if pose == "windup":
        cv.put(x0 + 14 * SX, y0 - 1, "! ! !", c(196) + BOLD)
    elif pose == "hurt":
        cv.put(x0 + 3 * SX, y0 + SY, "*", c(226) + BOLD)
        cv.put(x0 + 28 * SX, y0 + 2 * SY, "*", c(226) + BOLD)
        cv.put(x0 + 14 * SX, y0 - 1, "x x", c(226) + BOLD)
    elif pose == "punch":
        p = (gt - s["t0"]) / s["dur"]
        if p > 0.15:
            fist = scale_art(FIST_BIG, SX, SY)
            fx = (W - len(fist[0])) // 2
            fy = FLOOR - ENEMY_H * SY + 6 * SY
            for i, row in enumerate(fist):
                cv.put_solid(fx, fy + i, row, enemy_style)


def draw_gloves(cv, s, gt, st):
    if st["glove"] == 4:
        style = c(FIRE[int(gt * 8) % len(FIRE)]) + BOLD
    else:
        style = c(GLOVE_COLOR.get(st["glove"], 196)) + BOLD
    art = list(GLOVE)
    if st["glove"] in GLOVE_TOP:
        art[0] = GLOVE_TOP[st["glove"]]
    art = scale_art(art, SX, SY)
    gw = GLOVE_W * SX
    cx = W // 2
    top = FLOOR - ENEMY_H * SY

    pos = {"L": (3, FLOOR + int(gt * 2) % 2), "R": (W - 3 - gw, FLOOR + (int(gt * 2) + 1) % 2)}
    punching = None
    if s["phase"] == "anim" and s["kind"] == "player":
        p = (gt - s["t0"]) / s["dur"]
        if p < 0.4:
            t = p / 0.4
        elif p < 0.6:
            t = 1.0
        else:
            t = max(0.0, 1.0 - (p - 0.6) / 0.4)
        side = s["side"]
        rx, ry = pos[side]
        tx, ty = (cx - gw - 1, top + 2 * SY) if side == "L" else (cx + 1, top + 2 * SY)
        pos[side] = (int(rx + (tx - rx) * t), int(ry + (ty - ry) * t))
        punching = side
        if 0.3 <= p <= 0.75:
            word = "CRIT!" if s["crit"] else "POW!"
            cv.put(cx - 4, top - 1, f"* {word} *", c(226) + BOLD)
            cv.put(cx - 9, top + SY, "\\ | /", c(226))
            cv.put(cx + 7, top + 3 * SY, "* !", c(226))
    elif s["phase"] == "anim" and s["kind"] == "enemy":
        p = (gt - s["t0"]) / s["dur"]
        if 0.2 <= p <= 0.7:
            pos["L"] = (pos["L"][0] - 2 * SX, pos["L"][1])
            pos["R"] = (pos["R"][0] + 2 * SX, pos["R"][1])

    for side in ("L", "R"):
        if side == punching:
            continue
        for i, row in enumerate(art):
            cv.put_solid(pos[side][0], pos[side][1] + i, row, style)
    if punching:
        x, y = pos[punching]
        for i, row in enumerate(art):
            cv.put_solid(x, y + i, row, style)


def centered(cv, y, text, style):
    cv.put((W - len(text)) // 2, y, text, style)


def draw_prompt(cv, s, gt):
    y0 = FLOOR + 2 * SY
    if s["phase"] == "prompt":
        left = max(0.0, s["window"] - (gt - s["t0"]))
        frac = left / s["window"]
        color = 46 if frac > 0.5 else (226 if frac > 0.25 else 196)
        centered(cv, y0, "P R E S S", c(245))
        centered(cv, y0 + 1, f"[ {s['letter']} ]   {left:.1f} sec", c(color) + BOLD)
        width = max(24, min(24 * SX, W - 2 * GLOVE_W * SX - 12))
        fill = int(frac * width + 0.5)
        centered(cv, y0 + 2, "[" + "#" * fill + "-" * (width - fill) + "]", c(color))
    elif gt < s["msg_until"]:
        centered(cv, y0, s["msg"], s["msg_style"])
        if s["msg2"]:
            centered(cv, y0 + 2, s["msg2"], c(250))


def draw_end_box(cv, s, gt):
    won = s["won"]
    color = c(46) + BOLD if won else c(196) + BOLD
    lines = ["+------------------------+",
             "|        K . O .         |",
             "|" + ("YOU WIN!" if won else "YOU LOSE!").center(24) + "|",
             "|" + ("PRESS ENTER" if gt - s["t0"] > 1.0 else "").center(24) + "|",
             "+------------------------+"]
    top = FLOOR - ENEMY_H * SY + 3 * SY
    for i, line in enumerate(lines):
        cv.put((W - len(line)) // 2, top + i, line, color)


def draw_frame(cv, border):
    cv.put(0, 0, "+" + "=" * (W - 2) + "+", border)
    cv.put(0, H - 1, "+" + "=" * (W - 2) + "+", border)
    for y in (2, H - 5):
        cv.put(0, y, "+" + "-" * (W - 2) + "+", c(240))
        cv.put(0, y, "+", border)
        cv.put(W - 1, y, "+", border)
    for y in range(1, H - 1):
        cv.put(0, y, "|", border)
        cv.put(W - 1, y, "|", border)


def render(s, st, gt, size):
    cols, rows = size
    set_layout(cols, rows)
    cv = Canvas(W, H)
    draw_background(cv, st["map"], gt)
    draw_enemy(cv, s, gt)
    draw_gloves(cv, s, gt, st)
    draw_prompt(cv, s, gt)
    if s["phase"] == "end":
        draw_end_box(cv, s, gt)

    bar_w = max(30, W - 48)
    cv.put(2, 1, "ENEMY: " + ENEMY_NAMES.get(st["difficulty"], "ENEMY"), c(15) + BOLD)
    hp_bar(cv, 30, 1, s["shown_e"], st["enemy_max"], bar_w)
    cv.put(33 + bar_w, 1, hp_text(s["shown_e"], st["enemy_max"]), c(250))

    cv.put(2, H - 4, "PLAYER: GEARLESS JOE", c(15) + BOLD)
    hp_bar(cv, 30, H - 4, s["shown_p"], st["player_max"], bar_w)
    cv.put(33 + bar_w, H - 4, hp_text(s["shown_p"], st["player_max"]), c(250))

    status = (f"HITS GAVE: {st['phit']}  HITS TAKEN: {st['ehit']}  WRONG: {s['wrong']}  "
              f"SLOW: {s['slow']}  CRITS: {st['crits']}  LAST: {s['last']}")
    centered(cv, H - 3, status, c(250))
    centered(cv, H - 2, "Press the letter shown before the timer runs out! Wrong key = you get hit.",
             c(240))

    flash = gt < s["flash_until"]
    draw_frame(cv, c(196) + BOLD if flash else c(208))

    diff = DIFF_NAMES.get(st["difficulty"], "")
    cv.put(3, 2, f" {diff}  KEYS: {st['keys']} ", c(245))
    need = st["ult_need"]
    ready = st["ult"] >= need
    meter = "#" * min(st["ult"], need) + "-" * max(0, need - st["ult"])
    cv.put(W - 22, H - 5, f" ULT [{meter}] " + ("READY!" if ready else ""),
           (c(226) + BOLD) if ready else c(245))

    return HOME + (CLEAR_EOL + "\n").join(cv.lines()) + CLEAR_EOL + CLEAR_DOWN


def new_scene(st):
    return {
        "phase": "intro", "t0": 0.0, "until": 0.0, "dur": 0.4, "kind": "", "side": "R",
        "letter": "", "last_letter": "", "window": 2.0, "landed": 0,
        "msg": "GET READY!", "msg_style": c(250) + BOLD, "msg2": "", "msg_until": 99.0,
        "flash_until": 0.0, "wrong": 0, "slow": 0, "last": "-", "crit": False, "won": False,
        "shown_e": float(st["enemy"]), "shown_p": float(st["player"]),
    }


def set_msg(s, gt, text, style, msg2="", seconds=1.2):
    s["msg"] = text
    s["msg_style"] = style
    s["msg2"] = msg2
    s["msg_until"] = gt + seconds


def reaction_window(st, landed):
    base = st["react"]
    return max(base * 0.7, base * (1 - 0.02 * landed))


def start_gap(s, gt):
    s["phase"] = "gap"
    s["until"] = gt + random.uniform(0.5, 0.9)


def start_prompt(s, st, gt):
    pool = [ch for ch in st["keys"] if ch != s["last_letter"]] or list(st["keys"])
    s["letter"] = random.choice(pool)
    s["last_letter"] = s["letter"]
    s["window"] = reaction_window(st, s["landed"])
    s["phase"] = "prompt"
    s["t0"] = gt
    s["msg_until"] = 0.0
    flush_keys()


def do_hit(hooks, s, gt):
    res = hooks["player_hit"]()
    dmg = number(res["damage"])
    s["landed"] += 1
    s["last"] = "-" + dmg
    s["crit"] = res["crit"]
    s["side"] = "L" if s["side"] == "R" else "R"
    s["phase"], s["kind"], s["t0"], s["dur"] = "anim", "player", gt, 0.4
    # ---- SOUND: tunog ng suntok ----
    if res["ult"]:
        play_sfx(ULT_SFX.get(hooks["state"]()["glove"], "ult"))
    elif res["crit"]:
        play_sfx("crit")
    else:
        play_sfx("punch")
    # --------------------------------
    if res["ult"]:
        extra = "+5 HP!" if res["heal"] else random.choice(SAY)
        set_msg(s, gt, f"ULT: {res['ult']}!  -{dmg}", c(201) + BOLD, extra)
    elif res["crit"]:
        set_msg(s, gt, f"CRITICAL HIT!  -{dmg}", c(226) + BOLD)
    else:
        set_msg(s, gt, f"{random.choice(HIT_WORDS)}  -{dmg}", c(46) + BOLD)


def do_miss(hooks, s, gt, reason):
    res = hooks["enemy_hit"]()
    dmg = number(res["damage"])
    if reason == "wrong":
        s["wrong"] += 1
        text = "MISSED!  YOU GOT HIT!"
    else:
        s["slow"] += 1
        text = "TOO SLOW!  YOU GOT HIT!"
    s["last"] = "+" + dmg + " taken"
    s["phase"], s["kind"], s["t0"], s["dur"] = "anim", "enemy", gt, 0.45
    play_sfx("hurt")   # <-- SOUND: natamaan ka
    s["flash_until"] = gt + 0.35
    set_msg(s, gt, f"{text}  -{dmg}", c(196) + BOLD, random.choice(ESAY) if res["enraged"] else "")

def update(hooks, s, gt, key):
    st = hooks["state"]()
    phase = s["phase"]
    if phase == "intro":
        if gt > 0.7:
            if not s.get("bell"):
                s["bell"] = True
                play_sfx("bell")
            set_msg(s, gt, "FIGHT!", c(226) + BOLD, "", 1.0)
        if gt > 1.2:
            start_gap(s, gt)
    elif phase == "gap":
        if gt >= s["until"]:
            start_prompt(s, st, gt)
    elif phase == "prompt":
        left = s["window"] - (gt - s["t0"])
        if 0 < left <= s["window"] * 0.35 and not s.get("ticked"):
            s["ticked"] = True
            play_sfx("tick")
        if left <= 0:
            do_miss(hooks, s, gt, "slow")
        elif len(key) == 1 and key.isalpha():
            if key == s["letter"]:
                do_hit(hooks, s, gt)
            else:
                do_miss(hooks, s, gt, "wrong")
    elif phase == "anim":
        if gt - s["t0"] >= s["dur"]:
            st = hooks["state"]()
            if st["enemy"] <= 0 or st["player"] <= 0:
                s["phase"] = "end"
                s["won"] = st["enemy"] <= 0
                s["t0"] = gt
                play_sfx("ko_win" if s["won"] else "ko_lose")
                flush_keys()
            else:
                if not s.get("roared") and st["enemy"] <= st["enemy_max"] * 0.25:
                    s["roared"] = True
                    play_sfx("roar")
                start_gap(s, gt)
    elif phase == "end":
        if gt - s["t0"] > 1.0 and key in ("\r", "\n"):
            s["phase"] = "done"

def ease_bars(s, st, dt):
    k = min(1.0, dt * 12)
    for name, real in (("shown_e", st["enemy"]), ("shown_p", st["player"])):
        s[name] += (real - s[name]) * k
        if abs(real - s[name]) < 0.5:
            s[name] = float(real)


def too_small(size):
    return size[0] < MIN_COLS or size[1] < MIN_ROWS


def fight_loop(hooks, s, out):
    last = time.monotonic()
    gt = 0.0
    size = None
    while True:
        now = time.monotonic()
        dt = min(now - last, 0.1)
        last = now

        new_size = tuple(shutil.get_terminal_size((MIN_COLS, MIN_ROWS)))
        if new_size != size:
            size = new_size
            out.write(CLEAR)
        if too_small(size):
            out.write(HOME + f"TERMINAL TOO SMALL - NEED {MIN_COLS}x{MIN_ROWS}, "
                      f"YOU HAVE {size[0]}x{size[1]}. FIGHT IS PAUSED." + CLEAR_EOL)
            out.flush()
            flush_keys()
            time.sleep(0.2)
            continue

        gt += dt
        key = read_key()
        if key == "\x03":
            raise KeyboardInterrupt
        update(hooks, s, gt, key)
        if s["phase"] == "done":
            return
        st = hooks["state"]()
        ease_bars(s, st, dt)
        out.write(render(s, st, gt, size))
        out.flush()

        spare = 1.0 / FPS - (time.monotonic() - now)
        if spare > 0:
            time.sleep(spare)


def can_animate():
    global REASON
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        REASON = ("this is not a real terminal. Open Command Prompt / PowerShell / "
                  "Windows Terminal and run:  python punch_type.py")
        return False
    size = shutil.get_terminal_size((MIN_COLS, MIN_ROWS))
    if too_small(size):
        REASON = (f"your terminal is {size.columns}x{size.lines}; the fight needs at least "
                  f"{MIN_COLS}x{MIN_ROWS}. Maximize the window or reduce the font size.")
        return False
    return True


def run_combat(hooks):
    if not can_animate():
        return False
    enable_ansi_on_windows()
    s = new_scene(hooks["state"]())
    out = sys.stdout
    interrupted = False
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    try:
        with raw_input_mode():
            flush_keys()
            fight_loop(hooks, s, out)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()
        flush_keys()
    if interrupted:
        raise SystemExit
    return True
