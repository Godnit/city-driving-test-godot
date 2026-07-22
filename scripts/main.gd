extends Node3D

const ROAD_LENGTH: float = 740.0
const ROAD_CENTER_Z: float = -300.0
const MAIN_ROAD_HALF: float = 11.0
const CROSS_STREETS: Array[float] = [20.0, -160.0, -340.0, -520.0]
const PLAYER_LANE_X: float = 5.4

var car: CharacterBody3D
var camera_rig: Camera3D
var hud_speed: Label
var hud_status: Label
var navigation_arrow: Label
var checkpoints: Array[Area3D] = []
var next_checkpoint: int = 0
var elapsed: float = 0.0
var ui_timer: float = 0.0
var started: bool = false
var building_prototypes: Array[Node3D] = []
var curb_scene: PackedScene

func _ready() -> void:
	DisplayServer.screen_set_orientation(DisplayServer.SCREEN_LANDSCAPE)
	Engine.max_fps = 30
	Engine.physics_ticks_per_second = 30
	_create_loading_ui()
	await get_tree().process_frame
	_create_environment()
	_prepare_city_assets()
	_update_loading("بناء شبكة الطرق...")
	_create_road_network()
	await get_tree().process_frame
	_update_loading("تنظيم مباني المدينة...")
	_create_dense_buildings()
	await get_tree().process_frame
	_update_loading("إضافة حركة المرور...")
	_create_player()
	_create_traffic()
	_create_route()
	_create_hud()
	await get_tree().process_frame
	var loading := get_node_or_null("LoadingLayer")
	if loading:
		loading.queue_free()
	started = true
	if "--smoke-test" in OS.get_cmdline_user_args():
		print("CITY_DRIVING_V06_READY")
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
	hud_speed.text = "%03d\nkm/h" % int(car.get_speed_kmh())
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
	if absf(local_target.x) > maxf(9.0, absf(local_target.z) * 0.45):
		return "↱" if local_target.x > 0.0 else "↰"
	return "↑" if local_target.z < 0.0 else "↶"

func _create_loading_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "LoadingLayer"
	layer.layer = 100
	add_child(layer)
	var background := ColorRect.new()
	background.name = "LoadingBackground"
	background.color = Color(0.035, 0.055, 0.075, 1.0)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(background)
	var label := Label.new()
	label.name = "LoadingText"
	label.text = "CITY DRIVE MISSIONS\nجارٍ التشغيل..."
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 23)
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_child(label)

func _update_loading(text_value: String) -> void:
	var label := get_node_or_null("LoadingLayer/LoadingBackground/LoadingText") as Label
	if label:
		label.text = "CITY DRIVE MISSIONS\n" + text_value

func _create_environment() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.47, 0.68, 0.82)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.88, 0.90, 0.92)
	environment.ambient_light_energy = 0.92
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	environment.fog_enabled = true
	environment.fog_light_color = Color(0.48, 0.66, 0.78)
	environment.fog_density = 0.0028
	environment.fog_sky_affect = 0.65
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52.0, -28.0, 0.0)
	sun.light_energy = 0.82
	sun.shadow_enabled = false
	add_child(sun)

func _create_road_network() -> void:
	_add_static_box(Vector3(0.0, -0.48, ROAD_CENTER_Z), Vector3(290.0, 0.90, ROAD_LENGTH + 80.0), Color(0.20, 0.27, 0.19))
	_add_static_box(Vector3(0.0, 0.0, ROAD_CENTER_Z), Vector3(MAIN_ROAD_HALF * 2.0, 0.12, ROAD_LENGTH), Color(0.055, 0.060, 0.066))
	for street_z in CROSS_STREETS:
		_add_static_box(Vector3(-73.0, 0.0, street_z), Vector3(124.0, 0.12, 18.0), Color(0.055, 0.060, 0.066))
		_add_static_box(Vector3(73.0, 0.0, street_z), Vector3(124.0, 0.12, 18.0), Color(0.055, 0.060, 0.066))
	_create_main_sidewalks()
	_create_cross_sidewalks()
	_create_main_markings()
	_create_cross_markings()
	_create_intersections()
	_create_street_lights()

