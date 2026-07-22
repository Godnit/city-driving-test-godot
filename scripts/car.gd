extends CharacterBody3D

var speed: float = 0.0
var steer_value: float = 0.0
var controls: Dictionary = {"accelerate": false, "brake": false, "left": false, "right": false}
var gear: String = "D"
var cameras: Array[Camera3D] = []
var camera_index: int = 0

const MAX_FORWARD: float = 21.5
const MAX_REVERSE: float = 6.0
const ACCELERATION: float = 9.5
const REVERSE_ACCELERATION: float = 6.0
const BRAKE_POWER: float = 18.0
const COAST_DECEL: float = 3.8
const STEER_SPEED: float = 1.55
const GRAVITY: float = 20.0

func _ready() -> void:
	collision_layer = 1
	collision_mask = 1
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.78, 0.95, 3.85)
	collision.shape = shape
	collision.position.y = 0.5
	add_child(collision)
	_load_sketchfab_car()
	_create_cameras()

func _load_sketchfab_car() -> void:
	var model_path := "res://assets/sketchfab/player_car.glb"
	if not ResourceLoader.exists(model_path):
		push_warning("Sketchfab player car is not installed yet: " + model_path)
		return
	var packed := load(model_path) as PackedScene
	if not packed:
		push_warning("Sketchfab player car could not be imported")
		return
	var model := packed.instantiate() as Node3D
	_remove_embedded_scene_objects(model)
	model.name = "PlayerCarVisual"
	model.scale = Vector3.ONE
	model.rotation.y = PI
	model.position = Vector3.ZERO
	_make_model_mobile_fast(model)
	add_child(model)

func _create_cameras() -> void:
	# Cockpit-style camera, similar in function but not copied from any game assets.
	var cockpit := Camera3D.new()
	cockpit.name = "CockpitCamera"
	cockpit.position = Vector3(0.34, 1.18, -0.58)
	cockpit.rotation_degrees.x = -1.5
	cockpit.fov = 70.0
	cockpit.near = 0.08
	cockpit.far = 145.0
	add_child(cockpit)
	cameras.append(cockpit)

	var bonnet := Camera3D.new()
	bonnet.name = "BonnetCamera"
	bonnet.position = Vector3(0.0, 1.25, -1.45)
	bonnet.rotation_degrees.x = -3.0
	bonnet.fov = 68.0
	bonnet.near = 0.08
	bonnet.far = 145.0
	add_child(bonnet)
	cameras.append(bonnet)

	var chase := Camera3D.new()
	chase.name = "ChaseCamera"
	chase.position = Vector3(0.0, 2.85, 6.4)
	chase.rotation_degrees.x = -13.5
	chase.fov = 65.0
	chase.near = 0.12
	chase.far = 145.0
	add_child(chase)
	cameras.append(chase)

	camera_index = 0
	_update_current_camera()

func _physics_process(delta: float) -> void:
	var accelerating := bool(controls["accelerate"]) or Input.is_action_pressed("accelerate")
	var braking := bool(controls["brake"]) or Input.is_action_pressed("brake")
	var steering: float = 0.0
	if bool(controls["left"]) or Input.is_action_pressed("steer_left"):
		steering -= 1.0
	if bool(controls["right"]) or Input.is_action_pressed("steer_right"):
		steering += 1.0
	steer_value = move_toward(steer_value, steering, 4.4 * delta)

	if braking:
		speed = move_toward(speed, 0.0, BRAKE_POWER * delta)
	elif gear == "D" and accelerating:
		speed = move_toward(speed, MAX_FORWARD, ACCELERATION * delta)
	elif gear == "R" and accelerating:
		speed = move_toward(speed, -MAX_REVERSE, REVERSE_ACCELERATION * delta)
	elif gear == "P":
		speed = move_toward(speed, 0.0, BRAKE_POWER * delta)
	else:
		speed = move_toward(speed, 0.0, COAST_DECEL * delta)

	var steering_strength := clampf(absf(speed) / 5.5, 0.12, 1.0)
	rotation.y -= steer_value * STEER_SPEED * steering_strength * delta * (1.0 if speed >= 0.0 else -1.0)
	velocity.x = -transform.basis.z.x * speed
	velocity.z = -transform.basis.z.z * speed
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = -0.15
	move_and_slide()

	if global_position.y < -3.0 or absf(global_position.x) > 125.0 or global_position.z < -305.0 or global_position.z > 45.0:
		_reset_to_start()

func set_control(action: String, pressed: bool) -> void:
	if controls.has(action):
		controls[action] = pressed

func set_gear(new_gear: String) -> void:
	if new_gear not in ["P", "R", "N", "D"]:
		return
	gear = new_gear
	if gear == "P":
		speed = move_toward(speed, 0.0, 4.0)

func get_speed_kmh() -> float:
	return absf(speed) * 3.6

func toggle_camera() -> void:
	if cameras.is_empty():
		return
	camera_index = (camera_index + 1) % cameras.size()
	_update_current_camera()

func _update_current_camera() -> void:
	for index in range(cameras.size()):
		cameras[index].current = index == camera_index

func _reset_to_start() -> void:
	global_position = Vector3(5.5, 0.48, 12.0)
	rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	speed = 0.0
	gear = "D"

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
		geometry.visibility_range_end = 145.0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface_index in range(mesh_instance.mesh.get_surface_count()):
				var source_material := mesh_instance.mesh.surface_get_material(surface_index)
				if source_material is StandardMaterial3D:
					var fast_material := source_material.duplicate() as StandardMaterial3D
					fast_material.metallic = minf(fast_material.metallic, 0.15)
					fast_material.roughness = maxf(fast_material.roughness, 0.62)
					fast_material.clearcoat_enabled = false
					mesh_instance.set_surface_override_material(surface_index, fast_material)
	for child in node.get_children():
		_make_model_mobile_fast(child)
