extends Node3D

const MAIN_ROAD_LENGTH: float = 280.0
const CROSS_ROAD_LENGTH: float = 190.0
const INTERSECTION_Z: float = -220.0
const ROAD_SURFACE_Y: float = -0.16
const PLAYER_LANE_X: float = 5.5

var car: CharacterBody3D
var hud_speed: Label
var hud_status: Label
var navigation_arrow: Label
var loading_panel: ColorRect
var checkpoints: Array[Area3D] = []
var gear_buttons: Dictionary = {}
var next_checkpoint: int = 0
var elapsed: float = 0.0
var ui_timer: float = 0.0
var started: bool = false

func _ready() -> void:
	DisplayServer.screen_set_orientation(DisplayServer.SCREEN_LANDSCAPE)
	Engine.max_fps = 30
	Engine.physics_ticks_per_second = 30
	_create_loading_ui()
	await get_tree().process_frame
	_create_environment()
	_loading_text("تجهيز شوارع المدينة...")
	await get_tree().process_frame
	_create_city_roads()
	_loading_text("تحميل مباني Sketchfab...")
	await get_tree().process_frame
	_create_city_assets()
	_loading_text("تجهيز السيارة...")
	await get_tree().process_frame
	_create_player()
	_create_route()
	_create_hud()
	if is_instance_valid(loading_panel):
		loading_panel.queue_free()
	started = true
	if "--smoke-test" in OS.get_cmdline_user_args():
		print("CITY_DRIVING_READY")
		await get_tree().process_frame
		get_tree().quit()

func _process(delta: float) -> void:
	if not started or not is_instance_valid(car):
		return
	elapsed += delta
	ui_timer += delta
	if ui_timer < 0.08:
		return
	ui_timer = 0.0
	hud_speed.text = "%03d" % int(car.get_speed_kmh())
	if next_checkpoint < checkpoints.size():
		var target := checkpoints[next_checkpoint].global_position
		var distance := car.global_position.distance_to(target)
		hud_status.text = "%dm" % int(distance)
		navigation_arrow.text = _navigation_symbol(target)
	else:
		hud_status.text = "%02d:%02d" % [int(elapsed) / 60, int(elapsed) % 60]
		navigation_arrow.text = "✓"

func _navigation_symbol(target: Vector3) -> String:
	var local_target := car.to_local(target)
	if absf(local_target.x) > maxf(8.0, absf(local_target.z) * 0.48):
		return "↱" if local_target.x > 0.0 else "↰"
	if local_target.z < 0.0:
		return "↑"
	return "↶"

func _create_loading_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	loading_panel = ColorRect.new()
	loading_panel.color = Color(0.035, 0.055, 0.075, 1.0)
	loading_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(loading_panel)
	var title := Label.new()
	title.name = "LoadingText"
	title.text = "CITY DRIVE\nجارٍ التشغيل..."
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 24)
	title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	loading_panel.add_child(title)

func _loading_text(value: String) -> void:
	var label := loading_panel.get_node_or_null("LoadingText") as Label
	if label:
		label.text = "CITY DRIVE\n" + value

func _create_environment() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.38, 0.62, 0.80)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.82, 0.86, 0.90)
	environment.ambient_light_energy = 0.95
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -32.0, 0.0)
	sun.light_energy = 0.78
	sun.shadow_enabled = false
	add_child(sun)

