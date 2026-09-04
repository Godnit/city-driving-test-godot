extends Node2D

const W = 1280.0
const H = 720.0
const FIELD = Rect2(80, 105, 1120, 510)
const GOAL_TOP = 270.0
const GOAL_BOTTOM = 450.0
const GOAL_DEPTH = 52.0
const PLAYER_R = 31.0
const BALL_R = 16.0
const JOY_CENTER = Vector2(168, 580)
const JOY_R = 78.0
const KICK_CENTER = Vector2(1110, 580)
const KICK_R = 68.0

var state = "menu"
var buttons = {}
var player_pos = Vector2(350, 360)
var player_vel = Vector2.ZERO
var cpu_pos = Vector2(930, 360)
var cpu_vel = Vector2.ZERO
var ball_pos = Vector2(640, 360)
var ball_vel = Vector2.ZERO
var joystick = Vector2.ZERO
var joystick_touch = -1
var mouse_joystick = false
var score_player = 0
var score_cpu = 0
var score_limit = 5
var difficulty = 1
var haptics = true
var aim_assist = true
var match_time = 180.0
var golden_goal = false
var round_freeze = 0.0
var kick_cd = 0.0
var cpu_kick_cd = 0.0
var ai_timer = 0.0
var ai_target = Vector2(900, 360)
var ai_wants_kick = false
var training = false
var last_goal = ""
var banner_timer = 0.0
var wins = 0
var losses = 0
var draws = 0
var goals_for = 0
var goals_against = 0
var smoke_mode = false
var smoke_frames = 0

func _ready():
    _load_data()
    smoke_mode = "--smoke-test" in OS.get_cmdline_user_args()
    if smoke_mode:
        print("CIRCLE_FOOTBALL_READY")
    set_process(true)
    queue_redraw()

func _process(delta):
    if smoke_mode:
        smoke_frames += 1
        if smoke_frames > 3:
            get_tree().quit()
        return
    if state == "game":
        _game_step(delta)
    queue_redraw()

func _game_step(delta):
    kick_cd = max(0.0, kick_cd - delta)
    cpu_kick_cd = max(0.0, cpu_kick_cd - delta)
    banner_timer = max(0.0, banner_timer - delta)
    if round_freeze > 0.0:
        round_freeze -= delta
        if round_freeze <= 0.0:
            _reset_positions(last_goal == "PLAYER")
        return

    if not training:
        if not golden_goal:
            match_time = max(0.0, match_time - delta)
            if match_time <= 0.0:
                if score_player == score_cpu:
                    golden_goal = true
                    banner_timer = 2.4
                    last_goal = "GOLDEN GOAL"
                else:
                    _finish_match()
                    return
        _update_ai(delta)
    else:
        cpu_vel = cpu_vel.move_toward(Vector2.ZERO, 1000.0 * delta)

    var desired = joystick * 355.0
    player_vel = player_vel.move_toward(desired, 1050.0 * delta)
    if joystick.length() < 0.05:
        player_vel *= pow(0.001, delta)

    player_pos += player_vel * delta
    if not training:
        cpu_pos += cpu_vel * delta
    ball_pos += ball_vel * delta
    ball_vel *= pow(0.23, delta)
    if ball_vel.length() < 2.0:
        ball_vel = Vector2.ZERO

    _clamp_player(player_pos, true)
    player_pos = _clamped_actor(player_pos)
    if not training:
        cpu_pos = _clamped_actor(cpu_pos)

    _resolve_actor_collision()
    _actor_ball_collision(player_pos, player_vel, 1.0)
    if not training:
        _actor_ball_collision(cpu_pos, cpu_vel, 0.95)

    _ball_walls_and_goals()

    if ai_wants_kick and not training and cpu_kick_cd <= 0.0 and cpu_pos.distance_to(ball_pos) < PLAYER_R + BALL_R + 20.0:
        _cpu_kick()

func _clamp_player(_p, _is_player):
    pass

