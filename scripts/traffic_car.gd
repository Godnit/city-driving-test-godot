extends Node3D

var lane_x: float = 0.0
var direction: float = -1.0
var drive_speed: float = 10.0
var wheel_nodes: Array[Node3D] = []
var wheel_spin: float = 0.0

func configure(x_value: float, direction_value: float, speed_value: float, start_z: float) -> void:
	lane_x = x_value
	direction = direction_value
	drive_speed = speed_value
	position = Vector3(lane_x, 0.04, start_z)
	rotation.y = 0.0 if direction < 0.0 else PI

func _ready() -> void:
	var packed := load("res://assets/models/traffic_hatchback.glb") as PackedScene
	if packed:
		var visual := packed.instantiate() as Node3D
		visual.rotation = Vector3.ZERO
		add_child(visual)
		_prepare_visuals(visual)
		for node_variant in visual.find_children("*Wheel*", "MeshInstance3D", true, false):
			wheel_nodes.append(node_variant as Node3D)

func _physics_process(delta: float) -> void:
	position.z += direction * drive_speed * delta
	wheel_spin += direction * drive_speed * delta / 0.32
	for wheel in wheel_nodes:
		if is_instance_valid(wheel):
			wheel.rotation.x = wheel_spin
	if direction < 0.0 and position.z < -690.0:
		position.z = 70.0
		reset_physics_interpolation()
	elif direction > 0.0 and position.z > 75.0:
		position.z = -685.0
		reset_physics_interpolation()

func _prepare_visuals(node: Node) -> void:
	if node is GeometryInstance3D:
		var geometry := node as GeometryInstance3D
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for index in range(mesh_instance.mesh.get_surface_count()):
				var source := mesh_instance.mesh.surface_get_material(index)
				if source is StandardMaterial3D:
					var material := source.duplicate() as StandardMaterial3D
					material.metallic = 0.0
					material.roughness = maxf(material.roughness, 0.72)
					material.clearcoat_enabled = false
					mesh_instance.set_surface_override_material(index, material)
	for child in node.get_children():
		_prepare_visuals(child)
