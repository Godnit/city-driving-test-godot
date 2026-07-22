extends Node3D

const ROAD_HALF_WIDTH := 7.5
const ROAD_LENGTH := 280.0
const BUILDING_SPACING := 24.0
const BUILDING_COUNT := 10

var car: CharacterBody3D
var hud_speed: Label
var hud_status: Label
var loading_panel: ColorRect
var checkpoints: Array[Area3D] = []
var next_checkpoint := 0
var elapsed := 0.0
var started := false

func _ready() -> void:
	DisplayServer.screen_set_orientation(DisplayServer.SCREEN_LANDSCAPE)
	Engine.max_fps = 30
	_create_loading_ui()
	await get_tree().process_frame
	_create_environment()
	_loading_text("إنشاء الطريق...")
	await get_tree().process_frame
	_create_road()
	_loading_text("تحميل المدينة...")
	await get_tree().process_frame
	_create_city_models()
	_loading_text("تحميل السيارة...")
	await get_tree().process_frame
	_create_player()
	_create_checkpoints()
	_create_hud()
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
	var kmh := car.get_speed_kmh()
	hud_speed.text = "%03d km/h" % int(kmh)
	if next_checkpoint < checkpoints.size():
		var dist := car.global_position.distance_to(checkpoints[next_checkpoint].global_position)
		hud_status.text = "البوابة %d/%d   المسافة %dm   الوقت %02d:%02d" % [next_checkpoint + 1, checkpoints.size(), int(dist), int(elapsed) / 60, int(elapsed) % 60]
	else:
		hud_status.text = "أحسنت! اكتملت الجولة خلال %02d:%02d" % [int(elapsed) / 60, int(elapsed) % 60]

func _create_loading_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	loading_panel = ColorRect.new()
	loading_panel.color = Color(0.02, 0.03, 0.05, 1.0)
	loading_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(loading_panel)
	var title := Label.new()
	title.name = "LoadingText"
	title.text = "City Driving Test\nجارٍ تجهيز اللعبة..."
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 36)
	title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	loading_panel.add_child(title)

func _loading_text(value: String) -> void:
	var label := loading_panel.get_node_or_null("LoadingText") as Label
	if label:
		label.text = "City Driving Test\n" + value

func _create_environment() -> void:
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.45, 0.67, 0.86)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.8, 0.86)
	env.ambient_light_energy = 0.85
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = env
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -28, 0)
	sun.light_energy = 1.15
	sun.shadow_enabled = false
	add_child(sun)

func _create_road() -> void:
	_add_static_box(Vector3(0, -0.25, -ROAD_LENGTH * 0.5), Vector3(ROAD_HALF_WIDTH * 2.0, 0.5, ROAD_LENGTH), Color(0.055, 0.06, 0.065))
	var road_model := _load_scene("res://assets/models/road_straight.glb")
	if road_model:
		for i in range(14):
			var segment := road_model.instantiate()
			segment.position = Vector3(0, 0.02, -10.0 - i * 20.0)
			segment.scale = Vector3(2.0, 2.0, 2.0)
			_disable_shadows(segment)
			add_child(segment)
	for side in [-1.0, 1.0]:
		_add_static_box(Vector3(side * 9.2, 0.05, -ROAD_LENGTH * 0.5), Vector3(3.0, 0.35, ROAD_LENGTH), Color(0.34, 0.36, 0.37))
	for i in range(28):
		_add_visual_box(Vector3(0, 0.035, -5.0 - i * 10.0), Vector3(0.22, 0.035, 4.0), Color(0.96, 0.93, 0.72))
	_add_static_box(Vector3(0, -0.65, -ROAD_LENGTH * 0.5), Vector3(50, 0.8, ROAD_LENGTH + 30), Color(0.23, 0.38, 0.2))

