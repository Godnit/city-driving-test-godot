extends Control

signal steer_changed(value: float)
signal action_changed(action: String, pressed: bool)
signal horn_pressed
signal camera_pressed
signal gear_selected(gear: String)

var steer_value: float = 0.0
var gear: String = "D"
var touch_roles: Dictionary = {}
var mouse_role: String = ""

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_process_input(true)
	queue_redraw()

func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			_press_pointer(touch.index, touch.position)
		else:
			_release_pointer(touch.index)
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		_drag_pointer(drag.index, drag.position)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var mouse_button := event as InputEventMouseButton
		if mouse_button.pressed:
			mouse_role = _role_at(mouse_button.position)
			_activate_role(mouse_role, mouse_button.position)
		else:
			_deactivate_role(mouse_role)
			mouse_role = ""
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		if mouse_role == "wheel":
			_update_wheel(event.position)

func _press_pointer(index: int, position: Vector2) -> void:
	var role := _role_at(position)
	touch_roles[index] = role
	_activate_role(role, position)

func _drag_pointer(index: int, position: Vector2) -> void:
	var role: String = str(touch_roles.get(index, ""))
	if role == "wheel":
		_update_wheel(position)

func _release_pointer(index: int) -> void:
	var role: String = str(touch_roles.get(index, ""))
	touch_roles.erase(index)
	if role == "wheel" and not _has_active_role("wheel"):
		steer_value = 0.0
		steer_changed.emit(0.0)
	elif role == "gas" and not _has_active_role("gas"):
		action_changed.emit("accelerate", false)
	elif role == "brake" and not _has_active_role("brake"):
		action_changed.emit("brake", false)
	queue_redraw()

func _activate_role(role: String, position: Vector2) -> void:
	match role:
		"wheel":
			_update_wheel(position)
		"horn":
			horn_pressed.emit()
		"gas":
			action_changed.emit("accelerate", true)
		"brake":
			action_changed.emit("brake", true)
		"camera":
			camera_pressed.emit()
		_:
			if role.begins_with("gear_"):
				gear = role.trim_prefix("gear_")
				gear_selected.emit(gear)
	queue_redraw()

func _deactivate_role(role: String) -> void:
	if role == "wheel":
		steer_value = 0.0
		steer_changed.emit(0.0)
	elif role == "gas":
		action_changed.emit("accelerate", false)
	elif role == "brake":
		action_changed.emit("brake", false)
	queue_redraw()

func _has_active_role(role: String) -> bool:
	for value in touch_roles.values():
		if str(value) == role:
			return true
	return false

func _update_wheel(position: Vector2) -> void:
	var center := _wheel_center()
	var radius := _wheel_radius()
	steer_value = clampf((position.x - center.x) / (radius * 0.78), -1.0, 1.0)
	steer_changed.emit(steer_value)
	queue_redraw()

func _role_at(position: Vector2) -> String:
	var center := _wheel_center()
	var distance := position.distance_to(center)
	var radius := _wheel_radius()
	if distance <= radius * 0.34:
		return "horn"
	if distance <= radius * 1.18:
		return "wheel"
	if _gas_rect().has_point(position):
		return "gas"
	if _brake_rect().has_point(position):
		return "brake"
	if _camera_rect().has_point(position):
		return "camera"
	var gear_rects := _gear_rects()
	for key in gear_rects.keys():
		if (gear_rects[key] as Rect2).has_point(position):
			return "gear_" + str(key)
	return ""

func _wheel_center() -> Vector2:
	return Vector2(size.x * 0.165, size.y * 0.77)

func _wheel_radius() -> float:
	return minf(size.y * 0.205, size.x * 0.125)

func _gas_rect() -> Rect2:
	return Rect2(size.x * 0.855, size.y * 0.60, size.x * 0.105, size.y * 0.34)

func _brake_rect() -> Rect2:
	return Rect2(size.x * 0.715, size.y * 0.68, size.x * 0.105, size.y * 0.26)

func _camera_rect() -> Rect2:
	return Rect2(size.x * 0.865, size.y * 0.035, size.x * 0.105, size.y * 0.12)

