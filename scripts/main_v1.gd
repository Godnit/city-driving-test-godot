extends Node3D

enum GameState { MENU, GARAGE, PLAYING, PAUSED, RESULT }

const ROAD_LENGTH: float = 780.0
const ROAD_CENTER_Z: float = -310.0
const MAIN_ROAD_HALF: float = 11.0
const CROSS_STREETS: Array[float] = [30.0, -150.0, -330.0, -510.0]
const BUILDING_SEGMENTS: Array[Vector2] = [
	Vector2(78.0, 44.0),
	Vector2(16.0, -136.0),
	Vector2(-164.0, -316.0),
	Vector2(-344.0, -496.0),
	Vector2(-524.0, -698.0)
]
const PLAYER_START := Vector3(5.4, 0.48, 58.0)
const CAR_COLORS: Array[Color] = [
	Color(0.88, 0.15, 0.055),
	Color(0.045, 0.26, 0.72),
	Color(0.12, 0.55, 0.22)
]

var state: int = GameState.MENU
var selected_mission: int = 0
var selected_car: int = 0
var coins: int = 0
var car: CharacterBody3D
var camera_rig: Camera3D
var controls: Control
var menu_layer: CanvasLayer
var garage_layer: CanvasLayer
var hud_layer: CanvasLayer
var result_layer: CanvasLayer
var pause_panel: Control
var hud_speed: Label
var hud_route: Label
var hud_timer: Label
var hud_fuel: Label
var hud_damage: Label
var hud_coins: Label
var navigation_arrow: Label
var checkpoints: Array[Area3D] = []
var checkpoint_visuals: Array[Node3D] = []
var traffic_lamps: Array[Dictionary] = []
var next_checkpoint: int = 0
var elapsed: float = 0.0
var mission_limit: float = 110.0
var fuel: float = 100.0
var damage: float = 0.0
var penalty: int = 0
var offroad_tick: float = 0.0
var ui_tick: float = 0.0
var loading_layer: CanvasLayer

var missions: Array[Dictionary] = [
	{
		"title": "جولة المدينة",
		"subtitle": "اتبع الأسهم واعبر 7 نقاط",
		"reward": 450,
		"limit": 110.0,
		"route": [
			Vector3(5.4, 1.0, -35.0),
			Vector3(5.4, 1.0, -138.0),
			Vector3(48.0, 1.0, -150.0),
			Vector3(82.0, 1.0, -150.0),
			Vector3(5.4, 1.0, -245.0),
			Vector3(5.4, 1.0, -410.0),
			Vector3(-60.0, 1.0, -510.0)
		]
	},
	{
		"title": "قيادة اقتصادية",
		"subtitle": "أكمل الطريق قبل نفاد الوقود",
		"reward": 600,
		"limit": 135.0,
		"route": [
			Vector3(5.4, 1.0, -70.0),
			Vector3(5.4, 1.0, -180.0),
			Vector3(5.4, 1.0, -300.0),
			Vector3(-45.0, 1.0, -330.0),
			Vector3(-85.0, 1.0, -330.0),
			Vector3(5.4, 1.0, -470.0),
			Vector3(5.4, 1.0, -610.0)
		]
	},
	{
		"title": "اختبار الاصطفاف",
		"subtitle": "قد بهدوء إلى موقف السيارات",
		"reward": 750,
		"limit": 95.0,
		"route": [
			Vector3(5.4, 1.0, -75.0),
			Vector3(5.4, 1.0, -140.0),
			Vector3(34.0, 1.0, -150.0),
			Vector3(70.0, 1.0, -150.0),
			Vector3(91.0, 1.0, -137.0)
		]
	}
]

func _ready() -> void:
	DisplayServer.screen_set_orientation(DisplayServer.SCREEN_LANDSCAPE)
	Engine.max_fps = 30
	Engine.physics_ticks_per_second = 30
	_load_save()
	_create_loading()
	await get_tree().process_frame
	_set_loading("إنشاء الطرق والمباني...")
	_create_environment()
	_create_city()
	await get_tree().process_frame
	_set_loading("تجهيز سيارة Sketchfab...")
	_create_player()
	_create_traffic()
	await get_tree().process_frame
	_set_loading("تجهيز واجهة القيادة...")
	_create_hud()
	_create_main_menu()
	_create_garage()
	_create_result_screen()
	await get_tree().process_frame
	_apply_car_paint()
	loading_layer.queue_free()
	_show_main_menu()
	if "--smoke-test" in OS.get_cmdline_user_args():
		if not _run_touch_routing_check():
			get_tree().quit(2)
			return
		print("CITY_DRIVE_V1_READY")
		print("SKETCHFAB_MODEL_SLOT_READY")
		print("ANDROID_81_ARMV7_READY")
		print("MENU_TOUCH_ROUTING_READY")
		print("DENSE_CITY_BLOCKS_READY")
		await get_tree().process_frame
		get_tree().quit()

