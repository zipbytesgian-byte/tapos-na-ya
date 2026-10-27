ult = 0;
xult = 0;
gold = 0;
pdamage = 20;
pdmg = 30;
import os;
import sys;
import shutil;
import random;
import time;
from punch_type_menu import run_main_menu, run_exit_screen, run_victory_screen, run_defeat_screen;  # CHANGE: run_defeat_screen added
from punch_type_shop import run_map_select, run_shop;
from punch_type_difficulty import run_difficulty_menu, DIFFICULTIES;
import punch_type_combat;
from punch_type_combat import run_combat;
from sound.punch_type_sound import play_music, stop_music, play_sfx

crit = random.randint(1, 100);
player = 100;
7
pult = 1.5;
ehit = 0;
phit = 0;
x = 1;
a = 0;
b = 0;
c = 0;
next = 0;
cheat = 0;
crits = 0;
map2 = 0;
map3 = 0;
choice4 = 0;


def retry():
    global gold;
    global gol;
    global gg;
    global x;
    global player;
    global enemy;
    global ult;
    global pdmg;
    global next;
    global map2;
    global map3;

    if enemy <= 0:
        if choice2 == 1:
            gol = 500;
            gold += 500;

        elif choice2 == 2:
            gol = 800;
            gold += 800;
        elif choice2 == 3:
            gol = 1000;
            gold += 1000;

        note = "";
        if choice2 == 3:
            if choice4 == 1:
                map2 = 1;
                note = "CONGRATULATIONS, YOU'VE UNLOCKED UNDERGROUND MAP";
            elif choice4 == 2:
                map3 = 1;
                note = "CONGRATULATIONS, YOU'VE UNLOCKED BOXING RING MAP";
            elif choice4 == 3:
                note = "CONGRATULATIONS, YOU ARE THE CHAMPION!!!";

        lamon = victory_screen(gol, note);
        match lamon:
            case 1:
                gg = 1;
                player = 100;
                enemy = hp;
                pdmg = 30;

            case 2:
                x = 1;
                gg = 0;
                return;

            case 3:
                exit_screen();
                sys.exit();

    if player <= 0:
        if choice2 == 1:
            gol=150;
            gold += 150;
        elif choice2 == 2:
            gol = 300;
            gold += 300;
        elif choice2 == 3:
            gol = 450;
            gold += 450;
        gold += 50;
        # CHANGE: the plain text lose screen is replaced by the animated one.
        # (Same gold rewards as before; defeat_screen() returns 1 = retry, 2 = menu.)
        ulit = defeat_screen(gol);
        match ulit:
            case 1:
                gg = 1;
                player = 100;
                enemy = hp;
                pdmg = 30;
            case 2:
                x = 1;
                gg = 0;
                return;


def owned_set():
    owned = {"none"};
    if a == 1:
        owned.add("spiked");
    if b == 1:
        owned.add("bomb");
    if c == 1:
        owned.add("lava");
    return owned;


def shop():
    global gold;
    global a;
    global b;
    global c;
    _, gold, owned = run_shop(gold, owned_set(), "none", mode="shop");
    a = 1 if "spiked" in owned else 0;
    b = 1 if "bomb" in owned else 0;
    c = 1 if "lava" in owned else 0;


GLOVE_NUMBER = {"none": 1, "spiked": 2, "bomb": 3, "lava": 4};
DIFFICULTY_STATS = {1: (500, 10), 2: (1000, 25), 3: (1500, 50)};


def prepare_fight():
    global gg;
    global x;
    global choice4;
    global choice6;
    while True:
        picked_map = run_map_select(gold, (1, map2, map3));
        if picked_map == 0:
            return False;
        choice4 = picked_map;
        picked, _, _ = run_shop(gold, owned_set(), "none", mode="pick");
        if picked is not None:
            choice6 = GLOVE_NUMBER[picked];
            gg = 1;
            x = 0;
            return True;


def gamemenu():
    global x;
    global enemy;
    global hp;
    global dmg;
    global edmg;
    global choice2;
    global gg;

    gg = 0;
    if choice1 != 1:
        return;
    while True:
        choice2 = run_difficulty_menu();
        if choice2 not in (1, 2, 3):
            return;
        hp, dmg = DIFFICULTY_STATS[choice2];
        enemy = hp;
        edmg = dmg;
        if prepare_fight():
            return;


