from __future__ import annotations

import shutil
import sys
import time

import punch_type_menu as m
from sound.punch_type_sound import play_sfx
from punch_type_menu import (
    BOLD, CLEAR, CLEAR_EOL, FIRE, HIDE_CURSOR, HOME, FPS, RESET,
    SHOW_CURSOR, c, enable_ansi_on_windows, poll_key, portrait_art,
    portrait_box, raw_input_mode, _row,
)

HEIGHT = 28

FONT = dict(m.FONT)
FONT.update({
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "Q": [" ### ", "#   #", "# # #", "#  ##", " ####"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
})


def block_text(text):
    return [" ".join(FONT[ch][row] for ch in text) for row in range(5)]


MAPS = [
    ("STREET", 208,
     ["|##| /||\\ |##|", "|##|/ || \\|##|"]),
    ("UNDERGROUND", 245,
     ["==|========|==", "  \\\\  ||  //  "]),
    ("BOXING RING", 196,
     ["+==+==+==+==+", "|  _[__]_   |"]),
]

ITEMS = [
    ("none", "NO GLOVES", 0,
     ["  .--.      .--.  ", " ( () )    ( () ) ", "  '--'      '--'  "], 250),
    ("spiked", "SPIKED GLOVES", 2500,
     [" ^ ^ ^      ^ ^ ^ ", " (@@@@@)    (@@@@@)", "  '---'      '---' "], 252),
    ("bomb", "BOMB GLOVES", 5000,
     ["  .--.   *   .--. ", " (@@@@) (o) (@@@@)", "  '--'       '--' "], 214),
    ("lava", "LAVA GLOVES", 10000,
     ["  ~^~^~     ~^~^~ ", " (@@@@@)   (@@@@@)", "  ~'~'~     ~'~'~ "], 202),
]

DESCRIPTIONS = {
    "none": "NO GLOVES: BASE DAMAGE | TWIN PUNCH ULT: 3 HITS = DOUBLE DAMAGE",
    "spiked": "SPIKED: 20% CRIT RATE | BERSERK ULT: 3 HITS = +250% BASE DAMAGE",
    "bomb": "BOMB: +200% BASE DAMAGE | BLOODLUST BANG ULT: 3 HITS = +500% DAMAGE",
    "lava": "LAVA: +150% DAMAGE, +30% CRIT | MULTXXXXX ULT: 5 HITS = STACKING +30%",
}

LOCK_MSG = [
    "",
    "MAP NOT UNLOCKED YET, DEFEAT THE HARD DIFFICULTY OF THE 1ST MAP",
    "MAP NOT UNLOCKED YET, DEFEAT THE HARD DIFFICULTY OF THE 2ND MAP",
]

_reason = ""


def _header(t, shown, title):
    m._sync_size()
    coin = ["[o]", "[O]", "[0]", "[O]"][int(t * 5) % 4]
    lines = [
        c(208) + "+" + "=" * m.INNER + "+" + RESET,
        _row([("  GOLD: ", c(220) + BOLD), (str(int(round(shown))), c(226) + BOLD),
              (" ", ""), (coin, c(220) + BOLD)]),
        _row([]),
    ]
    rows = block_text(title)
    tw = len(rows[0])
    reveal = min(tw, int(t / 0.7 * tw))
    pad = (m.INNER - tw) // 2
    for r, text in enumerate(rows):
        parts = [(" " * pad, "")]
        for i, ch in enumerate(text):
            if ch == "#" and i < reveal:
                parts.append(("#", c(FIRE[(i // 2 + r - int(t * 12)) % len(FIRE)]) + BOLD))
            else:
                parts.append((" ", ""))
        lines.append(_row(parts))
    lines.append(_row([]))
    return lines


def _stars(t):
    shift = int(t * 10)
    return _row([("*", c(220) + BOLD) if (i + shift) % 4 == 0 else (".", c(240))
                 for i in range(m.INNER)])


def _footer(t, msg, msg_style, hint):
    return [
        _stars(t),
        _row([(msg.center(m.INNER), msg_style)] if msg else []),
        _row([(hint.center(m.INNER), c(245))]),
        c(208) + "+" + "=" * m.INNER + "+" + RESET,
    ]


def _portrait_rows(t, punching):
    return portrait_box(art=portrait_art(t, punching))


def _portrait_parts(box, k):
    p = box[k]
    edge = c(45)
    if k in (0, len(box) - 1):
        return [(p, edge)]
    return [(p[0], edge), (p[1:-1], c(252)), (p[-1], edge)]


def _frame(lines):
    size = m._sync_size()
    extra = size.lines - 1 - len(lines)
    if extra > 0:
        blank = _row([])
        top = extra // 4
        middle = extra // 4
        lines = (lines[:2] + [blank] * top + lines[2:9] + [blank] * middle + lines[9:-4]
                 + [blank] * (extra - top - middle) + lines[-4:])
    return HOME + "".join(l + CLEAR_EOL + "\n" for l in lines)


MAP_W = 44


def _map_cell(j, kind, st, t):
    name, color, scene = MAPS[j]
    locked = not st["unlocked"][j]
    active = j == st["sel"]
    flash = t < st.get("flash_until", 0)
    bs = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(240)
    ls = c(15) + BOLD if active else c(250)
    if locked:
        color = 240
        ls = c(196) + BOLD if active else c(240)
    if kind in (0, 3):
        return [("+" + "=" * (MAP_W - 2) + "+", bs)]
    art = scene[kind - 1].center(16)[:16]
    label = (("LOCKED" if locked else "MAP") if kind == 1 else name).center(25)[:25]
    return [("|", bs), (art, c(color)), ("|", bs), (label, ls), ("|", bs)]


def _render_maps(st, t):
    lines = _header(t, st["shown"], "CHOOSE MAP")
    box = _portrait_rows(t, t < st.get("flash_until", 0))
    pulse = int(t * 3) % 2
    for k in range(15):
        j, kind = divmod(k, 5)
        if kind == 4 or j >= len(MAPS):
            left = [(" " * (3 + MAP_W), "")]
            gap = [("   ", "")]
        else:
            active = j == st["sel"]
            arrow = c(196) + BOLD
            show = active and kind in (1, 2)
            lead = [((">> " if pulse else " >>"), arrow)] if show else [("   ", "")]
            left = lead + _map_cell(j, kind, st, t)
            gap = [(("<< " if pulse else " <<"), arrow)] if show else [("   ", "")]
        pk = k - 1
        right = _portrait_parts(box, pk) if 0 <= pk < len(box) else [(" " * 24, "")]
        lines.append(_row([(" " * max(0, (m.INNER - 74) // 2), "")] + left + gap + right))
    hint = "W/S or UP/DOWN to move   ENTER to select   ESC to go back"
    if t < st.get("msg_until", 0):
        lines += _footer(t, st["msg"], c(196) + BOLD, hint)
    else:
        lines += _footer(t, "", "", hint)
    return _frame(lines)


def _handle_maps(st, key, t):
    if "done_at" in st:
        return
    if key == "up":
        st["sel"] = (st["sel"] - 1) % len(MAPS)
        play_sfx("move")
    elif key == "down":
        st["sel"] = (st["sel"] + 1) % len(MAPS)
        play_sfx("move")
    elif key.isdigit() and key in "123":
        st["sel"] = int(key) - 1
        play_sfx("move")
    elif key == "quit":
        st["result"] = 0
        st["done_at"] = t
        play_sfx("back")
    elif key == "enter":
        if not st["unlocked"][st["sel"]]:
            st["msg"] = LOCK_MSG[st["sel"]]
            st["msg_until"] = t + 2.5
            play_sfx("denied")
        else:
            st["result"] = st["sel"] + 1
            play_sfx("select")
            st["flash_until"] = t + 0.4
            st["done_at"] = t + 0.4


CARD_W = 22


def _card_cell(k, local, st, t):
    gid, label, price, art, base = ITEMS[k]
    active = k == st["sel"]
    flash = t < st.get("flash_until", 0)
    bs = (c(15) + BOLD if flash else c(226) + BOLD) if active else c(240)
    if local in (0, 6):
        return [("+" + "-" * (CARD_W - 2) + "+", bs)]
    if 1 <= local <= 3:
        color = c(FIRE[(int(t * 8) + local + k) % len(FIRE)]) if gid == "lava" else c(base)
        return [("|", bs), (art[local - 1].center(CARD_W - 2)[:CARD_W - 2], color), ("|", bs)]
    if local == 4:
        style = c(15) + BOLD if active else c(250)
        return [("|", bs), (f"[ {label} ]".center(CARD_W - 2)[:CARD_W - 2], style), ("|", bs)]
    if st["equipped"] == gid:
        txt, style = "EQUIPPED", c(46) + BOLD
    elif gid in st["owned"]:
        txt, style = "OWNED", c(51)
    elif st["mode"] == "pick":
        txt, style = "LOCKED", c(196)
    else:
        txt = f"{price} G"
        style = c(226) + BOLD if st["gold"] >= price else c(196)
    return [("|", bs), (txt.center(CARD_W - 2), style), ("|", bs)]


def _render_shop(st, t):
    lines = _header(t, st["shown"], "SHOP" if st["mode"] == "shop" else "EQUIPMENTS")
    box = _portrait_rows(t, t < st.get("flash_until", 0))
    for kr in range(15):
        if kr == 7:
            card_row = None
        else:
            card_row, local = (0, kr) if kr < 7 else (1, kr - 8)
        if card_row is None:
            left = [(" " * (3 + CARD_W * 2 + 2), "")]
        else:
            a, b = card_row * 2, card_row * 2 + 1
            left = ([("   ", "")] + _card_cell(a, local, st, t) + [("  ", "")]
                    + _card_cell(b, local, st, t))
        pk = kr - 1
        right = _portrait_parts(box, pk) if 0 <= pk < len(box) else [(" " * 24, "")]
        lines.append(_row([(" " * max(0, (m.INNER - 76) // 2), "")] + left + [("   ", "")] + right))
    if t < st.get("msg_until", 0):
        msg, msg_style = st["msg"], st.get("msg_style", "")
    else:
        msg, msg_style = DESCRIPTIONS.get(ITEMS[st["sel"]][0], ""), c(250)
    hint = ("W/S or UP/DOWN to move   1-4 jump   ENTER equip   ESC back" if st["mode"] == "pick"
            else "W/S or UP/DOWN to move   1-4 jump   ENTER buy   ESC back")
    lines += _footer(t, msg, msg_style, hint)
    return _frame(lines)


def _try_buy(st, t):
    gid, label, price, _, _ = ITEMS[st["sel"]]
    if st["mode"] == "pick":
        if gid in st["owned"]:
            st["equipped"] = gid
            st["flash_until"] = t + 0.4
            st["done_at"] = t + 0.4
            st["msg"], st["msg_style"] = f"{label} EQUIPPED", c(46) + BOLD
            play_sfx("select")
        else:
            st["msg"], st["msg_style"] = "YOU DONT HAVE THAT YET", c(196) + BOLD
            play_sfx("denied")
    elif gid in st["owned"]:
        st["equipped"] = gid
        play_sfx("select")
        st["msg"], st["msg_style"] = f"{label} EQUIPPED", c(46) + BOLD
    elif st["gold"] >= price:
        st["gold"] -= price
        st["owned"].add(gid)
        play_sfx("buy")
        st["equipped"] = gid
        st["flash_until"] = t + 0.4
        st["msg"], st["msg_style"] = f"PURCHASED {label}!  -{price} GOLD", c(226) + BOLD
    else:
        st["msg"], st["msg_style"] = "NOT ENOUGH GOLD!", c(196) + BOLD
        play_sfx("denied")
    st["msg_until"] = t + 2.0


def _handle_shop(st, key, t):
    if "done_at" in st:
        return
    if key == "up":
        st["sel"] = (st["sel"] - 1) % len(ITEMS)
        play_sfx("move")
    elif key == "down":
        st["sel"] = (st["sel"] + 1) % len(ITEMS)
        play_sfx("move")
    elif key.isdigit() and key in "1234":
        st["sel"] = int(key) - 1
        play_sfx("move")
    elif key == "quit":
        if st["mode"] == "pick":
            st["equipped"] = None
        st["done_at"] = t
        play_sfx("back")
    elif key == "enter":
        _try_buy(st, t)


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

    m._sync_size()
    return True


def _animate(st, render, handle):
    out = sys.stdout
    out.write(HIDE_CURSOR + CLEAR)
    out.flush()
    t0 = last = time.monotonic()
    try:
        with raw_input_mode():
            while True:
                now = time.monotonic()
                dt, last, t = now - last, now, now - t0
                if m._too_small(out, HEIGHT + 2):
                    continue
                handle(st, poll_key(), t)
                if "done_at" in st and t >= st["done_at"]:
                    break
                if st["shown"] != st["gold"]:
                    step = max(60.0, abs(st["shown"] - st["gold"]) / 0.5) * dt
                    if st["shown"] > st["gold"]:
                        st["shown"] = max(float(st["gold"]), st["shown"] - step)
                    else:
                        st["shown"] = min(float(st["gold"]), st["shown"] + step)
                out.write(render(st, t))
                out.flush()
                spare = 1.0 / FPS - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
    except KeyboardInterrupt:
        st.setdefault("result", 0)
    finally:
        out.write(RESET + SHOW_CURSOR + CLEAR + HOME)
        out.flush()


def _static_maps(gold, unlocked):
    print("=== CHOOSE MAP ===    GOLD:", gold)
    for i, (name, _, _) in enumerate(MAPS, 1):
        print(f"  {i}. MAP {name}" + ("" if unlocked[i - 1] else "   [LOCKED]"))
    print(f"(Animation is off: {_reason})")
    while True:
        try:
            n = int(input("ENTER CHOICE (0 = back): "))
        except (ValueError, EOFError):
            return 0
        if not 1 <= n <= len(MAPS):
            return 0
        if unlocked[n - 1]:
            return n
        print(LOCK_MSG[n - 1])


def _static_shop(gold, owned, equipped, mode="shop"):
    print(f"(Animation is off: {_reason})")
    while True:
        print(f"\n=== CHOOSE EQUIPMENTS ===    GOLD: {gold}")
        for i, (gid, label, price, _, _) in enumerate(ITEMS, 1):
            tag = ("EQUIPPED" if gid == equipped else "OWNED" if gid in owned
                   else "LOCKED" if mode == "pick" else f"{price} G")
            print(f"  {i}. {label:<14} {tag}")
        try:
            n = int(input("BUY / EQUIP (0 = back): "))
        except (ValueError, EOFError):
            return equipped, gold, owned
        if n == 0:
            return (None if mode == "pick" else equipped), gold, owned
        if 1 <= n <= len(ITEMS):
            gid, label, price, _, _ = ITEMS[n - 1]
            if mode == "pick":
                if gid in owned:
                    return gid, gold, owned
                print("YOU DONT HAVE THAT YET")
            elif gid in owned:
                equipped = gid
            elif gold >= price:
                gold -= price
                owned.add(gid)
                equipped = gid
                print(f"Purchased {label}!")
            else:
                print("NOT ENOUGH GOLD!")


def run_map_select(gold=0, unlocked=(1, 1, 1)):
    enable_ansi_on_windows()
    unlocked = [bool(u) for u in unlocked] + [True] * len(MAPS)
    unlocked = unlocked[:len(MAPS)]
    if not _can_animate():
        return _static_maps(gold, unlocked)
    st = {"sel": 0, "gold": gold, "shown": float(gold), "result": 0, "unlocked": unlocked}
    _animate(st, _render_maps, _handle_maps)
    return st["result"]


def run_shop(gold=0, owned=None, equipped="none", mode="shop"):
    enable_ansi_on_windows()
    owned = set(owned or ()) | {"none"}
    if not _can_animate():
        return _static_shop(gold, owned, equipped, mode)
    sel = next((i for i, it in enumerate(ITEMS) if it[0] == equipped), 0)
    st = {"sel": sel, "gold": gold, "shown": float(gold), "owned": owned,
          "equipped": equipped, "msg": "", "mode": mode}
    _animate(st, _render_shop, _handle_shop)
    return st["equipped"], st["gold"], st["owned"]


if __name__ == "__main__":
    print("Map:", run_map_select(500))
    print("Shop:", run_shop(500))