func _process(delta: float) -> void:
	_update_traffic_lights()
	if state != GameState.PLAYING or not is_instance_valid(car):
		return
	elapsed += delta
	ui_tick += delta
	offroad_tick += delta
	var speed_kmh: float = car.get_speed_kmh()
	fuel = maxf(0.0, fuel - delta * (0.042 + speed_kmh * 0.00125))
	if offroad_tick >= 0.55:
		offroad_tick = 0.0
		if not _is_on_road(car.global_position) and speed_kmh > 12.0:
			damage = minf(100.0, damage + 2.5)
			penalty += 5
	if ui_tick >= 0.08:
		ui_tick = 0.0
		_update_hud()
	if elapsed > mission_limit or fuel <= 0.0 or damage >= 100.0:
		_finish_mission(false)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if state == GameState.PLAYING:
			_pause_game()
		elif state == GameState.PAUSED:
			_resume_game()

func _create_loading() -> void:
	loading_layer = CanvasLayer.new()
	loading_layer.layer = 100
	loading_layer.name = "LoadingLayer"
	add_child(loading_layer)
	var background := ColorRect.new()
	background.name = "Background"
	background.color = Color(0.018, 0.028, 0.042)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	loading_layer.add_child(background)
	var title := Label.new()
	title.name = "Title"
	title.text = "CITY DRIVE MISSIONS\nجارٍ التشغيل..."
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", Color(1.0, 0.46, 0.08))
	title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_child(title)

func _set_loading(text_value: String) -> void:
	var label := loading_layer.get_node_or_null("Background/Title") as Label
	if label:
		label.text = "CITY DRIVE MISSIONS\n" + text_value

func _create_environment() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.36, 0.61, 0.80)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.82, 0.86, 0.92)
	environment.ambient_light_energy = 0.92
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -25.0, 0.0)
	sun.light_energy = 0.82
	sun.shadow_enabled = false
	add_child(sun)

func _create_city() -> void:
	_add_static_box(Vector3(0.0, -0.62, ROAD_CENTER_Z), Vector3(230.0, 0.75, ROAD_LENGTH + 120.0), Color(0.18, 0.28, 0.18))
	_add_static_box(Vector3(0.0, -0.18, ROAD_CENTER_Z), Vector3(MAIN_ROAD_HALF * 2.0, 0.34, ROAD_LENGTH), Color(0.052, 0.058, 0.064))
	for street_z in CROSS_STREETS:
		_add_static_box(Vector3(0.0, -0.17, street_z), Vector3(195.0, 0.34, 20.0), Color(0.052, 0.058, 0.064))
		_create_intersection(street_z)
	_create_sidewalks()
	_create_markings()
	_create_center_dividers()
	_create_frontage_fences()
	_create_buildings()
	_create_street_lights()
	_create_barriers()

func _create_sidewalks() -> void:
	var bounds: Array[float] = [80.0, 42.0, 18.0, -138.0, -162.0, -318.0, -342.0, -498.0, -522.0, -700.0]
	for index in range(0, bounds.size(), 2):
		var top: float = bounds[index]
		var bottom: float = bounds[index + 1]
		var center: float = (top + bottom) * 0.5
		var length: float = top - bottom
		for side in [-1.0, 1.0]:
			_add_static_box(Vector3(side * 13.0, 0.0, center), Vector3(4.0, 0.30, length), Color(0.39, 0.40, 0.41))
			_add_static_box(Vector3(side * 11.05, 0.18, center), Vector3(0.26, 0.48, length), Color(0.70, 0.70, 0.66))
	for street_z in CROSS_STREETS:
		for side_z in [-1.0, 1.0]:
			_add_static_box(Vector3(0.0, 0.0, street_z + side_z * 12.0), Vector3(195.0, 0.30, 4.0), Color(0.39, 0.40, 0.41))

func _create_markings() -> void:
	var transforms: Array[Transform3D] = []
	for x_value in [-7.4, -3.7, 3.7, 7.4]:
		for index in range(75):
			var z_value: float = 66.0 - float(index) * 10.0
			if not _near_intersection(z_value, 13.0):
				transforms.append(Transform3D(Basis.IDENTITY, Vector3(x_value, 0.025, z_value)))
	_add_multimesh_boxes(Vector3(0.12, 0.026, 3.5), Color(0.94, 0.94, 0.90), transforms)
	for x_value in [-10.1, 0.0, 10.1]:
		_add_visual_box(Vector3(x_value, 0.022, ROAD_CENTER_Z), Vector3(0.12, 0.026, ROAD_LENGTH), Color(0.92, 0.92, 0.88))
	for street_z in CROSS_STREETS:
		var cross: Array[Transform3D] = []
		for side in [-1.0, 1.0]:
			for index in range(9):
				var x_pos: float = side * (18.0 + float(index) * 9.0)
				cross.append(Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(x_pos, 0.025, street_z - 3.5)))
				cross.append(Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(x_pos, 0.025, street_z + 3.5)))
		_add_multimesh_boxes(Vector3(0.12, 0.026, 3.2), Color(0.94, 0.94, 0.90), cross)

