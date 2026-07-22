extends CharacterBody3D

var speed: float = 0.0
var steer_input: float = 0.0
var steer_visual: float = 0.0
var throttle_pressed: bool = false
var brake_pressed: bool = false
var gear: String = "D"
var visual_root: Node3D
var wheel_pivots: Array[Node3D] = []
var front_wheel_pivots: Array[Node3D] = []
var wheel_spin: float = 0.0
var engine_idle: AudioStreamPlayer
var engine_high: AudioStreamPlayer
var horn_player: AudioStreamPlayer
var brake_player: AudioStreamPlayer
var brake_was_pressed: bool = false

const MAX_FORWARD: float = 25.0
const MAX_REVERSE: float = 6.5
const WHEEL_RADIUS: float = 0.34
const GRAVITY: float = 22.0

func _ready() -> void:
	collision_layer = 1
	collision_mask = 1
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.72, 0.95, 3.95)
	collision.shape = shape
	collision.position.y = 0.48
	add_child(collision)
	_load_vehicle_visual()
	_create_audio()

func _load_vehicle_visual() -> void:
	var packed := load("res://assets/models/player_sedan.glb") as PackedScene
	if packed == null:
		push_error("Player sedan model missing")
		return
	visual_root = packed.instantiate() as Node3D
	visual_root.name = "PlayerCarVisual"
	visual_root.rotation = Vector3.ZERO
	visual_root.position = Vector3.ZERO
	add_child(visual_root)
	_remove_embedded_scene_objects(visual_root)
	_prepare_visuals(visual_root)
	_prepare_wheels()

func _prepare_wheels() -> void:
	var wheel_nodes := visual_root.find_children("*Wheel*", "MeshInstance3D", true, false)
	for wheel_variant in wheel_nodes:
		var wheel := wheel_variant as MeshInstance3D
		if wheel == null:
			continue
		var old_parent := wheel.get_parent()
		var old_transform := wheel.transform
		var pivot := Node3D.new()
		pivot.name = wheel.name + "_Pivot"
		old_parent.add_child(pivot)
		pivot.transform = old_transform
		wheel.reparent(pivot)
		wheel.transform = Transform3D.IDENTITY
		wheel_pivots.append(pivot)
		if wheel.name.contains("003") or wheel.name.contains("001"):
			front_wheel_pivots.append(pivot)

func _create_audio() -> void:
	engine_idle = _make_audio_player("res://assets/audio/engine_idle.wav", true, -12.0)
	engine_high = _make_audio_player("res://assets/audio/engine_high.wav", true, -50.0)
	horn_player = _make_audio_player("res://assets/audio/horn.wav", false, -5.0)
	brake_player = _make_audio_player("res://assets/audio/brake.ogg", false, -12.0)
	if engine_idle.stream:
		engine_idle.play()
	if engine_high.stream:
		engine_high.play()

