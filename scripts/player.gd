extends CharacterBody3D
## First-person player. Each peer controls only its own player;
## the MultiplayerSynchronizer sends position/rotation to the other peer.

const WALK_SPEED := 5.0
const SNEAK_SPEED := 2.5
const JUMP_VELOCITY := 4.5
const MOUSE_SENSITIVITY := 0.002
const INTERACT_RANGE := 4.0
const INTERACT_PROMPT := "Press E to interact"
const DROP_PROMPT := "Press E to drop"
## Physics runs 60 times a second, far less often than a fast screen draws, so the camera and a
## teammate's model are drawn between steps. Only what's seen moves; the body and its sync don't change.
const GLIDE_SPEED := 22.0
const SNAP_DISTANCE := 3.0

## Accent colour, picked by the host and set before this node enters the tree.
var variant: int = 0

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var interact_ray: RayCast3D = $Head/Camera3D/InteractRay
@onready var interact_prompt: Label = $PromptLayer/InteractPrompt
@onready var model: Node3D = $Model

var current_interactable: Node = null
var holding: bool = false
var _view_from: Vector3
var _view_to: Vector3
var _head_offset: Vector3
var _model_at: Vector3
var _model_offset: Vector3


func _enter_tree() -> void:
	# Must run before _ready so the synchronizer knows who owns this node.
	# The host names each player after its peer id (e.g. "1", "1593872234").
	set_multiplayer_authority(name.to_int())
	add_to_group("players")


func _ready() -> void:
	camera.current = is_multiplayer_authority()
	model.variant = variant
	model.visible = not is_multiplayer_authority()  # the first-person camera sits inside this body
	if is_multiplayer_authority():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	interact_ray.add_exception(self)
	_head_offset = head.position
	_model_offset = model.position
	reset_view_smoothing()


func _unhandled_input(event: InputEvent) -> void:
	if not is_multiplayer_authority():
		return

	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
		head.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
		head.rotation.x = clampf(head.rotation.x, deg_to_rad(-89.0), deg_to_rad(89.0))
	elif event.is_action_pressed("interact") and holding:
		get_tree().get_first_node_in_group("artifact").request_drop()
	elif event.is_action_pressed("interact") and current_interactable != null:
		_request_interact.rpc_id(1, current_interactable.get_path())
		
	elif event.is_action_pressed("throw") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_request_throw.rpc_id(1)
		
	elif event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE  # Esc frees the mouse
	elif event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED  # click to recapture


func _process(delta: float) -> void:
	_glide_between_steps(delta)

	# You only vanish from your own view while you're looking out through this body.
	if is_multiplayer_authority():
		model.visible = not camera.current

	# The host owns who holds the artifact; every peer just shows it.
	holding = GameState.artifact_state == GameState.ArtifactState.CARRIED and GameState.artifact_holder == name.to_int()
	if holding != model.carrying:
		model.carrying = holding

	# Every peer can see for itself who's on a plinth, so being a statue needs no network traffic.
	model.statue = not holding and _is_on_plinth()


func _is_on_plinth() -> bool:
	for plate: PressurePlate in get_tree().get_nodes_in_group("plates"):
		if plate.overlaps_body(self):
			return true
	return _is_on_statue_spot()


func _is_on_statue_spot() -> bool:
	for spot: Area3D in get_tree().get_nodes_in_group("statue_spots"):
		if spot.overlaps_body(self):
			return true
	return false


## True while standing on one of the empty plinths outside with nothing to give them away. The guard
## takes them for one more statue. The plates indoors don't count: she knows what belongs on those.
func is_posing_as_statue() -> bool:
	return not holding and _is_on_statue_spot()


func _glide_between_steps(delta: float) -> void:
	if is_multiplayer_authority():
		var between := _view_from.lerp(_view_to, Engine.get_physics_interpolation_fraction())
		head.global_position = between + global_basis * _head_offset
		return
	_model_at = _model_at.lerp(global_position, 1.0 - exp(-GLIDE_SPEED * delta))
	if _model_at.distance_to(global_position) > SNAP_DISTANCE:
		_model_at = global_position
	model.global_position = _model_at + _model_offset


## Jump straight to where the body is, after a teleport.
func reset_view_smoothing() -> void:
	_view_from = global_position
	_view_to = global_position
	_model_at = global_position


func _physics_process(delta: float) -> void:
	if not is_multiplayer_authority():
		return
		
	_update_interact_target()

	if not is_on_floor():
		velocity += get_gravity() * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	var speed := SNEAK_SPEED if Input.is_action_pressed("sneak") else WALK_SPEED
	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

	if direction:
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed)
		velocity.z = move_toward(velocity.z, 0.0, speed)

	move_and_slide()
	_view_from = _view_to
	_view_to = global_position
	if _view_from.distance_to(_view_to) > SNAP_DISTANCE:
		_view_from = _view_to


func _update_interact_target() -> void:
	var new_target: Node = null

	if interact_ray.is_colliding():
		var collider := interact_ray.get_collider() as Node
		if collider and collider.is_in_group("interactable"):
			new_target = collider

	current_interactable = new_target
	interact_prompt.visible = holding or current_interactable != null
	interact_prompt.text = DROP_PROMPT if holding else INTERACT_PROMPT
		
@rpc("any_peer", "call_local", "reliable")
func _request_interact(target_path: NodePath) -> void:
	if not multiplayer.is_server():
		return

	var sender_id := multiplayer.get_remote_sender_id()
	if sender_id != name.to_int():
		return
	if holding:
		return  # hands full: put the book down first

	var target := get_node_or_null(target_path)
	if target == null or not target.is_in_group("interactable"):
		return
	if not target.has_method("interact"):
		return
	if global_position.distance_to(target.global_position) > INTERACT_RANGE:
		return

	target.interact(sender_id)

@rpc("any_peer", "call_local", "reliable")
func _request_throw() -> void:
	if not multiplayer.is_server():
		return

	var sender_id := multiplayer.get_remote_sender_id()
	if sender_id != name.to_int():
		return

	for throwable: Throwable in get_tree().get_nodes_in_group("throwables"):
		if throwable.holder_id == sender_id:
			throwable.throw(-head.global_basis.z)
			return

## Host → owner: move this player (used on restart). The owner applies it,
## and the synchronizer carries the new position to everyone.
@rpc("any_peer", "call_local", "reliable")
func teleport(to: Vector3) -> void:
	if multiplayer.get_remote_sender_id() != 1:
		return  # only the host may teleport players
	global_position = to
	reset_view_smoothing()
	velocity = Vector3.ZERO
	rotation.y = 0.0
	head.rotation.x = 0.0