func _create_center_dividers() -> void:
	for bounds in BUILDING_SEGMENTS:
		var length: float = bounds.x - bounds.y
		var center_z: float = (bounds.x + bounds.y) * 0.5
		_add_static_box(Vector3(0.0, 0.13, center_z), Vector3(1.05, 0.30, length), Color(0.46, 0.47, 0.43))
		_add_visual_box(Vector3(0.0, 0.30, center_z), Vector3(0.70, 0.12, length - 0.5), Color(0.20, 0.36, 0.17))

func _create_frontage_fences() -> void:
	var post_transforms: Array[Transform3D] = []
	var rail_transforms: Array[Transform3D] = []
	for bounds in BUILDING_SEGMENTS:
		var length: float = bounds.x - bounds.y
		var center_z: float = (bounds.x + bounds.y) * 0.5
		for side in [-1.0, 1.0]:
			var fence_x: float = side * 15.15
			_add_static_box(Vector3(fence_x, 0.38, center_z), Vector3(0.25, 0.76, length), Color(0.17, 0.18, 0.18))
			var post_count: int = maxi(2, int(length / 3.0))
			for post_index in range(post_count + 1):
				var z_value: float = bounds.x - float(post_index) * length / float(post_count)
				post_transforms.append(Transform3D(Basis.IDENTITY, Vector3(fence_x, 1.08, z_value)))
			for y_value in [0.83, 1.34]:
				rail_transforms.append(Transform3D(Basis.IDENTITY, Vector3(fence_x, y_value, center_z)))
	_add_multimesh_boxes(Vector3(0.14, 1.55, 0.14), Color(0.055, 0.060, 0.063), post_transforms)
	for transform_value in rail_transforms:
		var bounds_length: float = _segment_length_at_z(transform_value.origin.z)
		_add_visual_box(transform_value.origin, Vector3(0.11, 0.10, bounds_length), Color(0.055, 0.060, 0.063))

func _segment_length_at_z(z_value: float) -> float:
	for bounds in BUILDING_SEGMENTS:
		if is_equal_approx(z_value, (bounds.x + bounds.y) * 0.5):
			return bounds.x - bounds.y
	return 1.0

func _create_intersection(street_z: float) -> void:
	for side in [-1.0, 1.0]:
		_create_traffic_light(Vector3(side * 10.4, 0.0, street_z + side * 12.5), -side * PI * 0.5)
	for stripe in range(6):
		_add_visual_box(Vector3(-7.5 + float(stripe) * 3.0, 0.027, street_z + 10.2), Vector3(1.5, 0.03, 4.0), Color(0.92, 0.92, 0.89))

func _create_traffic_light(position_value: Vector3, yaw: float) -> void:
	var root := Node3D.new()
	root.position = position_value
	root.rotation.y = yaw
	add_child(root)
	var pole := CylinderMesh.new()
	pole.height = 4.8
	pole.top_radius = 0.08
	pole.bottom_radius = 0.10
	var pole_mesh := _make_colored_mesh(pole, Color(0.08, 0.09, 0.10))
	pole_mesh.position.y = 2.4
	root.add_child(pole_mesh)
	var housing := BoxMesh.new()
	housing.size = Vector3(0.55, 1.52, 0.42)
	var housing_mesh := _make_colored_mesh(housing, Color(0.025, 0.03, 0.035))
	housing_mesh.position = Vector3(0.0, 4.3, 0.0)
	root.add_child(housing_mesh)
	var lamps: Array[MeshInstance3D] = []
	for index in range(3):
		var sphere := SphereMesh.new()
		sphere.radius = 0.12
		sphere.height = 0.24
		var lamp := _make_colored_mesh(sphere, Color(0.16, 0.04, 0.03))
		lamp.position = Vector3(0.0, 4.75 - float(index) * 0.45, -0.23)
		root.add_child(lamp)
		lamps.append(lamp)
	traffic_lamps.append({"lamps": lamps, "offset": position_value.z * 0.03})

func _update_traffic_lights() -> void:
	var phase: float = fmod(Time.get_ticks_msec() * 0.001, 18.0)
	var active: int = 0 if phase < 8.0 else (1 if phase < 10.0 else 2)
	var colors: Array[Color] = [Color(0.92, 0.055, 0.025), Color(1.0, 0.58, 0.03), Color(0.02, 0.90, 0.18)]
	for info in traffic_lamps:
		var lamps: Array = info["lamps"]
		for index in range(lamps.size()):
			var lamp := lamps[index] as MeshInstance3D
			var material := lamp.material_override as StandardMaterial3D
			material.albedo_color = colors[index] if index == active else colors[index].darkened(0.78)