func _clamped_actor(p):
    return Vector2(clamp(p.x, FIELD.position.x + PLAYER_R, FIELD.end.x - PLAYER_R), clamp(p.y, FIELD.position.y + PLAYER_R, FIELD.end.y - PLAYER_R))

func _resolve_actor_collision():
    if training:
        return
    var d = cpu_pos - player_pos
    var dist = d.length()
    var min_dist = PLAYER_R * 2.0
    if dist > 0.001 and dist < min_dist:
        var n = d / dist
        var push = (min_dist - dist) * 0.5
        player_pos -= n * push
        cpu_pos += n * push
        var rel = (cpu_vel - player_vel).dot(n)
        if rel < 0.0:
            var impulse = -rel * 0.45
            player_vel -= n * impulse
            cpu_vel += n * impulse

func _actor_ball_collision(actor_pos, actor_vel, power):
    var d = ball_pos - actor_pos
    var dist = d.length()
    var min_dist = PLAYER_R + BALL_R
    if dist > 0.001 and dist < min_dist:
        var n = d / dist
        ball_pos = actor_pos + n * min_dist
        var toward = actor_vel.dot(n)
        var rel = (ball_vel - actor_vel).dot(n)
        if rel < 0.0:
            ball_vel -= n * rel * 1.28
        if toward > 0.0:
            ball_vel += n * toward * 0.62 * power
        ball_vel = ball_vel.limit_length(980.0)

func _ball_walls_and_goals():
    var left = FIELD.position.x
    var right = FIELD.end.x
    var top = FIELD.position.y
    var bottom = FIELD.end.y

    if ball_pos.y - BALL_R < top:
        ball_pos.y = top + BALL_R
        ball_vel.y = abs(ball_vel.y) * 0.78
    elif ball_pos.y + BALL_R > bottom:
        ball_pos.y = bottom - BALL_R
        ball_vel.y = -abs(ball_vel.y) * 0.78

    var in_goal_mouth = ball_pos.y > GOAL_TOP + BALL_R * 0.25 and ball_pos.y < GOAL_BOTTOM - BALL_R * 0.25

    if ball_pos.x - BALL_R < left:
        if in_goal_mouth:
            if ball_pos.x < left - GOAL_DEPTH:
                _goal("CPU")
        else:
            ball_pos.x = left + BALL_R
            ball_vel.x = abs(ball_vel.x) * 0.78
    elif ball_pos.x + BALL_R > right:
        if in_goal_mouth:
            if ball_pos.x > right + GOAL_DEPTH:
                _goal("PLAYER")
        else:
            ball_pos.x = right - BALL_R
            ball_vel.x = -abs(ball_vel.x) * 0.78

    if in_goal_mouth:
        if ball_pos.x < left:
            if ball_pos.y - BALL_R < GOAL_TOP:
                ball_pos.y = GOAL_TOP + BALL_R
                ball_vel.y = abs(ball_vel.y) * 0.72
            elif ball_pos.y + BALL_R > GOAL_BOTTOM:
                ball_pos.y = GOAL_BOTTOM - BALL_R
                ball_vel.y = -abs(ball_vel.y) * 0.72
        elif ball_pos.x > right:
            if ball_pos.y - BALL_R < GOAL_TOP:
                ball_pos.y = GOAL_TOP + BALL_R
                ball_vel.y = abs(ball_vel.y) * 0.72
            elif ball_pos.y + BALL_R > GOAL_BOTTOM:
                ball_pos.y = GOAL_BOTTOM - BALL_R
                ball_vel.y = -abs(ball_vel.y) * 0.72

func _goal(who):
    if training:
        banner_timer = 1.2
        last_goal = "GOAL"
        round_freeze = 0.75
        return
    if who == "PLAYER":
        score_player += 1
        goals_for += 1
        last_goal = "GOAL!"
        _buzz(35)
    else:
        score_cpu += 1
        goals_against += 1
        last_goal = "CPU SCORES"
        _buzz(70)
    banner_timer = 1.6
    _save_data()
    if golden_goal or score_player >= score_limit or score_cpu >= score_limit:
        round_freeze = 0.8
        return
    round_freeze = 1.05