func _make_audio_player(path: String, looping: bool, volume: float) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.volume_db = volume
	if ResourceLoader.exists(path):
		player.stream = load(path)
		if looping and player.stream is AudioStreamWAV:
			(player.stream as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
		elif looping and player.stream is AudioStreamOggVorbis:
			(player.stream as AudioStreamOggVorbis).loop = true
	add_child(player)
	return player

func _physics_process(delta: float) -> void:
	var throttle := throttle_pressed or Input.is_action_pressed("accelerate")
	var braking := brake_pressed or Input.is_action_pressed("brake")
	var keyboard_steer := Input.get_axis("steer_left", "steer_right")
	var steering := steer_input if absf(steer_input) > 0.01 else keyboard_steer
	steer_visual = move_toward(steer_visual, steering, 4.8 * delta)
	var normalized_speed := clampf(absf(speed) / MAX_FORWARD, 0.0, 1.0)
	var drive_acceleration := lerpf(7.2, 1.35, normalized_speed)
	var rolling_resistance := 0.42 + absf(speed) * 0.035 + speed * speed * 0.0035
	if gear == "D" and throttle:
		speed = move_toward(speed, MAX_FORWARD, drive_acceleration * delta)
	elif gear == "R" and throttle:
		speed = move_toward(speed, -MAX_REVERSE, 4.8 * delta)
	elif braking:
		var brake_force := 13.5 if absf(speed) > 2.0 else 8.0
		speed = move_toward(speed, 0.0, brake_force * delta)
	elif gear == "P":
		speed = move_toward(speed, 0.0, 18.0 * delta)
	else:
		speed = move_toward(speed, 0.0, rolling_resistance * delta)
	if absf(speed) < 0.03:
		speed = 0.0
	var speed_abs := absf(speed)
	if speed_abs > 0.38:
		var speed_ratio := clampf(speed_abs / MAX_FORWARD, 0.0, 1.0)
		var max_yaw_rate := lerpf(1.45, 0.52, speed_ratio)
		var direction_sign := 1.0 if speed >= 0.0 else -1.0
		rotation.y -= steer_visual * max_yaw_rate * direction_sign * delta
	velocity.x = -transform.basis.z.x * speed
	velocity.z = -transform.basis.z.z * speed
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = -0.12
	move_and_slide()
	_update_wheels(delta)
	_update_audio(braking)
	if global_position.y < -3.0 or absf(global_position.x) > 145.0 or global_position.z < -720.0 or global_position.z > 85.0:
		reset_vehicle()

func _update_wheels(delta: float) -> void:
	wheel_spin += speed * delta / WHEEL_RADIUS
	for pivot in wheel_pivots:
		if is_instance_valid(pivot) and pivot.get_child_count() > 0:
			var wheel := pivot.get_child(0) as Node3D
			wheel.rotation.x = wheel_spin
	for pivot in front_wheel_pivots:
		if is_instance_valid(pivot):
			pivot.rotation.y = steer_visual * 0.42

func _update_audio(braking: bool) -> void:
	var ratio := clampf(absf(speed) / MAX_FORWARD, 0.0, 1.0)
	if engine_idle.stream:
		engine_idle.pitch_scale = 0.82 + ratio * 0.55
		engine_idle.volume_db = lerpf(-9.0, -18.0, ratio)
	if engine_high.stream:
		engine_high.pitch_scale = 0.75 + ratio * 0.95
		engine_high.volume_db = lerpf(-48.0, -7.0, clampf((ratio - 0.22) / 0.78, 0.0, 1.0))
	if braking and not brake_was_pressed and absf(speed) > 5.0 and brake_player.stream:
		brake_player.play()
	brake_was_pressed = braking

func set_control(action: String, pressed: bool) -> void:
	if action == "accelerate":
		throttle_pressed = pressed
	elif action == "brake":
		brake_pressed = pressed

func set_steer(value: float) -> void:
	steer_input = clampf(value, -1.0, 1.0)

func set_gear(new_gear: String) -> void:
	if new_gear in ["P", "R", "N", "D"]:
		gear = new_gear

func play_horn() -> void:
	if horn_player.stream:
		horn_player.stop()
		horn_player.play()

func get_speed_kmh() -> float:
	return absf(speed) * 3.6

func reset_vehicle() -> void:
	global_position = Vector3(5.4, 0.52, 48.0)
	rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	speed = 0.0
	gear = "D"
	reset_physics_interpolation()

func _remove_embedded_scene_objects(node: Node) -> void:
	for child in node.get_children():
		if child is Camera3D or child is Light3D or child is WorldEnvironment:
			child.queue_free()
		else:
			_remove_embedded_scene_objects(child)

func _prepare_visuals(node: Node) -> void:
	if node is GeometryInstance3D:
		var geometry := node as GeometryInstance3D
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geometry.layers = 2
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface_index in range(mesh_instance.mesh.get_surface_count()):
				var source_material := mesh_instance.mesh.surface_get_material(surface_index)
				if source_material is StandardMaterial3D:
					var material := source_material.duplicate() as StandardMaterial3D
					material.metallic = minf(material.metallic, 0.18)
					material.roughness = maxf(material.roughness, 0.55)
					material.clearcoat_enabled = false
					mesh_instance.set_surface_override_material(surface_index, material)
	for child in node.get_children():
		_prepare_visuals(child)
