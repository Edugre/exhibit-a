extends CharacterBody3D
## First-person player. Each peer controls only its own player;
## the MultiplayerSynchronizer sends position/rotation to the other peer.

const WALK_SPEED := 5.0
const SNEAK_SPEED := 2.5
const JUMP_VELOCITY := 4.5
const MOUSE_SENSITIVITY := 0.002
const INTERACT_RANGE := 4.0

## Accent colour, picked by the host and set before this node enters the tree.
var variant: int = 0

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var interact_ray: RayCast3D = $Head/Camera3D/InteractRay
@onready var interact_prompt: Label = $PromptLayer/InteractPrompt
@onready var model: Node3D = $Model

var current_interactable: Node = null


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


func _unhandled_input(event: InputEvent) -> void:
	if not is_multiplayer_authority():
		return

	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
		head.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
		head.rotation.x = clampf(head.rotation.x, deg_to_rad(-89.0), deg_to_rad(89.0))
	elif event.is_action_pressed("interact") and current_interactable != null:
		_request_interact.rpc_id(1, current_interactable.get_path())
		
	elif event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE  # Esc frees the mouse
	elif event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED  # click to recapture


func _process(_delta: float) -> void:
	# You only vanish from your own view while you're looking out through this body.
	if is_multiplayer_authority():
		model.visible = not camera.current

	# The host owns who holds the artifact; every peer just shows it.
	var holding := GameState.artifact_state == GameState.ArtifactState.CARRIED and GameState.artifact_holder == name.to_int()
	if holding != model.carrying:
		model.carrying = holding


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


func _update_interact_target() -> void:
	var new_target: Node = null

	if interact_ray.is_colliding():
		var collider := interact_ray.get_collider() as Node
		if collider and collider.is_in_group("interactable"):
			new_target = collider

	if new_target != current_interactable:
		current_interactable = new_target
		interact_prompt.visible = current_interactable != null
		
@rpc("any_peer", "call_local", "reliable")
func _request_interact(target_path: NodePath) -> void:
	if not multiplayer.is_server():
		return

	var sender_id := multiplayer.get_remote_sender_id()
	if sender_id != name.to_int():
		return

	var target := get_node_or_null(target_path)
	if target == null or not target.is_in_group("interactable"):
		return
	if not target.has_method("interact"):
		return
	if global_position.distance_to(target.global_position) > INTERACT_RANGE:
		return

	target.interact(sender_id)


## Host → owner: move this player (used on restart). The owner applies it,
## and the synchronizer carries the new position to everyone.
@rpc("any_peer", "call_local", "reliable")
func teleport(to: Vector3) -> void:
	if multiplayer.get_remote_sender_id() != 1:
		return  # only the host may teleport players
	global_position = to
	velocity = Vector3.ZERO
	rotation.y = 0.0
	head.rotation.x = 0.0
