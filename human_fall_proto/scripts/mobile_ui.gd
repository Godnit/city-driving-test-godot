extends Control

var move_vector := Vector2.ZERO
var _jump_buffered := false
var _camera_delta := Vector2.ZERO
var _move_finger := -1
var _camera_finger := -1
var _jump_finger := -1
var _joystick_center := Vector2.ZERO
var _joystick_knob := Vector2.ZERO
var _joystick_radius := 78.0
var _jump_center := Vector2.ZERO
var _jump_radius := 64.0

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_process_input(true)
	_rescale()
	get_viewport().size_changed.connect(_rescale)
	queue_redraw()

func _rescale() -> void:
	var s := get_viewport_rect().size
	var scale_factor: float = clamp(min(s.x / 960.0, s.y / 540.0), 0.78, 1.55)
	_joystick_radius = 78.0 * scale_factor
	_jump_radius = 64.0 * scale_factor
	_joystick_center = Vector2(122.0 * scale_factor, s.y - 112.0 * scale_factor)
	_jump_center = Vector2(s.x - 118.0 * scale_factor, s.y - 112.0 * scale_factor)
	if _move_finger == -1:
		_joystick_knob = _joystick_center
	queue_redraw()

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)

func _handle_touch(event: InputEventScreenTouch) -> void:
	var p := event.position
	if event.pressed:
		if p.distance_to(_jump_center) <= _jump_radius * 1.35 and _jump_finger == -1:
			_jump_finger = event.index
			_jump_buffered = true
			queue_redraw()
			return
		if p.x < get_viewport_rect().size.x * 0.48 and _move_finger == -1:
			_move_finger = event.index
			_joystick_center = p
			_joystick_knob = p
			move_vector = Vector2.ZERO
			queue_redraw()
			return
		if _camera_finger == -1:
			_camera_finger = event.index
	else:
		if event.index == _move_finger:
			_move_finger = -1
			move_vector = Vector2.ZERO
			_rescale()
		if event.index == _camera_finger:
			_camera_finger = -1
		if event.index == _jump_finger:
			_jump_finger = -1
		queue_redraw()

func _handle_drag(event: InputEventScreenDrag) -> void:
	if event.index == _move_finger:
		var delta := event.position - _joystick_center
		var limited := delta.limit_length(_joystick_radius)
		_joystick_knob = _joystick_center + limited
		move_vector = Vector2(limited.x / _joystick_radius, -limited.y / _joystick_radius)
		if move_vector.length() < 0.10:
			move_vector = Vector2.ZERO
		queue_redraw()
	elif event.index == _camera_finger:
		_camera_delta += event.relative

func consume_jump() -> bool:
	var value := _jump_buffered
	_jump_buffered = false
	return value

func consume_camera_delta() -> Vector2:
	var value := _camera_delta
	_camera_delta = Vector2.ZERO
	return value

func _draw() -> void:
	draw_circle(_joystick_center, _joystick_radius, Color(0.08, 0.11, 0.15, 0.24))
	draw_arc(_joystick_center, _joystick_radius, 0.0, TAU, 64, Color(1, 1, 1, 0.34), 3.0, true)
	draw_circle(_joystick_knob, _joystick_radius * 0.43, Color(0.95, 0.97, 1.0, 0.44))
	draw_arc(_joystick_knob, _joystick_radius * 0.43, 0.0, TAU, 48, Color(1, 1, 1, 0.62), 2.0, true)
	var jump_alpha := 0.58 if _jump_finger != -1 else 0.34
	draw_circle(_jump_center, _jump_radius, Color(0.18, 0.43, 0.70, jump_alpha))
	draw_arc(_jump_center, _jump_radius, 0.0, TAU, 64, Color(1, 1, 1, 0.60), 3.0, true)
	var r := _jump_radius * 0.34
	var tri := PackedVector2Array([_jump_center + Vector2(0, -r), _jump_center + Vector2(r * 0.78, r * 0.45), _jump_center + Vector2(-r * 0.78, r * 0.45)])
	draw_colored_polygon(tri, Color(1, 1, 1, 0.88))
