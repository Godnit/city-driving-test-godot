extends Node3D

const PlayerScript = preload("res://scripts/player.gd")
const MobileUIScript = preload("res://scripts/mobile_ui.gd")

var player: RigidBody3D
var camera: Camera3D
var ui
var camera_yaw: float = 0.0
var camera_pitch: float = deg_to_rad(-17.0)
var camera_distance: float = 6.8
var _camera_initialized: bool = false

func _ready() -> void:
	_build_environment()
	_build_ground()
	_build_player()
	_build_camera()
	_build_ui()
	print("HUMAN_PHYSICS_READY")
	if "--smoke-test" in OS.get_cmdline_user_args():
		call_deferred("_quit_smoke")

func _quit_smoke() -> void:
	await get_tree().process_frame
	get_tree().quit()

func _build_environment() -> void:
	var world_env: WorldEnvironment = WorldEnvironment.new()
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky: Sky = Sky.new()
	var sky_mat: ProceduralSkyMaterial = ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color("6f9fc7")
	sky_mat.sky_horizon_color = Color("d9e5ee")
	sky_mat.ground_bottom_color = Color("8695a2")
	sky_mat.ground_horizon_color = Color("d9e5ee")
	sky.material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.62
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_env.environment = env
	add_child(world_env)
	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -34, 0)
	sun.light_energy = 1.45
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 55.0
	add_child(sun)

func _build_ground() -> void:
	var ground: StaticBody3D = StaticBody3D.new()
	ground.name = "GridGround"
	ground.collision_layer = 1
	ground.collision_mask = 1
	add_child(ground)
	var floor_mesh_node: MeshInstance3D = MeshInstance3D.new()
	var floor_mesh: BoxMesh = BoxMesh.new()
	floor_mesh.size = Vector3(72, 0.18, 72)
	floor_mesh_node.mesh = floor_mesh
	floor_mesh_node.position.y = -0.09
	var floor_mat: StandardMaterial3D = StandardMaterial3D.new()
	floor_mat.albedo_color = Color("cfd3d7")
	floor_mat.roughness = 0.93
	floor_mesh_node.material_override = floor_mat
	ground.add_child(floor_mesh_node)
	var floor_shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(72, 0.18, 72)
	floor_shape.shape = box
	floor_shape.position.y = -0.09
	ground.add_child(floor_shape)
	var light_line_mat: StandardMaterial3D = StandardMaterial3D.new()
	light_line_mat.albedo_color = Color("aeb5bb")
	light_line_mat.roughness = 1.0
	var dark_line_mat: StandardMaterial3D = StandardMaterial3D.new()
	dark_line_mat.albedo_color = Color("7f8993")
	dark_line_mat.roughness = 1.0
	for i: int in range(-18, 19):
		var major: bool = (i % 5 == 0)
		var width: float = 0.042 if major else 0.022
		var mat: Material = dark_line_mat if major else light_line_mat
		_add_grid_strip(Vector3(i * 2.0, 0.014, 0), Vector3(width, 0.012, 72.0), mat, ground)
		_add_grid_strip(Vector3(0, 0.014, i * 2.0), Vector3(72.0, 0.012, width), mat, ground)
	_add_test_block(Vector3(3.2, 0.45, -3.0), Vector3(1.5, 0.9, 1.5), Color("8cb9d7"))
	_add_test_block(Vector3(5.0, 0.8, -3.0), Vector3(1.5, 1.6, 1.5), Color("7aa3c0"))
	_add_test_block(Vector3(6.8, 1.2, -3.0), Vector3(1.5, 2.4, 1.5), Color("698da9"))

func _add_grid_strip(pos: Vector3, size: Vector3, material: Material, parent: Node) -> void:
	var n: MeshInstance3D = MeshInstance3D.new()
	var m: BoxMesh = BoxMesh.new()
	m.size = size
	n.mesh = m
	n.position = pos
	n.material_override = material
	n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(n)

func _add_test_block(pos: Vector3, size: Vector3, color: Color) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 1
	body.position = pos
	add_child(body)
	var mesh_node: MeshInstance3D = MeshInstance3D.new()
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size
	mesh_node.mesh = mesh
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.85
	mesh_node.material_override = mat
	body.add_child(mesh_node)
	var shape_node: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = size
	shape_node.shape = shape
	body.add_child(shape_node)

func _build_player() -> void:
	player = PlayerScript.new()
	player.name = "FloppyPlayer"
	player.position = Vector3(0, 2.15, 1.0)
	player.collision_layer = 2
	player.collision_mask = 1
	add_child(player)

func _build_camera() -> void:
	camera = Camera3D.new()
	camera.name = "FollowCamera"
	camera.current = true
	camera.fov = 68.0
	camera.near = 0.08
	camera.far = 180.0
	add_child(camera)

func _build_ui() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	ui = MobileUIScript.new()
	layer.add_child(ui)

func _physics_process(delta: float) -> void:
	if player == null or ui == null:
		return
	var move: Vector2 = ui.move_vector
	if move.length_squared() < 0.001:
		move = Input.get_vector("move_left", "move_right", "move_back", "move_forward")
	var jump: bool = bool(ui.consume_jump()) or Input.is_action_just_pressed("jump")
	var cam_delta: Vector2 = ui.consume_camera_delta()
	camera_yaw -= cam_delta.x * 0.0062
	camera_pitch = clampf(camera_pitch - cam_delta.y * 0.0045, deg_to_rad(-48.0), deg_to_rad(10.0))
	player.set_controls(move, jump, camera_yaw)
	_update_camera(delta)

func _update_camera(delta: float) -> void:
	var target: Vector3 = player.global_position + Vector3.UP * 0.45
	var horizontal: float = cos(camera_pitch) * camera_distance
	var offset: Vector3 = Vector3(sin(camera_yaw) * horizontal, -sin(camera_pitch) * camera_distance + 0.6, cos(camera_yaw) * horizontal)
	var desired: Vector3 = target + offset
	if not _camera_initialized:
		camera.global_position = desired
		_camera_initialized = true
	else:
		var smooth: float = 1.0 - exp(-8.5 * delta)
		camera.global_position = camera.global_position.lerp(desired, smooth)
	camera.look_at(target, Vector3.UP)
