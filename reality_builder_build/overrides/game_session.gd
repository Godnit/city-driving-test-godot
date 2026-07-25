extends Node3D

signal return_to_menu_requested

const PieceLibraryScript = preload("res://scripts/piece_library.gd")
const BlockWorldScript = preload("res://scripts/block_world.gd")
const PlayerScript = preload("res://scripts/player.gd")
const MobileHUDScript = preload("res://scripts/mobile_hud.gd")
const PlanningSystemScript = preload("res://scripts/planning_system.gd")

var world_id: String = ""
var world_name: String = "عالم"
var world_template: String = "empty"
var world_save_path: String = "user://reality_builder_world.json"

var piece_library
var world
var player
var hud
var autosave_timer: Timer
var player_state_timer: Timer
var player_state_path: String = ""
var planning_system
var environment_node: WorldEnvironment
var environment: Environment
var sun: DirectionalLight3D
var sky_material: ProceduralSkyMaterial
var current_lighting_mode: String = "day"
const DISPLAY_SETTINGS_PATH := "user://reality_builder_display.cfg"
var mobile_runtime: bool = false
var low_end_mobile: bool = false
var loading_layer: CanvasLayer
var loading_label: Label


func _ready() -> void:
	mobile_runtime = OS.has_feature("mobile") or OS.get_name() == "Android"
	# أجهزة Android القديمة قد تتوقف عندما تُنشأ البيئة والواجهة والقطع في إطار واحد.
	# نستخدم إعدادًا خفيفًا لكل الهواتف ونقسّم التحميل على عدة إطارات.
	low_end_mobile = mobile_runtime
	if mobile_runtime:
		Engine.max_fps = 30
	_show_loading_screen("جاري تجهيز العالم…")
	await get_tree().process_frame

	_update_loading_text("جاري تجهيز الإضاءة…")
	_setup_environment()
	await get_tree().process_frame

	_update_loading_text("جاري تحميل قطع البناء…")
	_setup_piece_library()
	await get_tree().process_frame

	_update_loading_text("جاري إنشاء الأرض والعالم…")
	_setup_world()
	await get_tree().process_frame

	_update_loading_text("جاري تجهيز اللاعب والكاميرا…")
	_setup_player()
	await get_tree().process_frame

	_update_loading_text("جاري تجهيز أزرار التحكم…")
	_setup_hud()
	await get_tree().process_frame

	_update_loading_text("جاري تجهيز نظام التخطيط…")
	_setup_planning_system()
	_setup_autosave()
	await get_tree().process_frame
	_hide_loading_screen()


func _show_loading_screen(message: String) -> void:
	loading_layer = CanvasLayer.new()
	loading_layer.name = "WorldLoadingLayer"
	loading_layer.layer = 10000
	add_child(loading_layer)
	var background := ColorRect.new()
	background.color = Color("0b1d24")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_STOP
	loading_layer.add_child(background)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(420, 150)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 16)
	panel.add_child(box)
	var title := Label.new()
	title.text = "REALITY BUILDER"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 30)
	title.add_theme_color_override("font_color", Color("f4e5b7"))
	box.add_child(title)
	loading_label = Label.new()
	loading_label.text = message
	loading_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	loading_label.add_theme_font_size_override("font_size", 21)
	loading_label.add_theme_color_override("font_color", Color.WHITE)
	box.add_child(loading_label)


func _update_loading_text(message: String) -> void:
	if is_instance_valid(loading_label):
		loading_label.text = message


func _hide_loading_screen() -> void:
	if is_instance_valid(loading_layer):
		loading_layer.queue_free()
	loading_layer = null
	loading_label = null