func _create_city_roads() -> void:
	# Wide ground prevents the camera from showing empty space around the city corridor.
	_add_static_box(Vector3(0.0, -0.55, -130.0), Vector3(220.0, 0.7, 340.0), Color(0.20, 0.27, 0.19))
	# Two three-lane carriageways separated by a raised median.
	_add_static_box(Vector3(-5.5, ROAD_SURFACE_Y, -120.0), Vector3(9.5, 0.32, MAIN_ROAD_LENGTH), Color(0.055, 0.060, 0.066))
	_add_static_box(Vector3(5.5, ROAD_SURFACE_Y, -120.0), Vector3(9.5, 0.32, MAIN_ROAD_LENGTH), Color(0.055, 0.060, 0.066))
	# Main-road sidewalks.
	_add_static_box(Vector3(-12.0, 0.0, -120.0), Vector3(3.2, 0.30, MAIN_ROAD_LENGTH), Color(0.39, 0.40, 0.41))
	_add_static_box(Vector3(12.0, 0.0, -120.0), Vector3(3.2, 0.30, MAIN_ROAD_LENGTH), Color(0.39, 0.40, 0.41))
	# Median split around the junction to create a real turn opening.
	_add_static_box(Vector3(0.0, 0.05, -96.0), Vector3(1.25, 0.38, 190.0), Color(0.31, 0.33, 0.31))
	_add_static_box(Vector3(0.0, 0.05, -262.0), Vector3(1.25, 0.38, 44.0), Color(0.31, 0.33, 0.31))
	# Cross street and sidewalks at the end of the first mission leg.
	_add_static_box(Vector3(0.0, ROAD_SURFACE_Y, INTERSECTION_Z), Vector3(CROSS_ROAD_LENGTH, 0.32, 18.0), Color(0.055, 0.060, 0.066))
	_add_static_box(Vector3(0.0, 0.0, INTERSECTION_Z - 11.0), Vector3(CROSS_ROAD_LENGTH, 0.30, 3.0), Color(0.39, 0.40, 0.41))
	_add_static_box(Vector3(0.0, 0.0, INTERSECTION_Z + 11.0), Vector3(CROSS_ROAD_LENGTH, 0.30, 3.0), Color(0.39, 0.40, 0.41))
	_create_main_lane_markings()
	_create_cross_lane_markings()
	_create_intersection_details()

func _create_main_lane_markings() -> void:
	var transforms: Array[Transform3D] = []
	for x in [-7.0, -4.0, 4.0, 7.0]:
		for index in range(27):
			var transform := Transform3D.IDENTITY
			transform.origin = Vector3(x, 0.018, 12.0 - float(index) * 10.0)
			transforms.append(transform)
	_add_multimesh_boxes(Vector3(0.13, 0.024, 3.6), Color(0.93, 0.93, 0.88), transforms)
	# Solid white road edges.
	for x in [-10.0, -1.0, 1.0, 10.0]:
		_add_visual_box(Vector3(x, 0.018, -120.0), Vector3(0.12, 0.024, MAIN_ROAD_LENGTH), Color(0.94, 0.94, 0.90))

func _create_cross_lane_markings() -> void:
	var transforms: Array[Transform3D] = []
	for z in [INTERSECTION_Z - 3.0, INTERSECTION_Z + 3.0]:
		for index in range(19):
			var transform := Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(-86.0 + float(index) * 9.5, 0.018, z))
			transforms.append(transform)
	_add_multimesh_boxes(Vector3(0.13, 0.024, 3.4), Color(0.93, 0.93, 0.88), transforms)

func _create_intersection_details() -> void:
	# Stop lines and zebra crossings give the junction the visual structure of a driving game.
	_add_visual_box(Vector3(5.5, 0.022, INTERSECTION_Z + 15.0), Vector3(9.0, 0.028, 0.36), Color.WHITE)
	for index in range(6):
		_add_visual_box(Vector3(-7.5 + float(index) * 3.0, 0.023, INTERSECTION_Z + 10.5), Vector3(1.5, 0.03, 4.4), Color(0.92, 0.92, 0.89))
	_create_traffic_light(Vector3(10.8, 0.0, INTERSECTION_Z + 12.0), -PI * 0.5)
	_create_traffic_light(Vector3(-10.8, 0.0, INTERSECTION_Z - 12.0), PI * 0.5)

