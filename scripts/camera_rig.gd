extends Camera3D

var target: Node3D
var mode: int = 0

const OFFSETS: Array[Vector3] = [
	Vector3(0.0, 3.25, 8.30),
	Vector3(0.0, 2.05, 1.10),
	Vector3(0.30, 1.48, -0.30)
]

const LOOK_DISTANCES: Array[float] = [9.5, 16.0, 21.0]
const LOOK_HEIGHTS: Array[float] = [1.15, 1.30, 1.30]
const MIN_HEIGHTS_ABOVE_TARGET: Array[float] = [2.20, 1.45, 1.15]
const POSITIONAL_SPEEDS: Array[float] = [7.5, 11.5, 16.0]
const ROTATION_SPEEDS: Array[float] = [8.5, 12.0, 16.0]
const MODE_FOVS: Array[float] = [64.0, 68.0, 72.0]

func setup(target_node: Node3D) -> void:
	target = target_node
	far = 420.0
	near = 0.05
	fov = MODE_FOVS[0]
	current = true
	_snap_to_target()

func cycle_mode() -> void:
	mode = (mode + 1) % OFFSETS.size()
	fov = MODE_FOVS[mode]
	set_cull_mask_value(2, mode != 2)
	_snap_to_target()

func _process(delta: float) -> void:
	if not is_instance_valid(target):
		return
	var target_transform := target.global_transform
	var desired_position := target_transform * OFFSETS[mode]
	desired_position.y = maxf(desired_position.y, target.global_position.y + MIN_HEIGHTS_ABOVE_TARGET[mode])
	desired_position.y = maxf(desired_position.y, 1.65)
	var look_target := target.global_position + Vector3.UP * LOOK_HEIGHTS[mode] - target_transform.basis.z * LOOK_DISTANCES[mode]
	var positional_speed: float = POSITIONAL_SPEEDS[mode]
	var rotation_speed: float = ROTATION_SPEEDS[mode]
	var position_alpha := 1.0 - exp(-positional_speed * delta)
	var rotation_alpha := 1.0 - exp(-rotation_speed * delta)
	var new_position := global_position.lerp(desired_position, position_alpha)
	new_position.y = maxf(new_position.y, 1.55)
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
	desired_position.y = maxf(desired_position.y, target.global_position.y + MIN_HEIGHTS_ABOVE_TARGET[mode])
	desired_position.y = maxf(desired_position.y, 1.65)
	var look_target := target.global_position + Vector3.UP * LOOK_HEIGHTS[mode] - target_transform.basis.z * LOOK_DISTANCES[mode]
	look_at_from_position(desired_position, look_target, Vector3.UP)
	reset_physics_interpolation()
	print("CAMERA_RIG_READY mode=%d position=%s target=%s" % [mode, str(global_position), str(look_target)])