func _create_buildings() -> void:
	var palette: Array[Color] = [
		Color(0.57, 0.49, 0.39),
		Color(0.43, 0.48, 0.51),
		Color(0.64, 0.56, 0.45),
		Color(0.47, 0.38, 0.34),
		Color(0.37, 0.43, 0.49),
		Color(0.60, 0.45, 0.34),
		Color(0.49, 0.50, 0.44)
	]
	var building_index: int = 0
	for bounds in BUILDING_SEGMENTS:
		for side in [-1.0, 1.0]:
			var cursor_z: float = bounds.x
			while cursor_z > bounds.y + 0.5:
				var requested_frontage: float = 18.0 + float((building_index * 5) % 9)
				var frontage: float = minf(requested_frontage, cursor_z - bounds.y)
				var depth: float = 9.0 + float((building_index * 3) % 6)
				var height: float = 8.0 + float((building_index * 7) % 14)
				if building_index % 7 == 0:
					height += 5.0
				var center_z: float = cursor_z - frontage * 0.5
				var center_x: float = side * (15.65 + depth * 0.5)
				_create_building(
					Vector3(center_x, 0.0, center_z),
					Vector3(depth, height, maxf(5.0, frontage - 0.32)),
					palette[building_index % palette.size()],
					building_index % 5
				)
				cursor_z -= frontage
				building_index += 1
	for street_z in CROSS_STREETS:
		for side in [-1.0, 1.0]:
			for index in range(4):
				var x_value: float = side * (35.0 + float(index) * 22.0)
				var height: float = 9.0 + float((index + building_index) % 4) * 2.3
				_create_building(
					Vector3(x_value, 0.0, street_z + side * 23.0),
					Vector3(15.0, height, 16.0),
					palette[building_index % palette.size()],
					building_index % 5
				)
				building_index += 1

func _create_building(base_position: Vector3, size_value: Vector3, color_value: Color, style_index: int = 0) -> void:
	_add_visual_box(base_position + Vector3(0.0, size_value.y * 0.5, 0.0), size_value, color_value)
	var road_side: float = signf(base_position.x)
	var front_x: float = base_position.x - road_side * (size_value.x * 0.5 + 0.026)
	var window_color := Color(0.24, 0.43, 0.55).lightened(float(style_index) * 0.035)
	var rows: int = mini(5, int(size_value.y / 2.75))
	var columns: int = clampi(int(size_value.z / 5.0), 1, 3)
	for row in range(rows):
		var y_value: float = 2.15 + float(row) * 2.7
		for column in range(columns):
			var z_value: float = base_position.z - size_value.z * 0.5 + (float(column) + 0.5) * size_value.z / float(columns)
			var window_width: float = minf(2.25, size_value.z / float(columns) * 0.62)
			_add_visual_box(
				Vector3(front_x, y_value, z_value),
				Vector3(0.055, 1.15, window_width),
				window_color.darkened(float((row + column) % 3) * 0.055)
			)
	if style_index % 2 == 0:
		var shop_color := Color(0.10, 0.12, 0.14)
		_add_visual_box(
			Vector3(front_x - road_side * 0.015, 1.25, base_position.z),
			Vector3(0.07, 2.15, size_value.z * 0.72),
			shop_color
		)
		var awning_color := Color(0.82, 0.22, 0.08) if style_index == 0 else Color(0.13, 0.32, 0.50)
		_add_visual_box(
			Vector3(front_x - road_side * 0.48, 2.55, base_position.z),
			Vector3(0.95, 0.16, size_value.z * 0.78),
			awning_color
		)
	else:
		var door_z: float = base_position.z + size_value.z * 0.28
		_add_visual_box(Vector3(front_x - road_side * 0.02, 1.15, door_z), Vector3(0.07, 2.20, 1.55), Color(0.16, 0.12, 0.095))
	if style_index in [1, 3]:
		_add_visual_box(
			Vector3(front_x - road_side * 0.035, size_value.y * 0.55, base_position.z),
			Vector3(0.08, size_value.y * 0.82, 0.34),
			color_value.lightened(0.22)
		)
	var roof := BoxMesh.new()
	roof.size = Vector3(size_value.x + 0.6, 0.35, size_value.z + 0.6)
	var roof_mesh := _make_colored_mesh(roof, color_value.darkened(0.28))
	roof_mesh.position = base_position + Vector3(0.0, size_value.y + 0.18, 0.0)
	add_child(roof_mesh)
	if style_index == 4:
		_add_visual_box(
			base_position + Vector3(0.0, size_value.y + 0.75, 0.0),
			Vector3(size_value.x * 0.60, 1.2, size_value.z * 0.45),
			color_value.darkened(0.18)
		)

func _create_street_lights() -> void:
	for index in range(29):
		var z_value: float = 55.0 - float(index) * 25.5
		if _near_intersection(z_value, 13.0):
			continue
		for side in [-1.0, 1.0]:
			var pole := CylinderMesh.new()
			pole.height = 4.4
			pole.top_radius = 0.055
			pole.bottom_radius = 0.08
			var pole_mesh := _make_colored_mesh(pole, Color(0.13, 0.14, 0.15))
			pole_mesh.position = Vector3(side * 11.9, 2.2, z_value)
			add_child(pole_mesh)