func _create_city_models() -> void:
	var building_paths: Array[String] = []
	for i in range(1, 9):
		building_paths.append("res://assets/models/building_%02d.glb" % i)
	for i in range(BUILDING_COUNT):
		var z := -18.0 - i * BUILDING_SPACING
		for side in [-1.0, 1.0]:
			var path := building_paths[(i * 2 + (0 if side < 0 else 1)) % building_paths.size()]
			var packed := _load_scene(path)
			if packed:
				var building := packed.instantiate()
				building.position = Vector3(side * 15.5, 0.0, z)
				building.rotation.y = PI * 0.5 if side < 0 else -PI * 0.5
				building.scale = Vector3.ONE * 1.7
				_disable_shadows(building)
				add_child(building)
			else:
				_add_visual_box(Vector3(side * 15.5, 5.0, z), Vector3(9, 10, 14), Color(0.52, 0.55, 0.58))
	var traffic_paths := ["res://assets/models/traffic_car_01.glb", "res://assets/models/traffic_car_02.glb", "res://assets/models/traffic_car_03.glb"]
	for i in range(6):
		var packed := _load_scene(traffic_paths[i % traffic_paths.size()])
		if packed:
			var vehicle := packed.instantiate()
			vehicle.position = Vector3(-3.2 if i % 2 == 0 else 3.2, 0.15, -45.0 - i * 32.0)
			vehicle.rotation.y = PI if i % 2 == 0 else 0.0
			vehicle.scale = Vector3.ONE * 1.35
			_disable_shadows(vehicle)
			add_child(vehicle)

func _create_player() -> void:
	car = CharacterBody3D.new()
	car.set_script(load("res://scripts/car.gd"))
	car.position = Vector3(2.5, 0.45, 4.0)
	add_child(car)

func _create_checkpoints() -> void:
	for i in range(4):
		var area := Area3D.new()
		area.position = Vector3(0, 1.0, -45.0 - i * 58.0)
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(14.0, 3.0, 2.0)
		shape.shape = box
		area.add_child(shape)
		area.body_entered.connect(_on_checkpoint.bind(i))
		add_child(area)
		checkpoints.append(area)
		var left_mesh := CylinderMesh.new()
		left_mesh.height = 3.2
		left_mesh.top_radius = 0.12
		left_mesh.bottom_radius = 0.12
		var left_post := _make_colored_mesh(left_mesh, Color(1.0, 0.35, 0.05))
		left_post.position = area.position + Vector3(-6.2, 1.6, 0)
		add_child(left_post)
		var right_post := left_post.duplicate()
		right_post.position = area.position + Vector3(6.2, 1.6, 0)
		add_child(right_post)

func _on_checkpoint(body: Node3D, index: int) -> void:
	if body == car and index == next_checkpoint:
		next_checkpoint += 1
		checkpoints[index].monitoring = false

func _create_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(root)
	hud_speed = Label.new()
	hud_speed.text = "000 km/h"
	hud_speed.position = Vector2(24, 20)
	hud_speed.add_theme_font_size_override("font_size", 34)
	root.add_child(hud_speed)
	hud_status = Label.new()
	hud_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_status.position = Vector2(260, 20)
	hud_status.size = Vector2(760, 48)
	hud_status.add_theme_font_size_override("font_size", 24)
	root.add_child(hud_status)
	_add_hold_button(root, "◀", Vector2(24, 525), Vector2(150, 150), "left")
	_add_hold_button(root, "▶", Vector2(184, 525), Vector2(150, 150), "right")
	_add_hold_button(root, "فرامل", Vector2(955, 545), Vector2(140, 125), "brake")
	_add_hold_button(root, "بنزين", Vector2(1105, 510), Vector2(150, 160), "accelerate")
	var camera_button := Button.new()
	camera_button.text = "كاميرا"
	camera_button.position = Vector2(1100, 22)
	camera_button.size = Vector2(145, 62)
	camera_button.add_theme_font_size_override("font_size", 22)
	camera_button.pressed.connect(func(): car.toggle_camera())
	root.add_child(camera_button)

func _add_hold_button(parent: Control, text: String, pos: Vector2, size: Vector2, action: String) -> void:
	var button := Button.new()
	button.text = text
	button.position = pos
	button.size = size
	button.modulate = Color(1, 1, 1, 0.78)
	button.add_theme_font_size_override("font_size", 28)
	button.button_down.connect(func(): car.set_control(action, true))
	button.button_up.connect(func(): car.set_control(action, false))
	parent.add_child(button)

func _add_static_box(pos: Vector3, size: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.position = pos
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)
	var mesh := BoxMesh.new()
	mesh.size = size
	body.add_child(_make_colored_mesh(mesh, color))
	add_child(body)

func _add_visual_box(pos: Vector3, size: Vector3, color: Color) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	var visual := _make_colored_mesh(mesh, color)
	visual.position = pos
	add_child(visual)

func _make_colored_mesh(mesh: Mesh, color: Color) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.8
	instance.material_override = material
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return instance

func _load_scene(path: String) -> PackedScene:
	if not ResourceLoader.exists(path):
		return null
	return load(path) as PackedScene

func _disable_shadows(node: Node) -> void:
	if node is GeometryInstance3D:
		(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		_disable_shadows(child)
