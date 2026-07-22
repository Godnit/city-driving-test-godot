extends Node3D

const ROAD_HALF_WIDTH: float = 6.0
const ROAD_LENGTH: float = 180.0
const BUILDING_SPACING: float = 28.0
const BUILDING_ROWS: int = 5

var car: CharacterBody3D
var hud_speed: Label
var hud_status: Label
var loading_panel: ColorRect
var checkpoints: Array[Area3D] = []
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
	_loading_text("تجهيز الطريق الخفيف...")
	await get_tree().process_frame
	_create_road()
	_loading_text("تجهيز مباني المدينة...")
	await get_tree().process_frame
	_create_city_models()
	_loading_text("تجهيز السيارة...")
	await get_tree().process_frame
	_create_player()
	_create_checkpoints()
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
	if ui_timer < 0.1:
		return
	ui_timer = 0.0
	hud_speed.text = "%03d km/h" % int(car.get_speed_kmh())
	if next_checkpoint < checkpoints.size():
		var distance: float = car.global_position.distance_to(checkpoints[next_checkpoint].global_position)
		hud_status.text = "بوابة %d/%d  %dm" % [next_checkpoint + 1, checkpoints.size(), int(distance)]
	else:
		hud_status.text = "اكتملت الجولة  %02d:%02d" % [int(elapsed) / 60, int(elapsed) % 60]

func _create_loading_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	loading_panel = ColorRect.new()
	loading_panel.color = Color(0.12, 0.18, 0.24, 1.0)
	loading_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(loading_panel)
	var title := Label.new()
	title.name = "LoadingText"
	title.text = "City Driving Test Lite\nجارٍ التشغيل..."
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 22)
	title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	loading_panel.add_child(title)

func _loading_text(value: String) -> void:
	var label := loading_panel.get_node_or_null("LoadingText") as Label
	if label:
		label.text = "City Driving Test Lite\n" + value

func _create_environment() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.44, 0.68, 0.88)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 1.0
	world.environment = environment
	add_child(world)

func _create_road() -> void:
	_add_static_box(Vector3(0.0, -0.18, -ROAD_LENGTH * 0.5), Vector3(ROAD_HALF_WIDTH * 2.0, 0.36, ROAD_LENGTH), Color(0.075, 0.08, 0.085))
	_add_static_box(Vector3(-7.25, 0.02, -ROAD_LENGTH * 0.5), Vector3(2.5, 0.25, ROAD_LENGTH), Color(0.45, 0.46, 0.47))
	_add_static_box(Vector3(7.25, 0.02, -ROAD_LENGTH * 0.5), Vector3(2.5, 0.25, ROAD_LENGTH), Color(0.45, 0.46, 0.47))
	_add_visual_box(Vector3(0.0, -0.42, -ROAD_LENGTH * 0.5), Vector3(34.0, 0.45, ROAD_LENGTH + 20.0), Color(0.24, 0.42, 0.23))
	_create_lane_markings()

func _create_lane_markings() -> void:
	var marking_mesh := BoxMesh.new()
	marking_mesh.size = Vector3(0.16, 0.025, 3.4)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.98, 0.94, 0.70)
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	marking_mesh.material = material
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = marking_mesh
	multimesh.instance_count = 18
	for i in range(18):
		var transform := Transform3D.IDENTITY
		transform.origin = Vector3(0.0, 0.018, -5.0 - float(i) * 10.0)
		multimesh.set_instance_transform(i, transform)
	var instance := MultiMeshInstance3D.new()
	instance.multimesh = multimesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(instance)

func _create_city_models() -> void:
	var paths: Array[String] = [
		"res://assets/models/building_01.glb",
		"res://assets/models/building_02.glb",
		"res://assets/models/building_03.glb",
		"res://assets/models/building_04.glb"
	]
	var scenes: Array[PackedScene] = []
	for path in paths:
		var scene := _load_scene(path)
		if scene:
			scenes.append(scene)
	if scenes.is_empty():
		push_error("No city models were imported")
		return
	for row in range(BUILDING_ROWS):
		var z: float = -24.0 - float(row) * BUILDING_SPACING
		for side_index in range(2):
			var side: float = -1.0 if side_index == 0 else 1.0
			var building := scenes[(row * 2 + side_index) % scenes.size()].instantiate()
			building.position = Vector3(side * 13.0, 0.0, z)
			building.rotation.y = PI * 0.5 if side < 0.0 else -PI * 0.5
			building.scale = Vector3.ONE * 1.65
			_make_model_mobile_fast(building)
			add_child(building)

func _create_player() -> void:
	car = CharacterBody3D.new()
	car.set_script(load("res://scripts/car.gd"))
	car.position = Vector3(2.4, 0.45, 4.0)
	add_child(car)

func _create_checkpoints() -> void:
	for i in range(3):
		var area := Area3D.new()
		area.position = Vector3(0.0, 1.0, -42.0 - float(i) * 50.0)
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(11.5, 3.0, 2.0)
		collision.shape = shape
		area.add_child(collision)
		area.body_entered.connect(_on_checkpoint.bind(i))
		add_child(area)
		checkpoints.append(area)

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
	hud_speed.position = Vector2(484, 8)
	hud_speed.size = Vector2(146, 34)
	hud_speed.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hud_speed.add_theme_font_size_override("font_size", 22)
	root.add_child(hud_speed)

	hud_status = Label.new()
	hud_status.text = "بوابة 1/3"
	hud_status.position = Vector2(170, 8)
	hud_status.size = Vector2(300, 34)
	hud_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_status.add_theme_font_size_override("font_size", 16)
	root.add_child(hud_status)

	_add_hold_button(root, "◀", Vector2(14, 274), Vector2(72, 72), "left")
	_add_hold_button(root, "▶", Vector2(94, 274), Vector2(72, 72), "right")
	_add_hold_button(root, "فرامل", Vector2(470, 278), Vector2(76, 68), "brake")
	_add_hold_button(root, "بنزين", Vector2(554, 264), Vector2(74, 82), "accelerate")

	var camera_button := Button.new()
	camera_button.text = "كاميرا"
	camera_button.position = Vector2(12, 10)
	camera_button.size = Vector2(82, 38)
	camera_button.add_theme_font_size_override("font_size", 14)
	camera_button.pressed.connect(func() -> void: car.toggle_camera())
	root.add_child(camera_button)

func _add_hold_button(parent: Control, text_value: String, position_value: Vector2, size_value: Vector2, action: String) -> void:
	var button := Button.new()
	button.text = text_value
	button.position = position_value
	button.size = size_value
	button.modulate = Color(1.0, 1.0, 1.0, 0.72)
	button.add_theme_font_size_override("font_size", 18)
	button.button_down.connect(func() -> void: car.set_control(action, true))
	button.button_up.connect(func() -> void: car.set_control(action, false))
	parent.add_child(button)

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
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
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
		geometry.visibility_range_end = 105.0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface_index in range(mesh_instance.mesh.get_surface_count()):
				var source_material := mesh_instance.mesh.surface_get_material(surface_index)
				if source_material is StandardMaterial3D:
					var fast_material := source_material.duplicate() as StandardMaterial3D
					fast_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
					fast_material.metallic = 0.0
					fast_material.roughness = 1.0
					mesh_instance.set_surface_override_material(surface_index, fast_material)
	for child in node.get_children():
		_make_model_mobile_fast(child)
