extends RigidBody3D

const MOVE_SPEED: float = 5.2
const MOVE_ACCEL: float = 7.2
const AIR_CONTROL: float = 0.38
const MAX_FORCE: float = 560.0
const JUMP_IMPULSE: float = 6.6
const UPRIGHT_STRENGTH: float = 38.0
const UPRIGHT_DAMPING: float = 7.5
const TURN_STRENGTH: float = 8.0

var move_input: Vector2 = Vector2.ZERO
var control_yaw: float = 0.0
var jump_requested: bool = false
var grounded: bool = false
var _walk_time: float = 0.0
var _limbs: Array[Node3D] = []
var _torso: Node3D
var _head: Node3D

func _ready() -> void:
	mass = 2.8
	linear_damp = 0.55
	angular_damp = 0.85
	contact_monitor = true
	max_contacts_reported = 12
	continuous_cd = true
	can_sleep = false
	_build_collision()
	_build_character()

func _build_collision() -> void:
	var collider: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.43
	capsule.height = 1.55
	collider.shape = capsule
	collider.position.y = 0.05
	add_child(collider)

func _mat(color: Color, roughness: float = 0.78) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	return material

func _mesh_part(name_text: String, mesh: Mesh, position: Vector3, rotation: Vector3, material: Material) -> MeshInstance3D:
	var node: MeshInstance3D = MeshInstance3D.new()
	node.name = name_text
	node.mesh = mesh
	node.position = position
	node.rotation = rotation
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(node)
	return node

func _build_character() -> void:
	var suit: StandardMaterial3D = _mat(Color("f0f2f4"))
	var accent: StandardMaterial3D = _mat(Color("6aa5d8"), 0.65)
	var dark: StandardMaterial3D = _mat(Color("18202a"), 0.9)
	var torso_mesh: CapsuleMesh = CapsuleMesh.new()
	torso_mesh.radius = 0.39
	torso_mesh.height = 1.18
	_torso = _mesh_part("Torso", torso_mesh, Vector3(0, 0.05, 0), Vector3.ZERO, suit)
	var belly: BoxMesh = BoxMesh.new()
	belly.size = Vector3(0.56, 0.34, 0.06)
	_mesh_part("Accent", belly, Vector3(0, 0.06, -0.37), Vector3.ZERO, accent)
	var head_mesh: SphereMesh = SphereMesh.new()
	head_mesh.radius = 0.38
	head_mesh.height = 0.76
	_head = _mesh_part("Head", head_mesh, Vector3(0, 0.94, -0.02), Vector3.ZERO, suit)
	var eye_mesh: SphereMesh = SphereMesh.new()
	eye_mesh.radius = 0.042
	eye_mesh.height = 0.084
	_mesh_part("EyeL", eye_mesh, Vector3(-0.12, 1.00, -0.355), Vector3.ZERO, dark)
	_mesh_part("EyeR", eye_mesh, Vector3(0.12, 1.00, -0.355), Vector3.ZERO, dark)
	var arm_mesh: CapsuleMesh = CapsuleMesh.new()
	arm_mesh.radius = 0.13
	arm_mesh.height = 0.92
	var left_arm: MeshInstance3D = _mesh_part("LeftArm", arm_mesh, Vector3(-0.61, 0.22, 0), Vector3(0, 0, deg_to_rad(76)), suit)
	var right_arm: MeshInstance3D = _mesh_part("RightArm", arm_mesh, Vector3(0.61, 0.22, 0), Vector3(0, 0, deg_to_rad(-76)), suit)
	_limbs.append(left_arm)
	_limbs.append(right_arm)
	var leg_mesh: CapsuleMesh = CapsuleMesh.new()
	leg_mesh.radius = 0.16
	leg_mesh.height = 0.92
	var left_leg: MeshInstance3D = _mesh_part("LeftLeg", leg_mesh, Vector3(-0.22, -0.78, 0.02), Vector3.ZERO, suit)
	var right_leg: MeshInstance3D = _mesh_part("RightLeg", leg_mesh, Vector3(0.22, -0.78, 0.02), Vector3.ZERO, suit)
	_limbs.append(left_leg)
	_limbs.append(right_leg)
	var foot_mesh: BoxMesh = BoxMesh.new()
	foot_mesh.size = Vector3(0.30, 0.18, 0.50)
	_mesh_part("LeftFoot", foot_mesh, Vector3(-0.22, -1.18, -0.11), Vector3.ZERO, suit)
	_mesh_part("RightFoot", foot_mesh, Vector3(0.22, -1.18, -0.11), Vector3.ZERO, suit)