func _reset_positions(player_scored=false):
    if not training and (golden_goal or score_player >= score_limit or score_cpu >= score_limit):
        _finish_match()
        return
    player_pos = Vector2(350, 360)
    cpu_pos = Vector2(930, 360)
    player_vel = Vector2.ZERO
    cpu_vel = Vector2.ZERO
    ball_vel = Vector2.ZERO
    if training:
        ball_pos = Vector2(650, 360)
    else:
        ball_pos = Vector2(640, 360)
        if player_scored:
            ball_pos.x = 700
        else:
            ball_pos.x = 580

func _finish_match():
    if score_player > score_cpu:
        wins += 1
    elif score_cpu > score_player:
        losses += 1
    else:
        draws += 1
    _save_data()
    joystick = Vector2.ZERO
    joystick_touch = -1
    state = "result"

func _start_match(is_training=false):
    training = is_training
    score_player = 0
    score_cpu = 0
    match_time = 180.0
    golden_goal = false
    round_freeze = 0.0
    last_goal = ""
    banner_timer = 0.0
    state = "game"
    _reset_positions(false)

func _update_ai(delta):
    ai_timer -= delta
    if ai_timer <= 0.0:
        var reaction = [0.22, 0.11, 0.055][difficulty]
        ai_timer = reaction
        var lookahead = [0.14, 0.28, 0.42][difficulty]
        var predicted = ball_pos + ball_vel * lookahead
        predicted.y = clamp(predicted.y, FIELD.position.y + 42.0, FIELD.end.y - 42.0)
        predicted.x = clamp(predicted.x, FIELD.position.x + 40.0, FIELD.end.x - 40.0)
        var own_goal = Vector2(FIELD.end.x, 360)
        var opp_goal = Vector2(FIELD.position.x, 360)
        var ball_on_danger_side = predicted.x > 760.0
        var ball_heading_home = ball_vel.x > 90.0 and ball_pos.x > 610.0

        if ball_heading_home:
            var t = max(0.0, (FIELD.end.x - 110.0 - ball_pos.x) / max(80.0, ball_vel.x))
            var intercept_y = clamp(ball_pos.y + ball_vel.y * t, GOAL_TOP + 28.0, GOAL_BOTTOM - 28.0)
            ai_target = Vector2(FIELD.end.x - 115.0, intercept_y)
        elif ball_on_danger_side:
            var from_goal = (predicted - own_goal).normalized()
            ai_target = predicted + from_goal * 48.0
        else:
            var attack_line = (predicted - opp_goal).normalized()
            ai_target = predicted + attack_line * 38.0

        if ball_pos.x < 410.0 and ball_vel.length() < 130.0:
            ai_target = Vector2(780.0, clamp(ball_pos.y, 250.0, 470.0))

        ai_wants_kick = cpu_pos.distance_to(ball_pos) < PLAYER_R + BALL_R + 24.0

    var speed_mult = [0.82, 0.98, 1.10][difficulty]
    var dir = (ai_target - cpu_pos)
    if dir.length() > 7.0:
        dir = dir.normalized()
    else:
        dir = Vector2.ZERO
    var desired = dir * 338.0 * speed_mult
    cpu_vel = cpu_vel.move_toward(desired, (780.0 + difficulty * 160.0) * delta)
    if dir == Vector2.ZERO:
        cpu_vel *= pow(0.004, delta)

func _cpu_kick():
    var target = Vector2(FIELD.position.x - GOAL_DEPTH, 360.0)
    var error = [0.28, 0.12, 0.045][difficulty]
    var seed = sin(Time.get_ticks_msec() * 0.0017 + score_cpu * 2.31 + score_player)
    target.y += seed * error * 420.0
    var dir = (target - ball_pos).normalized()
    ball_vel += dir * (620.0 + difficulty * 70.0)
    ball_vel += cpu_vel * 0.35
    ball_vel = ball_vel.limit_length(1050.0)
    cpu_kick_cd = [0.75, 0.52, 0.38][difficulty]