def fight_classic():
    global player;
    global enemy;
    global ult;
    global gold;
    global phit;
    global ehit;
    global pdamage;
    global pdmg;
    global crits;

    ult = 0;
    ehit = 0;
    phit = 0
    while player > 0 and enemy > 0 and gg == 1:
        crit = random.randint(1, 100);

        if choice6 == 1:
            pdamage = 20;
            if ult >= 3:
                print("ULT ACTIVATED-TWIN PUNCH");
                pdamage *= 2;

        if choice6 == 2:
            pdamage = 20;
            if crit <= 25:
                pdamage *= 3;
                crits += 1;
            while ult >= 3:
                print("ULT ACTIVATED-BERSERK!!!!!!")
                pdamage *= 2.5;
                ult = 2;

        elif choice6 == 3:
            pdamage = 20 * 2;
            if ult >= 3:
                print("ULTIMATE ACTIVATED-BLOODLUST BANG!")
                pdamage *= 5;
                ult = 0;
                player += 5;

        elif choice6 == 4:
            pdamage = 20 * 1.5;

            if crit <= 30:
                pdamage = pdmg * 3;
                crits += 1;

            while ult >= 5:
                print("ULT ACTIVATED-LAVA MULTXXXX");
                pdmg += 30 * .30;
                phit += 1;
                ult = 4;

        letter = random.choice("QWERTY");
        letter2 = random.choice("QWERTYASDFGH");
        letter3 = random.choice("QWERTYASDFGHZXCVB");
        g = random.choice(["NICE!", "GOOD JOB", "WELL TIMED"]);
        say = random.choice(["WOOOOOOW!!!!", "WHOOOOOOOOHOOOO!!", "UNSTOPPABLE!!!", "UY BAGSAK!!"]);
        esay = random.choice(["AYAAAAAN NAAAA", "NGAWNGAW", "ARAYKUPOOOOO", "MAMAAAAAAA"]);
        print("ENEMY: ", enemy, "| PLAYER: ", player);
        if choice2 == 1:
            dmg = 10;
            print("EASY");
            print(letter);
            start = time.time();
            answer = input().upper();
            end = time.time();
            wrong = end - start;

            if enemy <= hp * 0.25:
                dmg = edmg * 2;

            if wrong <= 3:
                if answer == letter:
                    ult += 1;

                    print(ult);
                    if choice6 == 4:

                        if ult >= 5:

                            if crit <= 30:
                                print("CRITICAL!!!!");
                                print(say, " -", pdamage);
                                enemy -= pdamage;


                            elif crit > 30:

                                enemy -= pdmg;

                                print(say, " -", pdmg);


                        elif ult < 5:
                            if crit <= 30:

                                enemy -= pdamage;
                                print("CRITICAL!!!");
                                print(g, " -", pdamage);
                                phit += 1;
                            else:
                                enemy -= pdamage;
                                print(g, " -", pdamage);
                                phit += 1;


                        else:
                            enemy -= pdamage;
                            print(g, "-", pdamage);

                            phit += 1;
                    else:
                        enemy -= pdamage;
                        if choice6 == 2:
                            if crit <= 25:
                                print("CRITICAL!!!");
                                if ult <= 3:
                                    print(say, " -", pdamage);
                                else:
                                    print(g, " -", pdamage);
                            else:
                                print(g, " -", pdamage);
                        else:
                            print(g, " -", pdamage);

                        phit += 1;


                else:
                    player -= dmg;
                    if enemy <= hp * .25:

                        print(esay, "  -", dmg);
                        ehit += 1;
                    else:
                        print("WROOONG -", dmg);
                        ehit += 1;

                    ult = 0;
                    pdmg = 30;

            else:
                player -= dmg;

                if enemy <= hp * .25:

                    print(esay, "  -", dmg);
                    ehit += 1;
                else:
                    print("TOO SLOW  -", dmg);
                    ehit += 1;
                ult = 0;
                pdmg = 30;
            print("");

        elif choice2 == 2:
            dmg = 25;
            print("MEDIUM")
            print(letter2);
            start = time.time();
            answer = input().upper();
            end = time.time();
            wrong = end - start;
            if enemy <= hp * 0.25:
                dmg = edmg * 2;
            if wrong <= 2:
                if answer == letter2:
                    ult += 1;
                    print(ult);

                    if choice6 == 4:

                        if ult >= 5:
                            if crit <= 30:
                                print("CRITICAL!!!!");

                                print(say, "-", pdamage);
                                enemy -= pdamage;


                            elif crit > 30:

                                enemy -= pdmg;

                                print(say, "-", pdmg);


                        elif ult < 5:
                            if crit <= 30:

                                enemy -= pdamage;
                                print("CRITICAL!!!");
                                print(g, " -", pdamage);
                                phit += 1;
                            else:
                                enemy -= pdamage;
                                print(g, " -", pdamage);
                                phit += 1;


                        else:
                            enemy -= pdamage;
                            print(g, "-", pdamage);

                            phit += 1;
                    else:
                        enemy -= pdamage;
                        if choice6 == 2:
                            if crit <= 25:
                                print("CRITICAL!!!");
                                if ult <= 3:
                                    print(say, " -", pdamage);
                                else:
                                    print(g, " -", pdamage);
                            else:
                                print(g, " -", pdamage);
                        else:
                            print(g, " -", pdamage);

                        phit += 1;


                else:
                    player -= dmg;
                    if enemy <= hp * .25:

                        print(esay, "  -", dmg);
                        ehit += 1;
                    else:
                        print("WROOONG -", dmg);
                        ehit += 1;

                    ult = 0;
                    pdmg = 30;


            else:
                player -= dmg;

                if enemy <= hp * .25:

                    print(esay, "  -", dmg);
                    ehit += 1;
                else:
                    print("TOO SLOW  -", dmg);
                    ehit += 1;
                ult = 0;
                pdmg = 30;
            print("");

        elif choice2 == 3:
            dmg = 50;
            print("HARD");
            print(letter3);
            start = time.time();
            answer = input().upper();
            end = time.time();
            wrong = end - start;

            if enemy <= hp * 0.25:
                dmg = edmg * 2;

            if wrong <= 1.5:
                if answer == letter3:
                    ult += 1;
                    print(ult);
                    print(ult);

                    if choice6 == 4:
                        if ult >= 5:

                            if crit <= 30:
                                print("CRITICAL!!!!");
                                print(say, "-", pdamage);
                                enemy -= pdamage;

                            elif crit > 30:
                                enemy -= pdmg;
                                print(say, "-", pdmg);

                        elif ult < 5:
                            if crit <= 30:
                                enemy -= pdamage;
                                print("CRITICAL!!!");
                                print(g, " -", pdamage);
                                phit += 1;

                            else:
                                enemy -= pdamage;
                                print(g, " -", pdamage);
                                phit += 1;

                        else:
                            enemy -= pdamage;
                            print(g, "-", pdamage);
                            phit += 1;

                    else:
                        enemy -= pdamage;

                        if choice6 == 2:
                            if crit <= 25:
                                print("CRITICAL!!!");

                                if ult <= 3:
                                    print(say, " -", pdamage);

                                else:
                                    print(g, " -", pdamage);

                            else:
                                print(g, " -", pdamage);

                        else:
                            print(g, " -", pdamage);

                        phit += 1;

                else:

                    player -= dmg;

                    if enemy <= hp * .25:
                        print(esay, "  -", dmg);
                        ehit += 1;

                    else:
                        print("WROOONG -", dmg);
                        ehit += 1;

                    ult = 0;
                    pdmg = 30;

            else:

                player -= dmg;

                if enemy <= hp * .25:
                    print(esay, "  -", dmg);
                    ehit += 1;

                else:
                    print("TOO SLOW  -", dmg);
                    ehit += 1;

                ult = 0;
                pdmg = 30;
            print("");


