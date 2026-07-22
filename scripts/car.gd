extends CharacterBody3D

var speed: float = 0.0
var steer_value: float = 0.0
var controls: Dictionary = {"accelerate": false, "brake": false, "left": false, "right": false}
var chase_camera: Camera3D
var hood_camera: Camera3D
var hood_mode: bool = false

const MAX_FORWARD: float = 19.0
const MAX_REVERSE: float = 5.5
const ACCELERATION: float = 8.5
const BRAKE_POWER: float = 16.0
const COAST_DECEL: float = 4.2
const STEER_SPEED: float = 1.65
const GRAVITY: float = 20.0

func _ready() -> void:
	collision_layer = 1
	collision_mask = 1
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.65, 0.9, 3.45)
	collision.shape = shape
	collision.position.y = 0.48
	add_child(collision)

	var packed := load("res://assets/models/player_car.glb") as PackedScene
	if packed:
		var model := packed.instantiate() as Node3D
		_remove_embedded_scene_objects(model)
		model.name = "LowPolyCar"
		model.scale = Vector3.ONE * 1.18
		model.rotation.y = PI
		model.position = Vector3(0.0, 0.04, 0.0)
		_make_model_mobile_fast(model)
		add_child(model)
	else:
		push_error("Low-poly player car model was not found")

	chase_camera = Camera3D.new()
	chase_camera.position = Vector3(0.0, 2.55, 5.9)
	chase_camera.rotation_degrees.x = -12.0
	chase_camera.fov = 64.0
	chase_camera.near = 0.15
	chase_camera.far = 95.0
	chase_camera.current = true
	add_child(chase_camera)

	hood_camera = Camera3D.new()
	hood_camera.position = Vector3(0.0, 1.2, -1.15)
	hood_camera.rotation_degrees.x = -2.0
	hood_camera.fov = 68.0
	hood_camera.near = 0.12
	hood_camera.far = 95.0
	hood_camera.current = false
	add_child(hood_camera)

func _physics_process(delta: float) -> void:
	var accelerating: bool = bool(controls["accelerate"]) or Input.is_action_pressed("accelerate")
	var braking: bool = bool(controls["brake"]) or Input.is_action_pressed("brake")
	var steering: float = 0.0
	if bool(controls["left"]) or Input.is_action_pressed("steer_left"):
		steering -= 1.0
	if bool(controls["right"]) or Input.is_action_pressed("steer_right"):
		steering += 1.0
	steer_value = move_toward(steer_value, steering, 4.2 * delta)

	if accelerating:
		speed = move_toward(speed, MAX_FORWARD, ACCELERATION * delta)
	elif braking:
		if speed > 0.55:
			speed = move_toward(speed, 0.0, BRAKE_POWER * delta)
		else:
			speed = move_toward(speed, -MAX_REVERSE, ACCELERATION * 0.6 * delta)
	else:
		speed = move_toward(speed, 0.0, COAST_DECEL * delta)

	var steering_strength: float = clampf(absf(speed) / 5.0, 0.16, 1.0)
	rotation.y -= steer_value * STEER_SPEED * steering_strength * delta * (1.0 if speed >= 0.0 else -1.0)
	velocity.x = -transform.basis.z.x * speed
	velocity.z = -transform.basis.z.z * speed
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = -0.15
	move_and_slide()

	global_position.x = clampf(global_position.x, -5.35, 5.35)
	if global_position.y < -2.0 or global_position.z < -176.0:
		global_position = Vector3(2.4, 0.48, 4.0)
		rotation = Vector3.ZERO
		speed = 0.0

func set_control(action: String, pressed: bool) -> void:
	if controls.has(action):
		controls[action] = pressed

func get_speed_kmh() -> float:
	return absf(speed) * 3.6

func toggle_camera() -> void:
	hood_mode = not hood_mode
	chase_camera.current = not hood_mode
	hood_camera.current = hood_mode

func _remove_embedded_scene_objects(node: Node) -> void:
	for child in node.get_children():
		if child is Camera3D or child is Light3D or child is WorldEnvironment:
			child.free()
		else:
			_remove_embedded_scene_objects(child)

func _make_model_mobile_fast(node: Node) -> void:
	if node is GeometryInstance3D:
		var geometry := node as GeometryInstance3D
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geometry.visibility_range_end = 95.0
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