func _player_kick():
    if state != "game" or kick_cd > 0.0 or round_freeze > 0.0:
        return
    if player_pos.distance_to(ball_pos) > PLAYER_R + BALL_R + 28.0:
        kick_cd = 0.15
        return
    var dir = (ball_pos - player_pos).normalized()
    if aim_assist:
        var goal_dir = (Vector2(FIELD.end.x + GOAL_DEPTH, 360) - ball_pos).normalized()
        if joystick.length() < 0.35:
            dir = dir.lerp(goal_dir, 0.48).normalized()
        elif dir.dot(goal_dir) > 0.25:
            dir = dir.lerp(goal_dir, 0.18).normalized()
    ball_vel += dir * 720.0 + player_vel * 0.42
    ball_vel = ball_vel.limit_length(1080.0)
    kick_cd = 0.42
    _buzz(18)

func _buzz(ms):
    if haptics:
        Input.vibrate_handheld(ms)

func _input(event):
    if event is InputEventScreenTouch:
        if event.pressed:
            _touch_down(event.index, event.position)
        else:
            _touch_up(event.index, event.position)
    elif event is InputEventScreenDrag:
        if event.index == joystick_touch:
            _update_joystick(event.position)
    elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            if state == "game" and event.position.distance_to(JOY_CENTER) < JOY_R * 1.45:
                mouse_joystick = true
                _update_joystick(event.position)
            else:
                _tap(event.position)
        else:
            if mouse_joystick:
                mouse_joystick = false
                joystick = Vector2.ZERO
    elif event is InputEventMouseMotion and mouse_joystick:
        _update_joystick(event.position)
    elif event is InputEventKey and event.pressed:
        if state == "game":
            if event.keycode == KEY_SPACE:
                _player_kick()
            elif event.keycode == KEY_ESCAPE:
                state = "pause"
        elif event.keycode == KEY_ESCAPE and state != "menu":
            state = "menu"

func _touch_down(index, pos):
    if state == "game":
        if pos.x < 430.0 and pos.y > 410.0 and joystick_touch == -1:
            joystick_touch = index
            _update_joystick(pos)
            return
        if pos.distance_to(KICK_CENTER) < KICK_R * 1.35:
            _player_kick()
            return
        if Rect2(1180, 18, 72, 58).has_point(pos):
            state = "pause"
            joystick = Vector2.ZERO
            joystick_touch = -1
            return
    return

func _touch_up(index, pos):
    if index == joystick_touch:
        joystick_touch = -1
        joystick = Vector2.ZERO
    if state != "game":
        _tap(pos)

func _update_joystick(pos):
    var d = pos - JOY_CENTER
    joystick = d / JOY_R
    if joystick.length() > 1.0:
        joystick = joystick.normalized()

func _tap(pos):
    for key in buttons.keys():
        var r = buttons[key]
        if r.has_point(pos):
            _activate(key)
            return

func _activate(key):
    match key:
        "play":
            state = "setup"
        "training":
            _start_match(true)
        "settings":
            state = "settings"
        "help":
            state = "help"
        "stats":
            state = "stats"
        "back":
            state = "menu"
        "start":
            _start_match(false)
        "diff_easy":
            difficulty = 0
            _save_data()
        "diff_normal":
            difficulty = 1
            _save_data()
        "diff_hard":
            difficulty = 2
            _save_data()
        "score3":
            score_limit = 3
            _save_data()
        "score5":
            score_limit = 5
            _save_data()
        "score7":
            score_limit = 7
            _save_data()
        "haptics":
            haptics = not haptics
            _save_data()
        "assist":
            aim_assist = not aim_assist
            _save_data()
        "resume":
            state = "game"
        "restart":
            _start_match(training)
        "quit_match":
            state = "menu"
            joystick = Vector2.ZERO
        "again":
            _start_match(false)
        "result_menu":
            state = "menu"

func _draw():
    buttons.clear()
    _draw_background()
    match state:
        "menu":
            _draw_menu()
        "setup":
            _draw_setup()
        "settings":
            _draw_settings()
        "help":
            _draw_help()
        "stats":
            _draw_stats()
        "game":
            _draw_game()
        "pause":
            _draw_game()
            _draw_pause()
        "result":
            _draw_result()