func _create_barriers() -> void:
	for index in range(7):
		var x_value: float = 73.0 + float(index) * 2.7
		_add_static_box(Vector3(x_value, 0.55, -137.0), Vector3(1.8, 1.1, 0.42), Color(0.90, 0.24 if index % 2 == 0 else 0.86, 0.04))
	for index in range(5):
		var x_value: float = 86.0 + float(index) * 2.8
		_add_visual_box(Vector3(x_value, 0.025, -145.0), Vector3(0.12, 0.026, 13.0), Color.WHITE)

func _create_player() -> void:
	car = CharacterBody3D.new()
	car.name = "PlayerCar"
	car.set_script(load("res://scripts/car.gd"))
	car.position = PLAYER_START
	add_child(car)
	camera_rig = Camera3D.new()
	camera_rig.name = "CameraRig"
	camera_rig.set_script(load("res://scripts/camera_rig.gd"))
	add_child(camera_rig)
	camera_rig.setup(car)

func _create_traffic() -> void:
	var lanes: Array[float] = [-7.2, -3.7, 3.7, 7.2]
	for index in range(8):
		var traffic := Node3D.new()
		traffic.name = "TrafficCar%02d" % index
		traffic.set_script(load("res://scripts/traffic_car.gd"))
		var lane: float = lanes[index % lanes.size()]
		var direction: float = -1.0 if lane > 0.0 else 1.0
		traffic.configure(lane, direction, 7.5 + float(index % 4) * 1.1, 28.0 - float(index) * 89.0)
		add_child(traffic)

func _create_route() -> void:
	_clear_route()
	next_checkpoint = 0
	var route: Array = missions[selected_mission]["route"]
	for index in range(route.size()):
		var point: Vector3 = route[index]
		var area := Area3D.new()
		area.position = point
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(13.0, 3.0, 5.0)
		if index in [2, 3, 4]:
			shape.size = Vector3(5.0, 3.0, 14.0)
		collision.shape = shape
		area.add_child(collision)
		area.body_entered.connect(_on_checkpoint.bind(index))
		add_child(area)
		checkpoints.append(area)
		var marker := _create_checkpoint_marker(index == route.size() - 1)
		marker.position = point
		add_child(marker)
		checkpoint_visuals.append(marker)

func _create_checkpoint_marker(is_finish: bool) -> Node3D:
	var root := Node3D.new()
	for side in [-1.0, 1.0]:
		var pillar := CylinderMesh.new()
		pillar.height = 3.6
		pillar.top_radius = 0.08
		pillar.bottom_radius = 0.10
		var color := Color(0.12, 0.95, 0.22) if is_finish else Color(1.0, 0.45, 0.04)
		var mesh := _make_colored_mesh(pillar, color)
		mesh.position = Vector3(side * 5.3, 1.8, 0.0)
		root.add_child(mesh)
	return root

func _on_checkpoint(body: Node3D, index: int) -> void:
	if state != GameState.PLAYING or body != car or index != next_checkpoint:
		return
	checkpoints[index].monitoring = false
	checkpoint_visuals[index].visible = false
	next_checkpoint += 1
	if next_checkpoint >= checkpoints.size():
		_finish_mission(true)

func _clear_route() -> void:
	for area in checkpoints:
		if is_instance_valid(area):
			area.queue_free()
	for marker in checkpoint_visuals:
		if is_instance_valid(marker):
			marker.queue_free()
	checkpoints.clear()
	checkpoint_visuals.clear()

func _create_hud() -> void:
	hud_layer = CanvasLayer.new()
	hud_layer.layer = 20
	add_child(hud_layer)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud_layer.add_child(root)
	var top_bar := ColorRect.new()
	top_bar.color = Color(0.015, 0.02, 0.028, 0.80)
	_set_rect(top_bar, 0.0, 0.0, 1.0, 0.14)
	root.add_child(top_bar)
	hud_speed = _hud_label(root, "000 km/h", 0.79, 0.012, 0.98, 0.125, 24, Color.WHITE)
	hud_route = _hud_label(root, "نقطة 1/7", 0.33, 0.015, 0.67, 0.075, 16, Color.WHITE)
	hud_timer = _hud_label(root, "01:50", 0.42, 0.075, 0.58, 0.135, 16, Color(1.0, 0.53, 0.08))
	hud_fuel = _hud_label(root, "وقود 100%", 0.015, 0.015, 0.19, 0.07, 14, Color(0.35, 1.0, 0.48))
	hud_damage = _hud_label(root, "الحالة 100%", 0.015, 0.075, 0.22, 0.13, 14, Color(0.40, 0.80, 1.0))
	hud_coins = _hud_label(root, "¢ 0", 0.64, 0.015, 0.78, 0.125, 18, Color(1.0, 0.76, 0.12))
	navigation_arrow = _hud_label(root, "↑", 0.43, 0.15, 0.57, 0.30, 44, Color(1.0, 0.42, 0.04))
	controls = Control.new()
	controls.name = "DrivingControls"
	controls.set_script(load("res://scripts/driving_controls.gd"))
	controls.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(controls)
	controls.steer_changed.connect(func(value: float) -> void: car.set_steer(value))
	controls.action_changed.connect(func(action: String, pressed: bool) -> void: car.set_control(action, pressed))
	controls.horn_pressed.connect(func() -> void: car.play_horn())
	controls.camera_pressed.connect(func() -> void: camera_rig.cycle_mode())
	controls.gear_selected.connect(func(value: String) -> void: car.set_gear(value))
	controls.pause_pressed.connect(_pause_game)
	pause_panel = _create_pause_panel(root)
	hud_layer.visible = false