func _create_main_sidewalks() -> void:
	var boundaries: Array[float] = [70.0]
	for z_value in CROSS_STREETS:
		boundaries.append(z_value + 12.0)
		boundaries.append(z_value - 12.0)
	boundaries.append(-670.0)
	for index in range(0, boundaries.size() - 1, 2):
		var top := boundaries[index]
		var bottom := boundaries[index + 1]
		var length := top - bottom
		var center_z := (top + bottom) * 0.5
		for side in [-1.0, 1.0]:
			_add_static_box(Vector3(side * 13.0, 0.15, center_z), Vector3(4.0, 0.20, length), Color(0.38, 0.39, 0.40))
			_place_curb_strip(side * 11.18, center_z, length, side < 0.0)

func _create_cross_sidewalks() -> void:
	for street_z in CROSS_STREETS:
		for side_z in [-1.0, 1.0]:
			var z_position := street_z + side_z * 11.0
			_add_static_box(Vector3(-76.0, 0.15, z_position), Vector3(124.0, 0.20, 3.2), Color(0.38, 0.39, 0.40))
			_add_static_box(Vector3(76.0, 0.15, z_position), Vector3(124.0, 0.20, 3.2), Color(0.38, 0.39, 0.40))

func _place_curb_strip(x_position: float, center_z: float, total_length: float, rotate: bool) -> void:
	if curb_scene == null:
		return
	var count := int(total_length / 8.8)
	var start_z := center_z + total_length * 0.5 - 4.4
	for index in range(count):
		var curb := curb_scene.instantiate() as Node3D
		curb.position = Vector3(x_position, 0.06, start_z - float(index) * 8.8)
		curb.rotation.y = PI if rotate else 0.0
		_prepare_static_visual(curb)
		add_child(curb)

func _create_main_markings() -> void:
	for lane_x in [-7.2, -3.7, 3.7, 7.2]:
		for index in range(72):
			var z_value := 58.0 - float(index) * 10.0
			if _near_intersection(z_value, 14.0):
				continue
			_add_visual_box(Vector3(lane_x, 0.071, z_value), Vector3(0.13, 0.012, 3.8), Color(0.93, 0.93, 0.88))
	for edge_x in [-10.5, -0.75, 0.75, 10.5]:
		_add_visual_box(Vector3(edge_x, 0.071, ROAD_CENTER_Z), Vector3(0.12, 0.012, ROAD_LENGTH), Color(0.96, 0.96, 0.92))

func _create_cross_markings() -> void:
	for street_z in CROSS_STREETS:
		for lane_offset in [-3.1, 3.1]:
			for side in [-1.0, 1.0]:
				for index in range(12):
					var x_value := side * (17.0 + float(index) * 9.0)
					_add_visual_box(Vector3(x_value, 0.071, street_z + lane_offset), Vector3(3.7, 0.012, 0.13), Color(0.93, 0.93, 0.88))

func _create_intersections() -> void:
	for street_z in CROSS_STREETS:
		_add_visual_box(Vector3(5.5, 0.074, street_z + 13.0), Vector3(9.3, 0.015, 0.34), Color.WHITE)
		for stripe in range(7):
			_add_visual_box(Vector3(-9.0 + float(stripe) * 3.0, 0.074, street_z + 9.8), Vector3(1.5, 0.015, 3.8), Color(0.92, 0.92, 0.89))
		_create_traffic_light(Vector3(10.4, 0.0, street_z + 12.5), -PI * 0.5)
		_create_traffic_light(Vector3(-10.4, 0.0, street_z - 12.5), PI * 0.5)

func _near_intersection(z_value: float, margin: float) -> bool:
	for street_z in CROSS_STREETS:
		if absf(z_value - street_z) < margin:
			return true
	return false