func _draw_background():
    draw_rect(Rect2(0, 0, W, H), Color("0b1220"))
    for i in range(9):
        var y = 50.0 + i * 82.0
        draw_line(Vector2(0, y), Vector2(W, y), Color(1,1,1,0.025), 1.0)
    for i in range(13):
        var x = 34.0 + i * 104.0
        draw_line(Vector2(x, 0), Vector2(x, H), Color(1,1,1,0.018), 1.0)

func _draw_header(title, subtitle=""):
    _text(title, Vector2(64, 78), 40, Color("f7f9fc"))
    if subtitle != "":
        _text(subtitle, Vector2(66, 108), 18, Color("8fa3bd"))

func _draw_menu():
    draw_circle(Vector2(176, 165), 54, Color("2867ff"))
    draw_circle(Vector2(255, 165), 23, Color("f5d84d"))
    draw_circle(Vector2(334, 165), 54, Color("ff4141"))
    _text("CIRCLE FOOTBALL", Vector2(420, 160), 50, Color("ffffff"))
    _text("OFFLINE • VS CPU", Vector2(424, 198), 21, Color("8fa3bd"))
    _button("play", Rect2(390, 270, 500, 72), "PLAY VS CPU", true)
    _button("training", Rect2(390, 356, 242, 66), "TRAINING")
    _button("settings", Rect2(648, 356, 242, 66), "SETTINGS")
    _button("stats", Rect2(390, 438, 242, 66), "STATS")
    _button("help", Rect2(648, 438, 242, 66), "HOW TO PLAY")
    _text("Fast offline physics • smart CPU • no internet required", Vector2(384, 570), 19, Color("71839d"))
    _text("v1.0", Vector2(1190, 682), 16, Color("53657c"))

func _draw_setup():
    _draw_header("MATCH SETUP", "Choose difficulty and winning score")
    _text("CPU DIFFICULTY", Vector2(160, 185), 22, Color("a9bad0"))
    _option_button("diff_easy", Rect2(160, 215, 250, 72), "EASY", difficulty == 0)
    _option_button("diff_normal", Rect2(430, 215, 250, 72), "NORMAL", difficulty == 1)
    _option_button("diff_hard", Rect2(700, 215, 250, 72), "HARD", difficulty == 2)
    _text("FIRST TO", Vector2(160, 350), 22, Color("a9bad0"))
    _option_button("score3", Rect2(160, 380, 210, 72), "3 GOALS", score_limit == 3)
    _option_button("score5", Rect2(390, 380, 210, 72), "5 GOALS", score_limit == 5)
    _option_button("score7", Rect2(620, 380, 210, 72), "7 GOALS", score_limit == 7)
    _button("start", Rect2(850, 360, 270, 92), "START MATCH", true)
    _button("back", Rect2(64, 625, 180, 58), "BACK")
    _text("Match time: 3:00 • Tie = Golden Goal", Vector2(160, 520), 20, Color("71839d"))

func _draw_settings():
    _draw_header("SETTINGS", "Your choices are saved automatically")
    _toggle_row("haptics", 190, "HAPTIC FEEDBACK", "Short vibration for kicks and goals", haptics)
    _toggle_row("assist", 295, "AIM ASSIST", "Small help toward the opponent goal", aim_assist)
    _text("DEFAULT CPU", Vector2(160, 430), 21, Color("a9bad0"))
    _option_button("diff_easy", Rect2(160, 460, 210, 64), "EASY", difficulty == 0)
    _option_button("diff_normal", Rect2(390, 460, 210, 64), "NORMAL", difficulty == 1)
    _option_button("diff_hard", Rect2(620, 460, 210, 64), "HARD", difficulty == 2)
    _button("back", Rect2(64, 625, 180, 58), "BACK")