func _create_traffic_light(position_value: Vector3, rotation_value: float) -> void:
	var root := Node3D.new()
	root.position = position_value
	root.rotation.y = rotation_value
	add_child(root)
	var pole := CylinderMesh.new()
	pole.height = 4.8
	pole.top_radius = 0.09
	pole.bottom_radius = 0.11
	var pole_instance := _make_colored_mesh(pole, Color(0.10, 0.11, 0.12))
	pole_instance.position.y = 2.4
	root.add_child(pole_instance)
	var housing := BoxMesh.new()
	housing.size = Vector3(0.55, 1.55, 0.42)
	var housing_instance := _make_colored_mesh(housing, Color(0.06, 0.07, 0.08))
	housing_instance.position = Vector3(0.0, 4.35, 0.0)
	root.add_child(housing_instance)
	for light_index in range(3):
		var lamp := SphereMesh.new()
		lamp.radius = 0.12
		lamp.height = 0.24
		var lamp_color := [Color(0.85, 0.12, 0.08), Color(0.92, 0.63, 0.08), Color(0.10, 0.72, 0.22)][light_index]
		var lamp_instance := _make_colored_mesh(lamp, lamp_color)
		lamp_instance.position = Vector3(0.0, 4.82 - float(light_index) * 0.46, -0.23)
		root.add_child(lamp_instance)

func _create_city_assets() -> void:
	var building_paths: Array[String] = [
		"res://assets/sketchfab/building_01.glb",
		"res://assets/sketchfab/building_02.glb",
		"res://assets/sketchfab/building_03.glb",
		"res://assets/sketchfab/building_04.glb"
	]
	var scenes: Array[PackedScene] = []
	for path in building_paths:
		var packed := _load_scene(path)
		if packed:
			scenes.append(packed)
	if scenes.is_empty():
		# Development-only silhouettes. Final APK is not released until Sketchfab assets exist.
		_create_city_silhouettes()
		return
	for row in range(8):
		var z := 5.0 - float(row) * 34.0
		for side_index in range(2):
			var side := -1.0 if side_index == 0 else 1.0
			var building := scenes[(row * 2 + side_index) % scenes.size()].instantiate()
			building.position = Vector3(side * 17.5, 0.0, z)
			building.rotation.y = PI * 0.5 if side < 0.0 else -PI * 0.5
			_make_model_mobile_fast(building)
			add_child(building)
	for row in range(5):
		for side_index in range(2):
			var side := -1.0 if side_index == 0 else 1.0
			var building := scenes[(row + side_index) % scenes.size()].instantiate()
			building.position = Vector3(side * (28.0 + float(row) * 31.0), 0.0, INTERSECTION_Z + side * 17.0)
			building.rotation.y = 0.0 if side < 0.0 else PI
			_make_model_mobile_fast(building)
			add_child(building)

func _create_city_silhouettes() -> void:
	for index in range(8):
		var z := 4.0 - float(index) * 34.0
		for side in [-1.0, 1.0]:
			var height := 8.0 + float(index % 3) * 2.5
			_add_visual_box(Vector3(side * 18.0, height * 0.5, z), Vector3(10.0, height, 18.0), Color(0.30, 0.34, 0.38))

func _create_player() -> void:
	car = CharacterBody3D.new()
	car.set_script(load("res://scripts/car.gd"))
	car.position = Vector3(PLAYER_LANE_X, 0.46, 12.0)
	add_child(car)

func _create_route() -> void:
	var route: Array[Vector3] = [
		Vector3(PLAYER_LANE_X, 1.0, -78.0),
		Vector3(PLAYER_LANE_X, 1.0, -188.0),
		Vector3(35.0, 1.0, INTERSECTION_Z),
		Vector3(82.0, 1.0, INTERSECTION_Z)
	]
	for index in range(route.size()):
		var area := Area3D.new()
		area.position = route[index]
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(13.0, 3.0, 4.0) if index < 2 else Vector3(4.0, 3.0, 14.0)
		collision.shape = shape
		area.add_child(collision)
		area.body_entered.connect(_on_checkpoint.bind(index))
		add_child(area)
		checkpoints.append(area)