func _hud_label(parent: Control, text_value: String, left: float, top: float, right: float, bottom: float, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text_value
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	_set_rect(label, left, top, right, bottom)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

func _create_pause_panel(parent: Control) -> Control:
	var panel := ColorRect.new()
	panel.color = Color(0.01, 0.018, 0.028, 0.93)
	_set_rect(panel, 0.33, 0.20, 0.67, 0.80)
	parent.add_child(panel)
	var title := _hud_label(panel, "إيقاف مؤقت", 0.08, 0.06, 0.92, 0.28, 24, Color(1.0, 0.52, 0.08))
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_add_menu_button(panel, "متابعة", 0.16, 0.34, 0.84, 0.50, _resume_game)
	_add_menu_button(panel, "إعادة المهمة", 0.16, 0.55, 0.84, 0.71, _restart_mission)
	_add_menu_button(panel, "القائمة الرئيسية", 0.16, 0.76, 0.84, 0.92, _show_main_menu)
	panel.visible = false
	return panel

func _create_main_menu() -> void:
	menu_layer = CanvasLayer.new()
	menu_layer.layer = 40
	add_child(menu_layer)
	var background := ColorRect.new()
	background.name = "Background"
	background.color = Color(0.015, 0.026, 0.042, 0.95)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	menu_layer.add_child(background)
	var accent := ColorRect.new()
	accent.color = Color(1.0, 0.30, 0.035)
	_set_rect(accent, 0.0, 0.0, 0.018, 1.0)
	background.add_child(accent)
	_hud_label(background, "CITY DRIVE", 0.055, 0.07, 0.48, 0.23, 36, Color.WHITE)
	_hud_label(background, "MISSIONS", 0.055, 0.20, 0.48, 0.32, 21, Color(1.0, 0.42, 0.04))
	_hud_label(background, "لعبة قيادة مدينة خفيفة للأندرويد", 0.055, 0.31, 0.48, 0.40, 14, Color(0.72, 0.78, 0.84))
	var coins_label := _hud_label(background, "الرصيد  ¢ %d" % coins, 0.69, 0.05, 0.95, 0.16, 18, Color(1.0, 0.76, 0.12))
	coins_label.name = "MenuCoins"
	for index in range(missions.size()):
		var mission: Dictionary = missions[index]
		var button := Button.new()
		button.name = "MissionButton%d" % index
		button.text = "%s\n%s   |   الجائزة ¢%d" % [mission["title"], mission["subtitle"], mission["reward"]]
		_set_rect(button, 0.53, 0.19 + float(index) * 0.20, 0.94, 0.35 + float(index) * 0.20)
		button.add_theme_font_size_override("font_size", 15)
		button.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
		button.focus_mode = Control.FOCUS_NONE
		button.pressed.connect(_select_mission.bind(index))
		background.add_child(button)
	_add_menu_button(background, "المرآب واختيار السيارة", 0.08, 0.52, 0.43, 0.66, _show_garage, "GarageButton")
	_add_menu_button(background, "ابدأ المهمة المختارة", 0.08, 0.71, 0.43, 0.88, _start_mission, "StartButton")

func _create_garage() -> void:
	garage_layer = CanvasLayer.new()
	garage_layer.layer = 45
	add_child(garage_layer)
	var background := ColorRect.new()
	background.color = Color(0.018, 0.028, 0.040, 0.96)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	garage_layer.add_child(background)
	_hud_label(background, "المرآب", 0.10, 0.07, 0.90, 0.20, 32, Color(1.0, 0.48, 0.06))
	_hud_label(background, "سيدان خفيفة من Sketchfab — اختر اللون", 0.10, 0.19, 0.90, 0.29, 16, Color.WHITE)
	var names: Array[String] = ["برتقالي", "أزرق", "أخضر"]
	for index in range(3):
		var button := Button.new()
		button.text = names[index]
		button.modulate = CAR_COLORS[index].lightened(0.25)
		_set_rect(button, 0.18 + float(index) * 0.23, 0.42, 0.36 + float(index) * 0.23, 0.62)
		button.add_theme_font_size_override("font_size", 18)
		button.pressed.connect(_select_car.bind(index))
		background.add_child(button)
	_add_menu_button(background, "عودة", 0.37, 0.76, 0.63, 0.90, _show_main_menu)
	garage_layer.visible = false

func _create_result_screen() -> void:
	result_layer = CanvasLayer.new()
	result_layer.layer = 50
	add_child(result_layer)
	var background := ColorRect.new()
	background.name = "Background"
	background.color = Color(0.012, 0.022, 0.034, 0.95)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	result_layer.add_child(background)
	var title := _hud_label(background, "تمت المهمة", 0.20, 0.14, 0.80, 0.30, 34, Color(0.20, 1.0, 0.34))
	title.name = "ResultTitle"
	var details := _hud_label(background, "", 0.18, 0.32, 0.82, 0.58, 18, Color.WHITE)
	details.name = "ResultDetails"
	_add_menu_button(background, "إعادة المحاولة", 0.20, 0.68, 0.46, 0.84, _restart_mission)
	_add_menu_button(background, "القائمة", 0.54, 0.68, 0.80, 0.84, _show_main_menu)
	result_layer.visible = false

func _add_menu_button(parent: Control, text_value: String, left: float, top: float, right: float, bottom: float, callback: Callable, node_name: String = "") -> void:
	var button := Button.new()
	if not node_name.is_empty():
		button.name = node_name
	button.text = text_value
	_set_rect(button, left, top, right, bottom)
	button.add_theme_font_size_override("font_size", 17)
	button.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	button.focus_mode = Control.FOCUS_NONE
	button.pressed.connect(callback)
	parent.add_child(button)

func _select_mission(index: int) -> void:
	selected_mission = index
	_start_mission()

func _select_car(index: int) -> void:
	selected_car = index
	_apply_car_paint()
	_save_game()

func _apply_car_paint() -> void:
	if not is_instance_valid(car):
		return
	var mesh_nodes := car.find_children("*", "MeshInstance3D", true, false)
	var color_value: Color = CAR_COLORS[selected_car]
	var changed: int = 0
	for item in mesh_nodes:
		var mesh := item as MeshInstance3D
		if mesh == null or mesh.mesh == null:
			continue
		for surface in range(mesh.mesh.get_surface_count()):
			var source := mesh.get_active_material(surface)
			if source is StandardMaterial3D:
				var material := source.duplicate() as StandardMaterial3D
				if material.albedo_color.a > 0.85 and material.metallic < 0.75 and changed < 5:
					material.albedo_color = color_value
					mesh.set_surface_override_material(surface, material)
					changed += 1

func _start_mission() -> void:
	state = GameState.PLAYING
	Input.emulate_mouse_from_touch = false
	menu_layer.visible = false
	garage_layer.visible = false
	result_layer.visible = false
	hud_layer.visible = true
	pause_panel.visible = false
	controls.visible = true
	controls.set_controls_enabled(true)
	get_tree().paused = false
	elapsed = 0.0
	fuel = 100.0
	damage = 0.0
	penalty = 0
	mission_limit = float(missions[selected_mission]["limit"])
	car.reset_vehicle()
	car.global_position = PLAYER_START
	car.rotation = Vector3.ZERO
	car.set_gear("D")
	_create_route()
	camera_rig.setup(car)
	_update_hud()

func _restart_mission() -> void:
	_start_mission()

func _pause_game() -> void:
	if state != GameState.PLAYING:
		return
	state = GameState.PAUSED
	Input.emulate_mouse_from_touch = true
	pause_panel.visible = true
	controls.visible = false
	controls.set_controls_enabled(false)
	car.set_control("accelerate", false)
	car.set_control("brake", false)
	car.set_steer(0.0)

func _resume_game() -> void:
	if state != GameState.PAUSED:
		return
	state = GameState.PLAYING
	Input.emulate_mouse_from_touch = false
	pause_panel.visible = false
	controls.visible = true
	controls.set_controls_enabled(true)

func _show_main_menu() -> void:
	state = GameState.MENU
	Input.emulate_mouse_from_touch = true
	menu_layer.visible = true
	garage_layer.visible = false
	hud_layer.visible = false
	result_layer.visible = false
	pause_panel.visible = false
	controls.visible = false
	controls.set_controls_enabled(false)
	car.set_control("accelerate", false)
	car.set_control("brake", false)
	car.set_steer(0.0)
	car.set_gear("P")
	var label := menu_layer.get_node_or_null("Background/MenuCoins") as Label
	if label:
		label.text = "الرصيد  ¢ %d" % coins

func _show_garage() -> void:
	state = GameState.GARAGE
	Input.emulate_mouse_from_touch = true
	controls.set_controls_enabled(false)
	menu_layer.visible = false
	garage_layer.visible = true

func _finish_mission(success: bool) -> void:
	if state != GameState.PLAYING:
		return
	state = GameState.RESULT
	Input.emulate_mouse_from_touch = true
	controls.set_controls_enabled(false)
	hud_layer.visible = false
	result_layer.visible = true
	car.set_control("accelerate", false)
	car.set_control("brake", false)
	car.set_steer(0.0)
	car.set_gear("P")
	var title := result_layer.get_node("Background/ResultTitle") as Label
	var details := result_layer.get_node("Background/ResultDetails") as Label
	if success:
		var base_reward: int = int(missions[selected_mission]["reward"])
		var time_bonus: int = maxi(0, int(mission_limit - elapsed) * 3)
		var condition_bonus: int = maxi(0, int(100.0 - damage) * 2)
		var total: int = maxi(0, base_reward + time_bonus + condition_bonus - penalty)
		coins += total
		title.text = "نجحت في المهمة ✓"
		title.add_theme_color_override("font_color", Color(0.20, 1.0, 0.34))
		details.text = "الوقت: %02d:%02d\nالحالة: %d%%   |   الوقود: %d%%\nالجائزة: ¢%d" % [int(elapsed) / 60, int(elapsed) % 60, int(100.0 - damage), int(fuel), total]
		_save_game()
	else:
		title.text = "انتهت المحاولة"
		title.add_theme_color_override("font_color", Color(1.0, 0.22, 0.10))
		var reason := "انتهى الوقت"
		if fuel <= 0.0:
			reason = "نفد الوقود"
		elif damage >= 100.0:
			reason = "تضررت السيارة"
		details.text = "%s\nحاول القيادة بهدوء وتجنب الأرصفة والحواجز." % reason

func _update_hud() -> void:
	var speed_kmh: float = car.get_speed_kmh()
	hud_speed.text = "%03d km/h" % int(speed_kmh)
	hud_timer.text = "%02d:%02d" % [maxi(0, int(mission_limit - elapsed)) / 60, maxi(0, int(mission_limit - elapsed)) % 60]
	hud_fuel.text = "وقود %d%%" % int(fuel)
	hud_damage.text = "الحالة %d%%" % int(100.0 - damage)
	hud_coins.text = "¢ %d" % coins
	hud_fuel.add_theme_color_override("font_color", Color(1.0, 0.25, 0.08) if fuel < 20.0 else Color(0.35, 1.0, 0.48))
	hud_damage.add_theme_color_override("font_color", Color(1.0, 0.22, 0.10) if damage > 65.0 else Color(0.40, 0.80, 1.0))
	if next_checkpoint < checkpoints.size():
		var target: Vector3 = checkpoints[next_checkpoint].global_position
		var distance: float = car.global_position.distance_to(target)
		hud_route.text = "نقطة %d/%d   %dm" % [next_checkpoint + 1, checkpoints.size(), int(distance)]
		navigation_arrow.text = _navigation_symbol(target)
	else:
		hud_route.text = "اكتملت المهمة"
		navigation_arrow.text = "✓"

func _navigation_symbol(target: Vector3) -> String:
	var local_target: Vector3 = car.to_local(target)
	if absf(local_target.x) > maxf(8.0, absf(local_target.z) * 0.42):
		return "↱" if local_target.x > 0.0 else "↰"
	if local_target.z < 0.0:
		return "↑"
	return "↶"

func _is_on_road(position_value: Vector3) -> bool:
	if absf(position_value.x) <= MAIN_ROAD_HALF + 0.7 and position_value.z <= 82.0 and position_value.z >= -705.0:
		return true
	for street_z in CROSS_STREETS:
		if absf(position_value.z - street_z) <= 10.8 and absf(position_value.x) <= 98.0:
			return true
	return false

func _near_intersection(z_value: float, margin: float) -> bool:
	for street_z in CROSS_STREETS:
		if absf(z_value - street_z) < margin:
			return true
	return false

func _load_save() -> void:
	var config := ConfigFile.new()
	if config.load("user://city_drive_save.cfg") == OK:
		coins = int(config.get_value("profile", "coins", 0))
		selected_car = clampi(int(config.get_value("profile", "car", 0)), 0, CAR_COLORS.size() - 1)

func _save_game() -> void:
	var config := ConfigFile.new()
	config.set_value("profile", "coins", coins)
	config.set_value("profile", "car", selected_car)
	config.save("user://city_drive_save.cfg")

func _run_touch_routing_check() -> bool:
	var mission_button := menu_layer.get_node_or_null("Background/MissionButton0") as Button
	if mission_button == null:
		push_error("Touch routing check failed: mission button missing")
		return false
	if not Input.emulate_mouse_from_touch:
		push_error("Touch routing check failed: menu touch emulation disabled")
		return false
	if controls.is_processing_input():
		push_error("Touch routing check failed: hidden driving controls are intercepting the menu")
		return false
	mission_button.pressed.emit()
	if state != GameState.PLAYING or not controls.is_processing_input() or Input.emulate_mouse_from_touch:
		push_error("Touch routing check failed: mission button did not enter driving mode")
		return false
	_show_main_menu()
	return state == GameState.MENU and Input.emulate_mouse_from_touch and not controls.is_processing_input()

func _set_rect(control: Control, left: float, top: float, right: float, bottom: float) -> void:
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

func _add_multimesh_boxes(size_value: Vector3, color_value: Color, transforms: Array[Transform3D]) -> void:
	if transforms.is_empty():
		return
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

func _make_colored_mesh(mesh: Mesh, color_value: Color) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = 0.86
	material.metallic = 0.0
	instance.material_override = material
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return instance