func _draw_help():
    _draw_header("HOW TO PLAY", "Simple controls, deep positioning")
    _help_card(Rect2(105, 170, 500, 150), "MOVE", "Use the left joystick to move your blue player.\nRelease it to brake quickly.", "1")
    _help_card(Rect2(675, 170, 500, 150), "KICK", "Tap the yellow KICK button when you are close\nto the ball. Direction follows your approach.", "2")
    _help_card(Rect2(105, 350, 500, 150), "DEFEND", "Stay between the ball and your goal. Use walls\nand rebounds instead of chasing every touch.", "3")
    _help_card(Rect2(675, 350, 500, 150), "WIN", "Reach the goal limit first, or lead when 3:00 ends.\nA tie goes to Golden Goal.", "4")
    _button("back", Rect2(64, 625, 180, 58), "BACK")

func _draw_stats():
    _draw_header("CAREER STATS", "Offline results saved on this device")
    var total = wins + losses + draws
    _stat_card(Rect2(130, 180, 260, 130), "MATCHES", str(total), Color("9db3ce"))
    _stat_card(Rect2(410, 180, 260, 130), "WINS", str(wins), Color("4dd88a"))
    _stat_card(Rect2(690, 180, 260, 130), "LOSSES", str(losses), Color("ff6666"))
    _stat_card(Rect2(970, 180, 180, 130), "DRAWS", str(draws), Color("f0cf55"))
    _stat_card(Rect2(270, 355, 330, 130), "GOALS FOR", str(goals_for), Color("5f8cff"))
    _stat_card(Rect2(680, 355, 330, 130), "GOALS AGAINST", str(goals_against), Color("ff5d5d"))
    var rate = 0
    if total > 0:
        rate = int(round(float(wins) / float(total) * 100.0))
    _text("Win rate: " + str(rate) + "%", Vector2(548, 555), 23, Color("a9bad0"), true)
    _button("back", Rect2(64, 625, 180, 58), "BACK")

func _draw_game():
    draw_rect(Rect2(FIELD.position.x - GOAL_DEPTH, GOAL_TOP, GOAL_DEPTH, GOAL_BOTTOM - GOAL_TOP), Color(0.157, 0.404, 1.0, 0.20))
    draw_rect(Rect2(FIELD.end.x, GOAL_TOP, GOAL_DEPTH, GOAL_BOTTOM - GOAL_TOP), Color(1.0, 0.255, 0.255, 0.20))
    draw_rect(FIELD, Color("48515b"))
    for i in range(7):
        var yy = FIELD.position.y + 18 + i * 76
        draw_line(Vector2(FIELD.position.x, yy), Vector2(FIELD.end.x, yy), Color(1,1,1,0.035), 1.0)
    draw_rect(FIELD, Color("e8edf4"), false, 4.0)
    draw_line(Vector2(640, FIELD.position.y), Vector2(640, FIELD.end.y), Color("e8edf4"), 3.0)
    draw_arc(Vector2(640, 360), 82, 0, TAU, 64, Color("e8edf4"), 3.0)
    draw_circle(Vector2(640, 360), 6, Color("e8edf4"))
    draw_line(Vector2(FIELD.position.x, GOAL_TOP), Vector2(FIELD.position.x, GOAL_BOTTOM), Color("e8edf4"), 4.0)
    draw_line(Vector2(FIELD.end.x, GOAL_TOP), Vector2(FIELD.end.x, GOAL_BOTTOM), Color("e8edf4"), 4.0)

    draw_circle(player_pos + Vector2(0,5), PLAYER_R + 2, Color(0,0,0,0.22))
    draw_circle(player_pos, PLAYER_R, Color("2867ff"))
    draw_arc(player_pos, PLAYER_R, 0, TAU, 36, Color("0b1020"), 5.0)
    _text("YOU", player_pos + Vector2(0, 6), 15, Color("ffffff"), true)

    if not training:
        draw_circle(cpu_pos + Vector2(0,5), PLAYER_R + 2, Color(0,0,0,0.22))
        draw_circle(cpu_pos, PLAYER_R, Color("ff4141"))
        draw_arc(cpu_pos, PLAYER_R, 0, TAU, 36, Color("0b1020"), 5.0)
        _text("CPU", cpu_pos + Vector2(0, 6), 15, Color("ffffff"), true)

    draw_circle(ball_pos + Vector2(0,4), BALL_R + 2, Color(0,0,0,0.25))
    draw_circle(ball_pos, BALL_R, Color("f4d94f"))
    draw_arc(ball_pos, BALL_R, 0, TAU, 28, Color("20242b"), 3.0)

    _draw_hud()
    _draw_controls()

    if banner_timer > 0.0:
        draw_rect(Rect2(400, 305, 480, 110), Color(0.04,0.07,0.12,0.92))
        _text(last_goal, Vector2(640, 373), 38, Color("ffffff"), true)