ULT_NEED = {1: 3, 2: 3, 3: 3, 4: 5};
ULT_NAMES = {1: "TWIN PUNCH", 2: "BERSERK", 3: "BLOODLUST BANG", 4: "LAVA MULTXXXX"};


def combat_state():
    d = DIFFICULTIES[choice2 - 1];
    return {"player": player, "player_max": 100, "enemy": enemy, "enemy_max": hp,
            "ult": ult, "ult_need": ULT_NEED[choice6], "phit": phit, "ehit": ehit,
            "crits": crits, "difficulty": choice2, "map": choice4, "glove": choice6,
            "keys": d["keys"], "react": float(d["time"].rstrip("s"))};


def combat_player_hit():
    global ult;
    global enemy;
    global player;
    global phit;
    global pdamage;
    global pdmg;
    global crits;

    crit = random.randint(1, 100);
    crit_hit = False;
    ult_name = "";
    heal = 0;

    if choice6 == 1:
        pdamage = 20;
        if ult >= 3:
            ult_name = ULT_NAMES[1];
            pdamage *= 2;
    elif choice6 == 2:
        pdamage = 20;
        if crit <= 25:
            pdamage *= 3;
            crit_hit = True;
        if ult >= 3:
            ult_name = ULT_NAMES[2];
            pdamage *= 2.5;
            ult = 2;
    elif choice6 == 3:
        pdamage = 20 * 2;
        if ult >= 3:
            ult_name = ULT_NAMES[3];
            pdamage *= 5;
            ult = 0;
            player += 5;
            heal = 5;
    elif choice6 == 4:
        pdamage = 20 * 1.5;
        if crit <= 30:
            pdamage = pdmg * 3;
            crit_hit = True;
        if ult >= 5:
            ult_name = ULT_NAMES[4];
            pdmg += 30 * .30;
            ult = 4;

    ult += 1;
    if choice6 == 4 and ult >= 5 and not crit_hit:
        damage = pdmg;
    else:
        damage = pdamage;
    if crit_hit:
        crits += 1;
    enemy -= damage;
    phit += 1;
    return {"damage": damage, "crit": crit_hit, "ult": ult_name, "heal": heal};