func _gear_rects() -> Dictionary:
	var result: Dictionary = {}
	var top := size.y * 0.22
	var height := size.y * 0.085
	for index in range(4):
		var label := ["P", "R", "N", "D"][index]
		result[label] = Rect2(size.x * 0.90, top + float(index) * (height + 4.0), size.x * 0.065, height)
	return result

func _draw() -> void:
	var center := _wheel_center()
	var radius := _wheel_radius()
	var rim_color := Color(0.045, 0.055, 0.065, 0.82)
	var edge_color := Color(0.78, 0.82, 0.85, 0.92)
	draw_circle(center, radius, rim_color)
	draw_arc(center, radius, 0.0, TAU, 64, edge_color, 7.0, true)
	var angle := steer_value * 0.92
	for base_angle in [-PI * 0.5, PI / 6.0, PI * 5.0 / 6.0]:
		var spoke_angle := base_angle + angle
		var inner := center + Vector2(cos(spoke_angle), sin(spoke_angle)) * radius * 0.25
		var outer := center + Vector2(cos(spoke_angle), sin(spoke_angle)) * radius * 0.77
		draw_line(inner, outer, edge_color, 8.0, true)
	draw_circle(center, radius * 0.32, Color(0.12, 0.14, 0.16, 0.96))
	draw_arc(center, radius * 0.32, 0.0, TAU, 40, Color(0.95, 0.57, 0.10, 0.95), 3.0, true)
	_draw_centered_text(Rect2(center - Vector2(radius * 0.30, radius * 0.15), Vector2(radius * 0.60, radius * 0.30)), "HORN", 15, Color.WHITE)
	_draw_pedal(_gas_rect(), "GAS", Color(0.08, 0.44, 0.16, 0.86), _has_active_role("gas") or mouse_role == "gas")
	_draw_pedal(_brake_rect(), "BRAKE", Color(0.62, 0.10, 0.08, 0.86), _has_active_role("brake") or mouse_role == "brake")
	var camera_rect := _camera_rect()
	draw_style_box(_style(Color(0.04, 0.055, 0.07, 0.78), Color(0.75, 0.82, 0.86, 0.82), 12.0), camera_rect)
	_draw_centered_text(camera_rect, "CAM", 15, Color.WHITE)
	var gear_rects := _gear_rects()
	for key in gear_rects.keys():
		var rect := gear_rects[key] as Rect2
		var selected := str(key) == gear
		var background := Color(0.08, 0.42, 0.16, 0.90) if selected else Color(0.04, 0.055, 0.07, 0.78)
		draw_style_box(_style(background, Color(0.72, 0.78, 0.82, 0.78), 9.0), rect)
		_draw_centered_text(rect, str(key), 17, Color.WHITE)

func _draw_pedal(rect: Rect2, label: String, color: Color, active: bool) -> void:
	var shown := color.lightened(0.18) if active else color
	draw_style_box(_style(shown, Color(0.88, 0.90, 0.92, 0.88), 12.0), rect)
	for index in range(3):
		var y := rect.position.y + rect.size.y * (0.31 + float(index) * 0.18)
		draw_line(Vector2(rect.position.x + rect.size.x * 0.23, y), Vector2(rect.end.x - rect.size.x * 0.23, y), Color(0.95, 0.95, 0.95, 0.55), 3.0)
	_draw_centered_text(rect, label, 15, Color.WHITE)

func _draw_centered_text(rect: Rect2, text_value: String, font_size: int, color: Color) -> void:
	var font := ThemeDB.fallback_font
	var text_size := font.get_string_size(text_value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	var baseline := rect.position + Vector2((rect.size.x - text_size.x) * 0.5, (rect.size.y + text_size.y) * 0.5 - 2.0)
	draw_string(font, baseline, text_value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _style(background: Color, border: Color, radius: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(2)
	style.corner_radius_top_left = int(radius)
	style.corner_radius_top_right = int(radius)
	style.corner_radius_bottom_left = int(radius)
	style.corner_radius_bottom_right = int(radius)
	return style