func _draw_hud():
    draw_rect(Rect2(410, 16, 460, 72), Color(0.04,0.07,0.12,0.90))
    if training:
        _text("TRAINING", Vector2(640, 60), 26, Color("f4d94f"), true)
        _text("Reset positions after each goal", Vector2(640, 82), 14, Color("8fa3bd"), true)
    else:
        _text(str(score_player), Vector2(520, 65), 36, Color("5f8cff"), true)
        _text("-", Vector2(640, 61), 32, Color("d8e0ea"), true)
        _text(str(score_cpu), Vector2(760, 65), 36, Color("ff6666"), true)
        var time_text = _time_string(match_time)
        if golden_goal:
            time_text = "GOLDEN GOAL"
        _text(time_text, Vector2(640, 86), 16, Color("a9bad0"), true)
    draw_rect(Rect2(1180, 18, 72, 58), Color("182434"))
    _text("II", Vector2(1216, 56), 24, Color("ffffff"), true)

func _draw_controls():
    draw_circle(JOY_CENTER, JOY_R, Color(0.05,0.08,0.13,0.50))
    draw_arc(JOY_CENTER, JOY_R, 0, TAU, 48, Color(1,1,1,0.22), 3.0)
    var knob = JOY_CENTER + joystick * 45.0
    draw_circle(knob, 32, Color(0.72,0.79,0.88,0.55))
    draw_circle(KICK_CENTER, KICK_R, Color(0.827, 0.725, 0.220, 0.88))
    draw_arc(KICK_CENTER, KICK_R, 0, TAU, 48, Color("fff3a2"), 3.0)
    _text("KICK", KICK_CENTER + Vector2(0, 8), 22, Color("16191f"), true)
    if kick_cd > 0.0:
        draw_arc(KICK_CENTER, KICK_R - 8, -PI/2, -PI/2 + TAU * clamp(kick_cd / 0.42, 0, 1), 32, Color(0,0,0,0.45), 7.0)

func _draw_pause():
    draw_rect(Rect2(0,0,W,H), Color(0,0,0,0.62))
    draw_rect(Rect2(380, 150, 520, 420), Color("111b29"))
    _text("PAUSED", Vector2(640, 225), 42, Color("ffffff"), true)
    _button("resume", Rect2(470, 285, 340, 68), "RESUME", true)
    _button("restart", Rect2(470, 370, 340, 62), "RESTART")
    _button("quit_match", Rect2(470, 448, 340, 62), "MAIN MENU")

func _draw_result():
    _draw_header("MATCH COMPLETE", "Offline result")
    var won = score_player > score_cpu
    var title = "YOU WIN!" if won else "CPU WINS"
    var col = Color("4dd88a") if won else Color("ff6666")
    _text(title, Vector2(640, 220), 52, col, true)
    _text(str(score_player) + "  -  " + str(score_cpu), Vector2(640, 310), 64, Color("ffffff"), true)
    _text("First to " + str(score_limit) + " • " + ["Easy", "Normal", "Hard"][difficulty] + " CPU", Vector2(640, 360), 20, Color("8fa3bd"), true)
    _button("again", Rect2(390, 430, 500, 72), "PLAY AGAIN", true)
    _button("result_menu", Rect2(470, 520, 340, 62), "MAIN MENU")

