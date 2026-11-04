extends CharacterBody3D
## First-person player. Each peer controls only its own player;
## the MultiplayerSynchronizer sends position/rotation to the other peer.

const WALK_SPEED := 5.0
const SNEAK_SPEED := 2.5
const JUMP_VELOCITY := 4.5
const MOUSE_SENSITIVITY := 0.002

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D

@onready var interact_ray: RayCast3D = $Head/Camera3D/InteractRay

var current_interactable: Node = null


func _enter_tree() -> void:
	# Must run before _ready so the synchronizer knows who owns this node.
	# The host names each player after its peer id (e.g. "1", "1593872234").
	set_multiplayer_authority(name.to_int())


func _ready() -> void:
	camera.current = is_multiplayer_authority()
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
	elif event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE  # Esc frees the mouse
	elif event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED  # click to recapture


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
		print("Looking at: ", current_interactable)
	

	