func _setup_environment() -> void:
	environment_node = WorldEnvironment.new()
	environment_node.name = "WorldEnvironment"
	environment = Environment.new()
	# الخلفية اللونية أخف كثيرًا من السماء الإجرائية على معالجات الرسوم القديمة.
	environment.background_mode = Environment.BG_COLOR if low_end_mobile else Environment.BG_SKY
	environment.background_color = Color("78a8bf")
	var sky := Sky.new()
	sky_material = ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("397fab")
	sky_material.sky_horizon_color = Color("b8d8e6")
	sky_material.ground_horizon_color = Color("b8c5aa")
	sky_material.ground_bottom_color = Color("7d8c68")
	sky_material.sun_angle_max = 22.0
	sky_material.sun_curve = 0.12
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR if low_end_mobile else Environment.AMBIENT_SOURCE_SKY
	if low_end_mobile:
		environment.ambient_light_color = Color("c7d9df")
		environment.ambient_light_energy = 0.72
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	# تقليل احتراق الألوان وإظهار حدود الأحجار الفاتحة بوضوح أكبر.
	environment.set("tonemap_exposure", 0.95)
	environment.set("tonemap_white", 1.45)
	environment.set("adjustment_enabled", true)
	environment.set("adjustment_brightness", 0.98)
	environment.set("adjustment_contrast", 1.08)
	environment.set("adjustment_saturation", 0.98)
	environment.set("ssao_enabled", not mobile_runtime)
	environment.set("ssao_radius", 1.25)
	environment.set("ssao_intensity", 1.35)
	environment.set("ssao_power", 1.25)
	environment_node.environment = environment
	add_child(environment_node)

	sun = DirectionalLight3D.new()
	sun.name = "MainSun"
	sun.shadow_enabled = not low_end_mobile
	sun.directional_shadow_max_distance = 48.0 if mobile_runtime else 150.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if mobile_runtime else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.set("shadow_opacity", 0.86)
	sun.set("shadow_bias", 0.035)
	sun.set("shadow_normal_bias", 0.75)
	add_child(sun)

	_load_lighting_preference()
	_apply_lighting_mode(current_lighting_mode, false)


func _setup_piece_library() -> void:
	piece_library = PieceLibraryScript.new()
	piece_library.load_or_create_library()


func _setup_world() -> void:
	world = BlockWorldScript.new()
	world.name = "BlockWorld"
	world.piece_library = piece_library
	world.set_save_path(world_save_path)
	add_child(world)
	world.load_or_create_world(world_template)


func _setup_player() -> void:
	player = PlayerScript.new()
	player.name = "Player"
	player.world = world
	add_child(player)
	player_state_path = "%s.player_state.json" % world_save_path
	player.global_position = world.get_safe_spawn_position()
	_load_player_state()


func _setup_hud() -> void:
	hud = MobileHUDScript.new()
	hud.name = "HUD"
	hud.piece_library = piece_library
	add_child(hud)
	player.set_hud(hud)
	hud.set_world_name(world_name)
	hud.set_world_template(world_template)
	hud.save_requested.connect(_save_world)
	hud.reset_requested.connect(_reset_world)
	hud.menu_requested.connect(_return_to_menu)
	hud.lighting_mode_changed.connect(_on_lighting_mode_changed)
	hud.set_lighting_mode(current_lighting_mode)


func _setup_planning_system() -> void:
	planning_system = PlanningSystemScript.new()
	planning_system.name = "PlanningSystem"
	planning_system.configure(world, player, hud, piece_library, world_save_path, world_template)
	add_child(planning_system)
	hud.planning_requested.connect(planning_system.open_planner)
	hud.missions_requested.connect(planning_system.open_mission_gallery)
	planning_system.call_deferred("start_initial_flow")


func _setup_autosave() -> void:
	autosave_timer = Timer.new()
	autosave_timer.wait_time = 4.0
	autosave_timer.one_shot = true
	autosave_timer.timeout.connect(_save_world_silent)
	add_child(autosave_timer)
	world.world_changed.connect(_queue_autosave)

	player_state_timer = Timer.new()
	player_state_timer.wait_time = 3.0
	player_state_timer.one_shot = false
	player_state_timer.timeout.connect(_save_player_state)
	add_child(player_state_timer)
	player_state_timer.start()


func _queue_autosave() -> void:
	autosave_timer.start()


func _save_world() -> void:
	_save_world_silent()
	if hud:
		hud.show_message("تم حفظ عالم: %s" % world_name)


func _save_world_silent() -> void:
	if world:
		world.save_world()
	if piece_library:
		piece_library.save_library()
	if planning_system:
		planning_system.save_all()
	_save_player_state()


func _reset_world() -> void:
	world.reset_world(world_template)
	player.global_position = world.get_safe_spawn_position()
	player.velocity = Vector3.ZERO
	if not player_state_path.is_empty() and FileAccess.file_exists(player_state_path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(player_state_path))
	if hud:
		hud.show_message("تمت إعادة إنشاء العالم")


func _return_to_menu() -> void:
	_save_world_silent()
	return_to_menu_requested.emit()


func save_all() -> void:
	_save_world_silent()


func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_CLOSE_REQUEST]:
		_save_world_silent()


func _save_player_state() -> void:
	if player == null or player_state_path.is_empty() or not player.has_method("get_persistent_state"):
		return
	var file := FileAccess.open(player_state_path, FileAccess.WRITE)
	if file == null:
		return
	file.store_string(JSON.stringify({"version": 1, "player": player.get_persistent_state()}))


