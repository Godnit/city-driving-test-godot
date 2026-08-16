extends Spatial

const PlayerScript = preload("res://scripts/player.gd")
const MobileUIScript = preload("res://scripts/mobile_ui.gd")

var player = null
var camera = null
var ui = null
var camera_yaw = 0.0
var camera_pitch = deg2rad(-17.0)
var camera_distance = 6.8
var camera_initialized = false

func _ready():
    _build_environment()
    _build_ground()
    _build_player()
    _build_camera()
    _build_ui()
    print("HUMAN_LEGACY_READY")
    if "--smoke-test" in OS.get_cmdline_args():
        call_deferred("_quit_smoke")

func _quit_smoke():
    get_tree().quit()

func _build_environment():
    var world_env = WorldEnvironment.new()
    var env = Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color("b8cfdf")
    env.background_energy = 1.0
    env.ambient_light_color = Color("dbe5ec")
    env.ambient_light_energy = 0.78
    world_env.environment = env
    add_child(world_env)

    var sun = DirectionalLight.new()
    sun.rotation_degrees = Vector3(-52, -34, 0)
    sun.light_energy = 1.15
    sun.shadow_enabled = true
    add_child(sun)

func _build_ground():
    var ground = StaticBody.new()
    ground.name = "GridGround"
    ground.collision_layer = 1
    ground.collision_mask = 1
    add_child(ground)

    var floor_mesh_node = MeshInstance.new()
    var floor_mesh = CubeMesh.new()
    floor_mesh.size = Vector3(72, 0.18, 72)
    floor_mesh_node.mesh = floor_mesh
    floor_mesh_node.translation.y = -0.09
    var floor_mat = SpatialMaterial.new()
    floor_mat.albedo_color = Color("cfd3d7")
    floor_mat.roughness = 0.93
    floor_mesh_node.material_override = floor_mat
    ground.add_child(floor_mesh_node)

    var floor_shape = CollisionShape.new()
    var box = BoxShape.new()
    box.extents = Vector3(36, 0.09, 36)
    floor_shape.shape = box
    floor_shape.translation.y = -0.09
    ground.add_child(floor_shape)

    var light_line_mat = SpatialMaterial.new()
    light_line_mat.albedo_color = Color("aeb5bb")
    light_line_mat.roughness = 1.0
    var dark_line_mat = SpatialMaterial.new()
    dark_line_mat.albedo_color = Color("7f8993")
    dark_line_mat.roughness = 1.0

    for i in range(-18, 19):
        var major = (i % 5 == 0)
        var width = 0.042 if major else 0.022
        var mat = dark_line_mat if major else light_line_mat
        _add_grid_strip(Vector3(i * 2.0, 0.014, 0), Vector3(width, 0.012, 72.0), mat, ground)
        _add_grid_strip(Vector3(0, 0.014, i * 2.0), Vector3(72.0, 0.012, width), mat, ground)

    _add_test_block(Vector3(3.2, 0.45, -3.0), Vector3(1.5, 0.9, 1.5), Color("8cb9d7"))
    _add_test_block(Vector3(5.0, 0.8, -3.0), Vector3(1.5, 1.6, 1.5), Color("7aa3c0"))
    _add_test_block(Vector3(6.8, 1.2, -3.0), Vector3(1.5, 2.4, 1.5), Color("698da9"))

func _add_grid_strip(pos, size, material, parent):
    var n = MeshInstance.new()
    var m = CubeMesh.new()
    m.size = size
    n.mesh = m
    n.translation = pos
    n.material_override = material
    n.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
    parent.add_child(n)

func _add_test_block(pos, size, color):
    var body = StaticBody.new()
    body.collision_layer = 1
    body.collision_mask = 1
    body.translation = pos
    add_child(body)

    var mesh_node = MeshInstance.new()
    var mesh = CubeMesh.new()
    mesh.size = size
    mesh_node.mesh = mesh
    var mat = SpatialMaterial.new()
    mat.albedo_color = color
    mat.roughness = 0.85
    mesh_node.material_override = mat
    body.add_child(mesh_node)

    var shape_node = CollisionShape.new()
    var shape = BoxShape.new()
    shape.extents = size * 0.5
    shape_node.shape = shape
    body.add_child(shape_node)

func _build_player():
    player = PlayerScript.new()
    player.name = "FloppyPlayer"
    player.translation = Vector3(0, 2.15, 1.0)
    player.collision_layer = 2
    player.collision_mask = 1
    add_child(player)

func _build_camera():
    camera = Camera.new()
    camera.name = "FollowCamera"
    camera.current = true
    camera.fov = 68.0
    camera.near = 0.08
    camera.far = 180.0
    add_child(camera)

func _build_ui():
    var layer = CanvasLayer.new()
    layer.layer = 10
    add_child(layer)
    ui = MobileUIScript.new()
    layer.add_child(ui)

func _physics_process(delta):
    if player == null or ui == null:
        return
    var move = ui.move_vector
    var jump = ui.consume_jump()
    var cam_delta = ui.consume_camera_delta()
    camera_yaw -= cam_delta.x * 0.0062
    camera_pitch = clamp(camera_pitch - cam_delta.y * 0.0045, deg2rad(-48.0), deg2rad(10.0))
    player.set_controls(move, jump, camera_yaw)
    _update_camera(delta)

func _update_camera(delta):
    var target = player.global_transform.origin + Vector3.UP * 0.45
    var horizontal = cos(camera_pitch) * camera_distance
    var offset = Vector3(sin(camera_yaw) * horizontal, -sin(camera_pitch) * camera_distance + 0.6, cos(camera_yaw) * horizontal)
    var desired = target + offset
    if not camera_initialized:
        var t = camera.global_transform
        t.origin = desired
        camera.global_transform = t
        camera_initialized = true
    else:
        var smooth = 1.0 - exp(-8.5 * delta)
        var t2 = camera.global_transform
        t2.origin = t2.origin.linear_interpolate(desired, smooth)
        camera.global_transform = t2
    camera.look_at(target, Vector3.UP)