func _button(key, rect, label, primary=false):
    buttons[key] = rect
    var fill = Color("2867ff") if primary else Color("182434")
    draw_rect(rect, fill)
    draw_rect(rect, Color(1,1,1,0.08), false, 2.0)
    _text(label, rect.position + Vector2(rect.size.x/2, rect.size.y/2 + 8), 22, Color("ffffff"), true)

func _option_button(key, rect, label, selected):
    buttons[key] = rect
    var fill = Color("274a78") if selected else Color("172231")
    draw_rect(rect, fill)
    draw_rect(rect, Color("5f8cff") if selected else Color(1,1,1,0.08), false, 3.0 if selected else 2.0)
    _text(label, rect.position + Vector2(rect.size.x/2, rect.size.y/2 + 8), 21, Color("ffffff"), true)

func _toggle_row(key, y, title, desc, value):
    var rect = Rect2(160, y, 960, 82)
    buttons[key] = rect
    draw_rect(rect, Color("15202e"))
    _text(title, Vector2(190, y + 32), 22, Color("ffffff"))
    _text(desc, Vector2(190, y + 59), 16, Color("8396ae"))
    var track = Rect2(990, y + 22, 92, 40)
    draw_rect(track, Color("2867ff") if value else Color("3a4656"))
    draw_circle(Vector2(1060 if value else 1012, y + 42), 15, Color("ffffff"))

func _help_card(rect, title, body, num):
    draw_rect(rect, Color("15202e"))
    draw_circle(rect.position + Vector2(55, 54), 28, Color("2867ff"))
    _text(num, rect.position + Vector2(55, 62), 20, Color("ffffff"), true)
    _text(title, rect.position + Vector2(100, 48), 22, Color("ffffff"))
    var lines = body.split("\n")
    for i in range(lines.size()):
        _text(lines[i], rect.position + Vector2(100, 83 + i*24), 16, Color("8fa3bd"))

func _stat_card(rect, label, value, col):
    draw_rect(rect, Color("15202e"))
    _text(label, rect.position + Vector2(rect.size.x/2, 40), 17, Color("8fa3bd"), true)
    _text(value, rect.position + Vector2(rect.size.x/2, 92), 38, col, true)

func _text(s, pos, size, color, centered=false):
    var font = ThemeDB.fallback_font
    var p = pos
    if centered:
        var tw = font.get_string_size(str(s), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
        p.x -= tw * 0.5
    draw_string(font, p, str(s), HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _time_string(seconds):
    var total = int(ceil(seconds))
    var m = int(total / 60)
    var s = total % 60
    return "%d:%02d" % [m, s]

func _load_data():
    var cfg = ConfigFile.new()
    if cfg.load("user://circle_football.cfg") == OK:
        difficulty = int(cfg.get_value("settings", "difficulty", 1))
        score_limit = int(cfg.get_value("settings", "score_limit", 5))
        haptics = bool(cfg.get_value("settings", "haptics", true))
        aim_assist = bool(cfg.get_value("settings", "aim_assist", true))
        wins = int(cfg.get_value("stats", "wins", 0))
        losses = int(cfg.get_value("stats", "losses", 0))
        draws = int(cfg.get_value("stats", "draws", 0))
        goals_for = int(cfg.get_value("stats", "goals_for", 0))
        goals_against = int(cfg.get_value("stats", "goals_against", 0))
    difficulty = clamp(difficulty, 0, 2)
    if score_limit not in [3,5,7]:
        score_limit = 5

func _save_data():
    var cfg = ConfigFile.new()
    cfg.set_value("settings", "difficulty", difficulty)
    cfg.set_value("settings", "score_limit", score_limit)
    cfg.set_value("settings", "haptics", haptics)
    cfg.set_value("settings", "aim_assist", aim_assist)
    cfg.set_value("stats", "wins", wins)
    cfg.set_value("stats", "losses", losses)
    cfg.set_value("stats", "draws", draws)
    cfg.set_value("stats", "goals_for", goals_for)
    cfg.set_value("stats", "goals_against", goals_against)
    cfg.save("user://circle_football.cfg")