func _create_traffic_light(position_value: Vector3, rotation_value: float) -> void:
	var root := Node3D.new()
	root.position = position_value
	root.rotation.y = rotation_value
	add_child(root)
	var pole := CylinderMesh.new()
	pole.height = 4.7
	pole.top_radius = 0.08
	pole.bottom_radius = 0.10
	var pole_mesh := _make_colored_mesh(pole, Color(0.08, 0.09, 0.10))
	pole_mesh.position.y = 2.35
	root.add_child(pole_mesh)
	var housing := BoxMesh.new()
	housing.size = Vector3(0.50, 1.42, 0.40)
	var housing_mesh := _make_colored_mesh(housing, Color(0.035, 0.04, 0.045))
	housing_mesh.position = Vector3(0.0, 4.25, 0.0)
	root.add_child(housing_mesh)
	var colors: Array[Color] = [Color(0.82, 0.08, 0.05), Color(0.90, 0.54, 0.05), Color(0.05, 0.72, 0.18)]
	for index in range(3):
		var lamp := SphereMesh.new()
		lamp.radius = 0.115
		lamp.height = 0.23
		var lamp_mesh := _make_colored_mesh(lamp, colors[index])
		lamp_mesh.position = Vector3(0.0, 4.65 - float(index) * 0.43, -0.22)
		root.add_child(lamp_mesh)

func _create_street_lights() -> void:
	for index in range(28):
		var z_value := 55.0 - float(index) * 25.5
		if _near_intersection(z_value, 16.0):
			continue
		for side in [-1.0, 1.0]:
			var pole := CylinderMesh.new()
			pole.height = 5.6
			pole.top_radius = 0.055
			pole.bottom_radius = 0.075
			var mesh := _make_colored_mesh(pole, Color(0.13, 0.14, 0.15))
			mesh.position = Vector3(side * 14.0, 2.9, z_value)
			add_child(mesh)

func _prepare_city_assets() -> void:
	curb_scene = load("res://assets/models/curb_straight.glb") as PackedScene
	var pack := load("res://assets/models/midcity_buildings.glb") as PackedScene
	if pack == null:
		return
	var source := pack.instantiate() as Node3D
	source.name = "BuildingPrototypeSource"
	source.visible = false
	add_child(source)
	_collect_building_prototypes(source)

func _collect_building_prototypes(node: Node) -> void:
	for child in node.get_children():
		if child is Node3D and str(child.name).begins_with("MidCity_Commercial_") and not str(child.name).contains("Facade") and not str(child.name).contains("Walls"):
			building_prototypes.append(child as Node3D)
		else:
			_collect_building_prototypes(child)

func _create_dense_buildings() -> void:
	if building_prototypes.is_empty():
		_create_fallback_buildings()
		return
	var building_index := 0
	for z_index in range(40):
		var z_value := 57.0 - float(z_index) * 18.0
		if _near_intersection(z_value, 17.0):
			continue
		for side in [-1.0, 1.0]:
			var prototype := building_prototypes[building_index % building_prototypes.size()]
			var building := prototype.duplicate() as Node3D
			building.visible = true
			building.position = Vector3(side * 20.2, 0.25, z_value)
			building.rotation.y = PI * 0.5 if side < 0.0 else -PI * 0.5
			building.scale = Vector3.ONE * 0.88
			_prepare_static_visual(building)
			add_child(building)
			building_index += 1
	for street_z in CROSS_STREETS:
		for x_index in range(6):
			var x_value := 28.0 + float(x_index) * 18.5
			for side_x in [-1.0, 1.0]:
				for side_z in [-1.0, 1.0]:
					var prototype := building_prototypes[building_index % building_prototypes.size()]
					var building := prototype.duplicate() as Node3D
					building.visible = true
					building.position = Vector3(side_x * x_value, 0.25, street_z + side_z * 20.5)
					building.rotation.y = 0.0 if side_z < 0.0 else PI
					building.scale = Vector3.ONE * 0.88
					_prepare_static_visual(building)
					add_child(building)
					building_index += 1

func _create_fallback_buildings() -> void:
	for index in range(32):
		var z_value := 50.0 - float(index) * 22.0
		if _near_intersection(z_value, 16.0):
			continue
		for side in [-1.0, 1.0]:
			var height := 8.0 + float(index % 4) * 1.7
			_add_visual_box(Vector3(side * 20.0, height * 0.5 + 0.2, z_value), Vector3(12.0, height, 17.0), Color(0.44, 0.46, 0.48))