func _on_checkpoint(body: Node3D, index: int) -> void:
	if body == car and index == next_checkpoint:
		next_checkpoint += 1
		checkpoints[index].monitoring = false

func _create_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_PASS
	layer.add_child(root)

	# Mission direction and distance, centered like a navigation HUD.
	navigation_arrow = Label.new()
	navigation_arrow.text = "↑"
	_set_control_rect(navigation_arrow, 0.42, 0.02, 0.58, 0.18)
	navigation_arrow.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	navigation_arrow.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	navigation_arrow.add_theme_font_size_override("font_size", 38)
	navigation_arrow.add_theme_color_override("font_color", Color(1.0, 0.48, 0.08))
	root.add_child(navigation_arrow)

	hud_status = Label.new()
	hud_status.text = "90m"
	_set_control_rect(hud_status, 0.43, 0.15, 0.57, 0.24)
	hud_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_status.add_theme_font_size_override("font_size", 17)
	root.add_child(hud_status)

	var speed_panel := Panel.new()
	_set_control_rect(speed_panel, 0.80, 0.02, 0.98, 0.16)
	speed_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.02, 0.025, 0.03, 0.72), Color(0.82, 0.84, 0.86, 0.55)))
	root.add_child(speed_panel)
	hud_speed = Label.new()
	hud_speed.text = "000"
	hud_speed.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud_speed.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_speed.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hud_speed.add_theme_font_size_override("font_size", 25)
	speed_panel.add_child(hud_speed)
	var unit := Label.new()
	unit.text = "km/h"
	unit.position = Vector2(45.0, 28.0)
	unit.add_theme_font_size_override("font_size", 10)
	speed_panel.add_child(unit)

	var camera_button := Button.new()
	camera_button.text = "CAM"
	_set_control_rect(camera_button, 0.02, 0.03, 0.14, 0.14)
	_apply_button_style(camera_button, Color(0.04, 0.05, 0.06, 0.75), Color(0.22, 0.68, 0.95, 0.92))
	camera_button.pressed.connect(func() -> void: car.toggle_camera())
	root.add_child(camera_button)

	# Steering buttons use anchors, so they stay visible on every landscape aspect ratio.
	_add_hold_button(root, "◀", 0.025, 0.70, 0.145, 0.96, "left", Color(0.08, 0.11, 0.14, 0.78))
	_add_hold_button(root, "▶", 0.155, 0.70, 0.275, 0.96, "right", Color(0.08, 0.11, 0.14, 0.78))
	_add_hold_button(root, "BRAKE", 0.69, 0.74, 0.82, 0.96, "brake", Color(0.50, 0.08, 0.07, 0.82))
	_add_hold_button(root, "GAS", 0.835, 0.66, 0.97, 0.96, "accelerate", Color(0.10, 0.45, 0.12, 0.84))
	_create_gear_selector(root)

func _create_gear_selector(parent: Control) -> void:
	var selector := VBoxContainer.new()
	_set_control_rect(selector, 0.90, 0.19, 0.98, 0.62)
	selector.add_theme_constant_override("separation", 2)
	parent.add_child(selector)
	for gear_name in ["P", "R", "N", "D"]:
		var button := Button.new()
		button.text = gear_name
		button.custom_minimum_size = Vector2(0.0, 30.0)
		button.size_flags_vertical = Control.SIZE_EXPAND_FILL
		button.add_theme_font_size_override("font_size", 14)
		_apply_button_style(button, Color(0.025, 0.03, 0.04, 0.78), Color(0.95, 0.52, 0.08, 0.95))
		button.pressed.connect(_on_gear_pressed.bind(gear_name))
		selector.add_child(button)
		gear_buttons[gear_name] = button
	_on_gear_pressed("D")

