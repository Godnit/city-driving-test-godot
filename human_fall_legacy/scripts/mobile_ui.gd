extends Control

var move_vector = Vector2.ZERO
var jump_buffered = false
var camera_delta = Vector2.ZERO
var move_finger = -1
var camera_finger = -1
var jump_finger = -1
var joystick_center = Vector2.ZERO
var joystick_knob = Vector2.ZERO
var joystick_radius = 78.0
var jump_center = Vector2.ZERO
var jump_radius = 64.0

func _ready():
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    set_process_input(true)
    _rescale()
    get_viewport().connect("size_changed", self, "_rescale")
    update()

func _rescale():
    var s = get_viewport_rect().size
    rect_position = Vector2.ZERO
    rect_size = s
    var scale_factor = clamp(min(s.x / 960.0, s.y / 540.0), 0.72, 1.5)
    joystick_radius = 78.0 * scale_factor
    jump_radius = 64.0 * scale_factor
    joystick_center = Vector2(122.0 * scale_factor, s.y - 112.0 * scale_factor)
    jump_center = Vector2(s.x - 118.0 * scale_factor, s.y - 112.0 * scale_factor)
    if move_finger == -1:
        joystick_knob = joystick_center
    update()

func _input(event):
    if event is InputEventScreenTouch:
        _handle_touch(event)
    elif event is InputEventScreenDrag:
        _handle_drag(event)

func _handle_touch(event):
    var p = event.position
    if event.pressed:
        if p.distance_to(jump_center) <= jump_radius * 1.35 and jump_finger == -1:
            jump_finger = event.index
            jump_buffered = true
            update()
            return
        if p.x < get_viewport_rect().size.x * 0.48 and move_finger == -1:
            move_finger = event.index
            joystick_center = p
            joystick_knob = p
            move_vector = Vector2.ZERO
            update()
            return
        if camera_finger == -1:
            camera_finger = event.index
    else:
        if event.index == move_finger:
            move_finger = -1
            move_vector = Vector2.ZERO
            _rescale()
        if event.index == camera_finger:
            camera_finger = -1
        if event.index == jump_finger:
            jump_finger = -1
        update()

func _handle_drag(event):
    if event.index == move_finger:
        var delta = event.position - joystick_center
        var limited = delta
        if limited.length() > joystick_radius:
            limited = limited.normalized() * joystick_radius
        joystick_knob = joystick_center + limited
        move_vector = Vector2(limited.x / joystick_radius, -limited.y / joystick_radius)
        if move_vector.length() < 0.10:
            move_vector = Vector2.ZERO
        update()
    elif event.index == camera_finger:
        camera_delta += event.relative

func consume_jump():
    var value = jump_buffered
    jump_buffered = false
    return value

func consume_camera_delta():
    var value = camera_delta
    camera_delta = Vector2.ZERO
    return value

func _draw():
    draw_circle(joystick_center, joystick_radius, Color(0.08, 0.11, 0.15, 0.24))
    draw_arc(joystick_center, joystick_radius, 0.0, PI * 2.0, 64, Color(1, 1, 1, 0.34), 3.0, true)
    draw_circle(joystick_knob, joystick_radius * 0.43, Color(0.95, 0.97, 1.0, 0.44))
    draw_arc(joystick_knob, joystick_radius * 0.43, 0.0, PI * 2.0, 48, Color(1, 1, 1, 0.62), 2.0, true)
    var jump_alpha = 0.58 if jump_finger != -1 else 0.34
    draw_circle(jump_center, jump_radius, Color(0.18, 0.43, 0.70, jump_alpha))
    draw_arc(jump_center, jump_radius, 0.0, PI * 2.0, 64, Color(1, 1, 1, 0.60), 3.0, true)
    var r = jump_radius * 0.34
    var tri = PoolVector2Array([jump_center + Vector2(0, -r), jump_center + Vector2(r * 0.78, r * 0.45), jump_center + Vector2(-r * 0.78, r * 0.45)])
    draw_colored_polygon(tri, Color(1, 1, 1, 0.88))
