extends Camera3D

var target: Node3D
var mode: int = 0

const OFFSETS: Array[Vector3] = [
	Vector3(0.0, 2.7, 6.4),
	Vector3(0.0, 1.42, -1.05),
	Vector3(0.30, 1.28, -0.12)
]

func setup(target_node: Node3D) -> void:
	target = target_node
	far = 320.0
	near = 0.10
	fov = 66.0
	current = true
	_snap_to_target()

func cycle_mode() -> void:
	mode = (mode + 1) % OFFSETS.size()
	fov = [66.0, 70.0, 72.0][mode]
	set_cull_mask_value(2, mode != 2)
	_snap_to_target()

func _process(delta: float) -> void:
	if not is_instance_valid(target):
		return
	var target_transform := target.global_transform
	var desired_position := target_transform * OFFSETS[mode]
	var look_distance := [7.5, 20.0, 24.0][mode]
	var look_height := [1.0, 1.25, 1.20][mode]
	var look_target := target.global_position + Vector3.UP * look_height - target_transform.basis.z * look_distance
	var positional_speed := [6.2, 12.0, 18.0][mode]
	var rotation_speed := [7.5, 13.0, 18.0][mode]
	var position_alpha := 1.0 - exp(-positional_speed * delta)
	var rotation_alpha := 1.0 - exp(-rotation_speed * delta)
	var new_position := global_position.lerp(desired_position, position_alpha)
	var direction := (look_target - new_position).normalized()
	var desired_basis := Basis.looking_at(direction, Vector3.UP)
	var current_q := global_transform.basis.get_rotation_quaternion()
	var desired_q := desired_basis.get_rotation_quaternion()
	var new_basis := Basis(current_q.slerp(desired_q, rotation_alpha))
	global_transform = Transform3D(new_basis, new_position)

func _snap_to_target() -> void:
	if not is_instance_valid(target):
		return
	var target_transform := target.global_transform
	var desired_position := target_transform * OFFSETS[mode]
	var look_target := target.global_position + Vector3.UP * 1.1 - target_transform.basis.z * 8.0
	global_transform = Transform3D(Basis.looking_at((look_target - desired_position).normalized(), Vector3.UP), desired_position)
	reset_physics_interpolation()