func _on_gear_pressed(gear_name: String) -> void:
	if not is_instance_valid(car):
		return
	car.set_gear(gear_name)
	for key in gear_buttons.keys():
		var button := gear_buttons[key] as Button
		button.modulate = Color(1.0, 0.63, 0.20, 1.0) if key == gear_name else Color.WHITE

func _add_hold_button(parent: Control, text_value: String, left: float, top: float, right: float, bottom: float, action: String, color_value: Color) -> void:
	var button := Button.new()
	button.text = text_value
	_set_control_rect(button, left, top, right, bottom)
	button.add_theme_font_size_override("font_size", 18)
	_apply_button_style(button, color_value, Color(1.0, 0.52, 0.08, 0.96))
	button.button_down.connect(func() -> void: car.set_control(action, true))
	button.button_up.connect(func() -> void: car.set_control(action, false))
	parent.add_child(button)

func _set_control_rect(control: Control, left: float, top: float, right: float, bottom: float) -> void:
	control.anchor_left = left
	control.anchor_top = top
	control.anchor_right = right
	control.anchor_bottom = bottom
	control.offset_left = 0.0
	control.offset_top = 0.0
	control.offset_right = 0.0
	control.offset_bottom = 0.0

func _apply_button_style(button: Button, normal_color: Color, pressed_color: Color) -> void:
	button.add_theme_stylebox_override("normal", _panel_style(normal_color, Color(0.90, 0.92, 0.94, 0.72)))
	button.add_theme_stylebox_override("hover", _panel_style(normal_color.lightened(0.08), Color.WHITE))
	button.add_theme_stylebox_override("pressed", _panel_style(pressed_color, Color.WHITE))
	button.add_theme_color_override("font_color", Color.WHITE)
	button.add_theme_color_override("font_pressed_color", Color.WHITE)

func _panel_style(background: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(2)
	style.corner_radius_top_left = 9
	style.corner_radius_top_right = 9
	style.corner_radius_bottom_left = 9
	style.corner_radius_bottom_right = 9
	return style

func _add_multimesh_boxes(size_value: Vector3, color_value: Color, transforms: Array[Transform3D]) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh.material = material
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = mesh
	multimesh.instance_count = transforms.size()
	for index in range(transforms.size()):
		multimesh.set_instance_transform(index, transforms[index])
	var instance := MultiMeshInstance3D.new()
	instance.multimesh = multimesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(instance)

func _add_static_box(position_value: Vector3, size_value: Vector3, color_value: Color) -> void:
	var body := StaticBody3D.new()
	body.position = position_value
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size_value
	collision.shape = shape
	body.add_child(collision)
	var mesh := BoxMesh.new()
	mesh.size = size_value
	body.add_child(_make_colored_mesh(mesh, color_value))
	add_child(body)

func _add_visual_box(position_value: Vector3, size_value: Vector3, color_value: Color) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var visual := _make_colored_mesh(mesh, color_value)
	visual.position = position_value
	add_child(visual)

func _make_colored_mesh(mesh: Mesh, color_value: Color) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = 0.88
	material.metallic = 0.0
	instance.material_override = material
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return instance

func _load_scene(path: String) -> PackedScene:
	if not ResourceLoader.exists(path):
		return null
	return load(path) as PackedScene

func _make_model_mobile_fast(node: Node) -> void:
	if node is Camera3D or node is Light3D or node is WorldEnvironment:
		node.queue_free()
		return
	if node is GeometryInstance3D:
		var geometry := node as GeometryInstance3D
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geometry.visibility_range_end = 135.0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface_index in range(mesh_instance.mesh.get_surface_count()):
				var source_material := mesh_instance.mesh.surface_get_material(surface_index)
				if source_material is StandardMaterial3D:
					var fast_material := source_material.duplicate() as StandardMaterial3D
					fast_material.metallic = 0.0
					fast_material.roughness = 0.82
					mesh_instance.set_surface_override_material(surface_index, fast_material)
	for child in node.get_children():
		_make_model_mobile_fast(child)