func set_controls(move: Vector2, jump: bool, yaw: float) -> void:
	move_input = move.limit_length(1.0)
	control_yaw = yaw
	if jump:
		jump_requested = true

func _physics_process(delta: float) -> void:
	_update_grounded()
	_animate_soft_body(delta)
	if global_position.y < -15.0:
		linear_velocity = Vector3.ZERO
		angular_velocity = Vector3.ZERO
		global_position = Vector3(0, 3.0, 0)
		global_rotation = Vector3.ZERO

func _update_grounded() -> void:
	var world: World3D = get_world_3d()
	if world == null:
		grounded = false
		return
	var ray_from: Vector3 = global_position + Vector3.UP * 0.08
	var ray_to: Vector3 = ray_from + Vector3.DOWN * 1.48
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(ray_from, ray_to)
	query.exclude = [get_rid()]
	query.collision_mask = 1
	grounded = not world.direct_space_state.intersect_ray(query).is_empty()

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	var forward: Vector3 = Vector3(-sin(control_yaw), 0.0, -cos(control_yaw))
	var right: Vector3 = Vector3(cos(control_yaw), 0.0, -sin(control_yaw))
	var wish_dir: Vector3 = right * move_input.x + forward * move_input.y
	if wish_dir.length_squared() > 0.001:
		wish_dir = wish_dir.normalized()
	var lv: Vector3 = state.linear_velocity
	var horizontal: Vector3 = Vector3(lv.x, 0.0, lv.z)
	var target: Vector3 = wish_dir * MOVE_SPEED
	var control: float = 1.0 if grounded else AIR_CONTROL
	var force: Vector3 = (target - horizontal) * mass * MOVE_ACCEL * control
	if force.length() > MAX_FORCE:
		force = force.normalized() * MAX_FORCE
	state.apply_central_force(force)
	var up: Vector3 = state.transform.basis.y.normalized()
	var tilt_axis: Vector3 = up.cross(Vector3.UP)
	var tilt_dot: float = clampf(up.dot(Vector3.UP), -1.0, 1.0)
	var tilt_angle: float = acos(tilt_dot)
	if tilt_axis.length_squared() > 0.00001:
		var balance: Vector3 = tilt_axis.normalized() * tilt_angle * UPRIGHT_STRENGTH
		var damp: Vector3 = Vector3(state.angular_velocity.x, 0.0, state.angular_velocity.z) * UPRIGHT_DAMPING
		state.apply_torque(balance - damp)
	if wish_dir.length_squared() > 0.01:
		var body_forward: Vector3 = -state.transform.basis.z
		body_forward.y = 0.0
		if body_forward.length_squared() > 0.001:
			body_forward = body_forward.normalized()
			var signed_turn: float = body_forward.cross(wish_dir).y
			state.apply_torque(Vector3.UP * signed_turn * TURN_STRENGTH)
	if jump_requested:
		if grounded:
			state.apply_central_impulse(Vector3.UP * JUMP_IMPULSE)
			state.apply_torque_impulse(Vector3(move_input.y, 0.0, -move_input.x) * 0.85)
		jump_requested = false
	if state.linear_velocity.length() > 18.0:
		state.linear_velocity = state.linear_velocity.limit_length(18.0)
	if state.angular_velocity.length() > 12.0:
		state.angular_velocity = state.angular_velocity.limit_length(12.0)

func _animate_soft_body(delta: float) -> void:
	var speed: float = Vector2(linear_velocity.x, linear_velocity.z).length()
	_walk_time += delta * (2.0 + speed * 1.8)
	var amount: float = clampf(speed / MOVE_SPEED, 0.0, 1.0)
	var flop: float = sin(_walk_time) * 0.34 * amount
	if _limbs.size() >= 4:
		_limbs[0].rotation.z = deg_to_rad(76) + flop * 0.55
		_limbs[1].rotation.z = deg_to_rad(-76) - flop * 0.55
		_limbs[2].rotation.x = flop
		_limbs[3].rotation.x = -flop
	if _head:
		_head.rotation.z = sin(_walk_time * 0.55) * 0.055 * amount
	if _torso:
		_torso.rotation.z = sin(_walk_time * 0.5) * 0.035 * amount