def combat_enemy_hit():
    global player;
    global ehit;
    global ult;
    global pdmg;

    dmg = edmg;
    enraged = enemy <= hp * 0.25;
    if enraged:
        dmg = edmg * 2;
    player -= dmg;
    ehit += 1;
    ult = 0;
    pdmg = 30;
    return {"damage": dmg, "enraged": enraged};


COMBAT_HOOKS = {"state": combat_state, "player_hit": combat_player_hit,
                "enemy_hit": combat_enemy_hit};


def fight():
    global ult;
    global ehit;
    global phit;

    ult = 0;
    ehit = 0;
    phit = 0;
    if not run_combat(COMBAT_HOOKS):
        print("(First-person view is off: " + punch_type_combat.REASON + ")");
        fight_classic();


def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear");


def show_centered(lines, extra=0):
    size = shutil.get_terminal_size((80, 24));
    width = max(len(line) for line in lines);
    left = max(0, (size.columns - width) // 2);
    top = max(0, (size.lines - len(lines) - extra) // 2);
    clear_screen();
    print("\n" * top, end="");
    for line in lines:
        print((" " * left + line)[:size.columns - 1]);
    return left;


def box_row(text, width):
    return "|" + text[:width].center(width) + "|";


def stat_row(label, value, width):
    indent = max(0, (width - 26) // 2);
    text = " " * indent + label.ljust(16) + str(value).rjust(10);
    return "|" + text.ljust(width)[:width] + "|";


def victory_screen(earned, note):
    animated = run_victory_screen(gold, earned, phit, ehit, crits, note);
    if animated is not None:
        return animated;
    trophy = [
        "   .-=======-.   ",
        "  ( |  K.O.  | )  ",
        "   '-.     .-'   ",
        "      |   |      ",
        "     _|___|_     ",
        "    |_______|    ",
    ];
    message = "";
    while True:
        size = shutil.get_terminal_size((80, 24));
        width = max(30, min(52, size.columns - 2));
        border = "+" + "-" * width + "+";
        lines = [border, box_row("Y O U   W I N !", width)];
        if size.lines >= 26:
            lines += [box_row(row.ljust(19), width) for row in trophy];
        lines += [box_row(note, width), border];
        lines += [stat_row("HITS GIVEN", phit, width),
                  stat_row("HITS TAKEN", ehit, width),
                  stat_row("CRITICAL HITS", crits, width),
                  stat_row("GOLD EARNED", "+" + str(earned) + " G", width),
                  border];
        lines += [box_row("1. RETRY", width), box_row("2. MENU", width),
                  box_row("3. EXIT", width), border];
        lines += [box_row(message, width), border];
        left = show_centered(lines, 2);
        try:
            answer = input(" " * left + "ENTER CHOICE: ").strip();
        except (EOFError, KeyboardInterrupt):
            return 3;
        if answer in ("1", "2", "3"):
            return int(answer);
        message = "INVALID CHOICE. TYPE 1, 2 OR 3.";


# CHANGE: NEW FUNCTION. Shows the animated lose screen. If the terminal is
# too small or can't animate, it falls back to the old text version.
def defeat_screen(earned):
    animated = run_defeat_screen(gold, earned, phit, ehit, crits);
    if animated is not None:
        return animated;
    print("YOU LOSE!");
    print("1.RETRY  HITS TAKEN: ", ehit);
    print("2. MENU   HITS GAVE: ", phit);
    print("YOU'VE EARNED ", earned, " GOLD       CRITS: ", crits);
    while True:
        try:
            answer = input("ENTER CHOICE: ").strip();
        except (EOFError, KeyboardInterrupt):
            return 2;
        if answer in ("1", "2"):
            return int(answer);


def exit_screen():
    run_exit_screen();


while x == 1:
    play_music();
    choice1 = run_main_menu(gold);
    if choice1 == 2:
        shop();
    if choice1 == 1:

        gamemenu();
        while gg == 1:
            stop_music();
            print("FIGHT!");
            fight();
            retry();
            while next == 1:
                print("FIGHT!");
                fight2();
                retry2();

    if choice1 == 3:
        stop_music();
        exit_screen();
        break;
    if choice1 == 110:
        play_sfx("cheat");
        print("YOU'VE UNLOCKED ALL GLOVES AND MAPS!")
        a = 1
        b = 1
        c = 1
        map2 = 1
        map3 = 1
        map3 = 1