func _load_player_state() -> void:
	if player == null or player_state_path.is_empty() or not FileAccess.file_exists(player_state_path):
		return
	var file := FileAccess.open(player_state_path, FileAccess.READ)
	if file == null:
		return
	var parsed_value: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed_value) != TYPE_DICTIONARY:
		return
	var parsed: Dictionary = parsed_value
	var state_value: Variant = parsed.get("player", {})
	if typeof(state_value) == TYPE_DICTIONARY and player.has_method("apply_persistent_state"):
		var state: Dictionary = state_value
		player.apply_persistent_state(state)


func _on_lighting_mode_changed(mode_id: String) -> void:
	_apply_lighting_mode(mode_id, true)
	if hud:
		var labels: Dictionary = {"dawn":"الفجر", "day":"النهار", "dusk":"الغروب", "night":"الليل"}
		hud.show_message("الإضاءة: %s" % String(labels.get(current_lighting_mode, "النهار")))


func _apply_lighting_mode(mode_id: String, save_preference: bool = true) -> void:
	current_lighting_mode = mode_id if mode_id in ["dawn", "day", "dusk", "night"] else "day"
	if environment == null or sun == null:
		return
	match current_lighting_mode:
		"dawn":
			sky_material.sky_top_color = Color("344a72")
			sky_material.sky_horizon_color = Color("f3b78f")
			sky_material.ground_horizon_color = Color("a98d77")
			sky_material.ground_bottom_color = Color("5d594f")
			environment.ambient_light_color = Color("b8c9dc")
			environment.ambient_light_energy = 0.48
			environment.set("adjustment_brightness", 0.90)
			environment.set("adjustment_contrast", 1.08)
			environment.set("adjustment_saturation", 0.92)
			sun.light_color = Color("ffd0a3")
			sun.light_energy = 0.70
			sun.rotation_degrees = Vector3(-12.0, 62.0, 0.0)
		"night":
			sky_material.sky_top_color = Color("07152c")
			sky_material.sky_horizon_color = Color("243c5a")
			sky_material.ground_horizon_color = Color("1e2934")
			sky_material.ground_bottom_color = Color("10171f")
			environment.ambient_light_color = Color("45658b")
			environment.ambient_light_energy = 0.34
			environment.set("adjustment_brightness", 0.76)
			environment.set("adjustment_contrast", 1.12)
			environment.set("adjustment_saturation", 0.80)
			sun.light_color = Color("8db8ee")
			sun.light_energy = 0.24
			sun.rotation_degrees = Vector3(-28.0, 145.0, 0.0)
		"dusk":
			sky_material.sky_top_color = Color("5d6689")
			sky_material.sky_horizon_color = Color("e6a17b")
			sky_material.ground_horizon_color = Color("9c7865")
			sky_material.ground_bottom_color = Color("514a43")
			environment.ambient_light_color = Color("9fa8bb")
			environment.ambient_light_energy = 0.44
			environment.set("adjustment_brightness", 0.84)
			environment.set("adjustment_contrast", 1.10)
			environment.set("adjustment_saturation", 0.88)
			sun.light_color = Color("ffb676")
			sun.light_energy = 0.58
			sun.rotation_degrees = Vector3(-15.0, -58.0, 0.0)
		_:
			sky_material.sky_top_color = Color("397fab")
			sky_material.sky_horizon_color = Color("c6e1ec")
			sky_material.ground_horizon_color = Color("c7c9a8")
			sky_material.ground_bottom_color = Color("8d906f")
			environment.ambient_light_color = Color("d9e6ec")
			environment.ambient_light_energy = 0.58
			environment.set("adjustment_brightness", 0.98)
			environment.set("adjustment_contrast", 1.07)
			environment.set("adjustment_saturation", 0.98)
			sun.light_color = Color("fff3dc")
			sun.light_energy = 1.05
			sun.rotation_degrees = Vector3(-52.0, -35.0, 0.0)
	if hud:
		hud.set_lighting_mode(current_lighting_mode)
	if save_preference:
		_save_lighting_preference()


func _load_lighting_preference() -> void:
	var config := ConfigFile.new()
	if config.load(DISPLAY_SETTINGS_PATH) == OK:
		current_lighting_mode = String(config.get_value("display", "lighting_mode", "day"))
	if current_lighting_mode not in ["dawn", "day", "dusk", "night"]:
		current_lighting_mode = "day"


func _save_lighting_preference() -> void:
	var config := ConfigFile.new()
	config.set_value("display", "lighting_mode", current_lighting_mode)
	config.save(DISPLAY_SETTINGS_PATH)