func _prepare_static_visual(node: Node) -> void:
	if node is Camera3D or node is Light3D or node is WorldEnvironment:
		node.queue_free()
		return
	if node is GeometryInstance3D:
		var geometry := node as GeometryInstance3D
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geometry.visibility_range_end = 0.0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface_index in range(mesh_instance.mesh.get_surface_count()):
				var source := mesh_instance.mesh.surface_get_material(surface_index)
				if source is StandardMaterial3D:
					var material := source.duplicate() as StandardMaterial3D
					material.metallic = 0.0
					material.roughness = maxf(material.roughness, 0.72)
					material.clearcoat_enabled = false
					mesh_instance.set_surface_override_material(surface_index, material)
	for child in node.get_children():
		_prepare_static_visual(child)

func _create_player() -> void:
	car = CharacterBody3D.new()
	car.name = "PlayerCar"
	car.set_script(load("res://scripts/car.gd"))
	car.position = Vector3(PLAYER_LANE_X, 0.52, 48.0)
	add_child(car)
	camera_rig = Camera3D.new()
	camera_rig.name = "SmoothCamera"
	camera_rig.set_script(load("res://scripts/camera_rig.gd"))
	add_child(camera_rig)
	camera_rig.setup(car)

func _create_traffic() -> void:
	var lanes: Array[float] = [-7.3, -3.8, 3.8, 7.3]
	for index in range(8):
		var traffic := Node3D.new()
		traffic.name = "TrafficCar_%d" % index
		traffic.set_script(load("res://scripts/traffic_car.gd"))
		add_child(traffic)
		var lane := lanes[index % lanes.size()]
		var direction := -1.0 if lane > 0.0 else 1.0
		var start_z := 30.0 - float(index) * 82.0
		traffic.configure(lane, direction, 8.5 + float(index % 4) * 1.25, start_z)

func _create_route() -> void:
	var route: Array[Vector3] = [
		Vector3(PLAYER_LANE_X, 1.0, -120.0),
		Vector3(PLAYER_LANE_X, 1.0, -300.0),
		Vector3(PLAYER_LANE_X, 1.0, -500.0),
		Vector3(62.0, 1.0, -520.0)
	]
	for index in range(route.size()):
		var area := Area3D.new()
		area.position = route[index]
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(14.0, 3.0, 5.0) if index < 3 else Vector3(5.0, 3.0, 15.0)
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
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	var top_bar := ColorRect.new()
	top_bar.color = Color(0.025, 0.055, 0.075, 0.84)
	top_bar.anchor_right = 1.0
	top_bar.anchor_bottom = 0.15
	root.add_child(top_bar)
	hud_speed = Label.new()
	hud_speed.text = "000\nkm/h"
	_set_control_rect(hud_speed, 0.025, 0.015, 0.15, 0.145)
	hud_speed.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_speed.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hud_speed.add_theme_font_size_override("font_size", 20)
	root.add_child(hud_speed)
	navigation_arrow = Label.new()
	navigation_arrow.text = "↑"
	_set_control_rect(navigation_arrow, 0.43, 0.002, 0.57, 0.10)
	navigation_arrow.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	navigation_arrow.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	navigation_arrow.add_theme_font_size_override("font_size", 35)
	root.add_child(navigation_arrow)
	hud_status = Label.new()
	hud_status.text = "168m"
	_set_control_rect(hud_status, 0.43, 0.085, 0.57, 0.145)
	hud_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_status.add_theme_font_size_override("font_size", 15)
	root.add_child(hud_status)
	var controls := Control.new()
	controls.set_script(load("res://scripts/driving_controls.gd"))
	controls.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(controls)
	controls.steer_changed.connect(func(value: float) -> void: car.set_steer(value))
	controls.action_changed.connect(func(action: String, pressed: bool) -> void: car.set_control(action, pressed))
	controls.horn_pressed.connect(func() -> void: car.play_horn())
	controls.camera_pressed.connect(func() -> void: camera_rig.cycle_mode())
	controls.gear_selected.connect(func(value: String) -> void: car.set_gear(value))

func _set_control_rect(control: Control, left: float, top: float, right: float, bottom: float) -> void:
	control.anchor_left = left
	control.anchor_top = top
	control.anchor_right = right
	control.anchor_bottom = bottom
	control.offset_left = 0.0
	control.offset_top = 0.0
	control.offset_right = 0.0
	control.offset_bottom = 0.0

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
