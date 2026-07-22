extends CharacterBody3D

var speed: float = 0.0
var steer_value: float = 0.0
var controls: Dictionary = {"accelerate": false, "brake": false, "left": false, "right": false}
var chase_camera: Camera3D
var cockpit_camera: Camera3D
var cockpit_mode: bool = false

const MAX_FORWARD: float = 22.0
const MAX_REVERSE: float = 7.0
const ACCELERATION: float = 10.0
const BRAKE_POWER: float = 18.0
const COAST_DECEL: float = 4.5
const STEER_SPEED: float = 1.8
const GRAVITY: float = 22.0

func _ready() -> void:
	collision_layer = 1
	collision_mask = 1
	var collision: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(1.75, 1.0, 3.7)
	collision.shape = shape
	collision.position.y = 0.5
	add_child(collision)
	var packed: PackedScene = load("res://assets/models/player_car.glb") as PackedScene
	if packed:
		var model: Node3D = packed.instantiate() as Node3D
		model.scale = Vector3.ONE * 1.45
		model.rotation.y = PI
		model.position.y = 0.05
		_disable_shadows(model)
		add_child(model)
	chase_camera = Camera3D.new()
	chase_camera.position = Vector3(0, 3.3, 7.2)
	chase_camera.rotation_degrees.x = -14.0
	chase_camera.fov = 67.0
	add_child(chase_camera)
	cockpit_camera = Camera3D.new()
	cockpit_camera.position = Vector3(0, 1.45, -0.35)
	cockpit_camera.fov = 74.0
	cockpit_camera.current = false
	add_child(cockpit_camera)

func _physics_process(delta: float) -> void:
	var throttle: float = 1.0 if bool(controls["accelerate"]) or Input.is_action_pressed("accelerate") else 0.0
	var braking: bool = bool(controls["brake"]) or Input.is_action_pressed("brake")
	var steering: float = 0.0
	if bool(controls["left"]) or Input.is_action_pressed("steer_left"):
		steering -= 1.0
	if bool(controls["right"]) or Input.is_action_pressed("steer_right"):
		steering += 1.0
	steer_value = move_toward(steer_value, steering, 4.5 * delta)
	if throttle > 0.0:
		speed = move_toward(speed, MAX_FORWARD, ACCELERATION * delta)
	elif braking:
		if speed > 0.6:
			speed = move_toward(speed, 0.0, BRAKE_POWER * delta)
		else:
			speed = move_toward(speed, -MAX_REVERSE, ACCELERATION * 0.65 * delta)
	else:
		speed = move_toward(speed, 0.0, COAST_DECEL * delta)
	var steering_strength: float = clampf(absf(speed) / 5.0, 0.18, 1.0)
	rotation.y -= steer_value * STEER_SPEED * steering_strength * delta * (1.0 if speed >= 0.0 else -1.0)
	velocity.x = -transform.basis.z.x * speed
	velocity.z = -transform.basis.z.z * speed
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = -0.2
	move_and_slide()
	if global_position.y < -3.0:
		global_position = Vector3(2.5, 0.5, 4.0)
		speed = 0.0

func set_control(action: String, pressed: bool) -> void:
	if controls.has(action):
		controls[action] = pressed

func get_speed_kmh() -> float:
	return absf(speed) * 3.6

func toggle_camera() -> void:
	cockpit_mode = not cockpit_mode
	chase_camera.current = not cockpit_mode
	cockpit_camera.current = cockpit_mode

func _disable_shadows(node: Node) -> void:
	if node is GeometryInstance3D:
		(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child: Node in node.get_children():
		_disable_shadows(child)
