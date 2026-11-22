class_name DisplayCase
extends Node3D
## A glass display case that can be broken into with the crowbar (stretch goal: scoring). The prize inside is
## a Loot ("Prize"), out of reach of the interact ray behind the glass collider until the glass goes.
##
## The host decides: pry() checks the heist is on and the case is whole, plays the crowbar's creak on every
## peer, and a moment later breaks it: `broken` (synced, so a late joiner sees it too) hides the glass and
## drops its collider. The crash is a noise every guard within BREAK_NOISE metres comes to look at, and the
## librarian knows the sound of her own cases: she hears it anywhere in the museum and hurries over, as she
## does for a staff bell, and "She's coming…" shows on both screens.
## Who may pry, and from how close, is checked by the hotbar's request (Hotbar._request_pry).

const BREAK_NOISE := 10.0  # a thrown heel is 8 m: breaking a case is louder
const PRY_TIME := 0.55     # the creak before the glass goes
const PRY_SOUND := preload("res://assets/loot/crowbar_pry.wav")
const GLASS_SOUND := preload("res://assets/loot/glass_break.wav")

## Synced. True once the glass is broken.
@export var broken := false:
	set(value):
		broken = value
		_apply()

var _breaking := false  # host: the creak is playing


func _ready() -> void:
	add_to_group("display_cases")
	_apply()


## The case a collider belongs to (the glass, the cabinet), or null.
static func of(node: Node) -> DisplayCase:
	for i in 3:
		if node == null:
			return null
		if node is DisplayCase:
			return node
		node = node.get_parent()
	return null


## The prize inside, or null.
func prize() -> Loot:
	return get_node_or_null(^"Prize") as Loot


# --- Host only ---------------------------------------------------------------------

func pry() -> void:
	if not multiplayer.is_server() or broken or _breaking or GameState.phase != GameState.Phase.PLAYING:
		return
	_breaking = true
	_play_break.rpc()
	await get_tree().create_timer(PRY_TIME).timeout
	if not is_inside_tree():
		return
	_breaking = false
	broken = true
	NoiseSystem.emit_noise(global_position, BREAK_NOISE)
	for boss in get_tree().get_nodes_in_group("boss"):
		boss.hear_bell(global_position)


# --- Every peer --------------------------------------------------------------------

func _apply() -> void:
	if not is_node_ready():
		return
	($GlassMesh as Node3D).visible = not broken
	for shape: CollisionShape3D in $Glass.find_children("*", "CollisionShape3D", false, false):
		shape.set_deferred("disabled", broken)


## The creak, then the crash and a burst of shards, heard and seen by everyone.
@rpc("authority", "call_local", "reliable")
func _play_break() -> void:
	_sound(PRY_SOUND, global_position + Vector3(0.0, 1.0, 0.0))
	await get_tree().create_timer(PRY_TIME).timeout
	if not is_inside_tree():
		return
	var glass := $Glass/Shape as CollisionShape3D
	var box := glass.shape as BoxShape3D
	_sound(GLASS_SOUND, glass.global_position)
	_shards(glass.global_position, box.size)
	get_tree().call_group("boss", "warn")


func _sound(stream: AudioStream, at: Vector3) -> void:
	var player := AudioStreamPlayer3D.new()
	player.stream = stream
	player.unit_size = 9.0
	player.max_distance = 45.0
	add_child(player)
	player.global_position = at
	player.play()
	player.finished.connect(player.queue_free)


func _shards(at: Vector3, size: Vector3) -> void:
	var motion := ParticleProcessMaterial.new()
	motion.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	motion.emission_box_extents = size * 0.5
	motion.direction = Vector3(0.0, 1.0, 0.0)
	motion.spread = 70.0
	motion.initial_velocity_min = 1.2
	motion.initial_velocity_max = 3.2
	motion.gravity = Vector3(0.0, -9.8, 0.0)
	motion.angular_velocity_min = -540.0
	motion.angular_velocity_max = 540.0
	motion.scale_min = 0.4
	motion.scale_max = 1.3
	var look := StandardMaterial3D.new()
	look.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	look.albedo_color = Color(0.82, 0.92, 1.0, 0.55)
	look.metallic_specular = 1.0
	look.roughness = 0.05
	look.cull_mode = BaseMaterial3D.CULL_DISABLED
	look.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	var quad := QuadMesh.new()
	quad.size = Vector2(0.06, 0.04)
	quad.material = look
	var burst := GPUParticles3D.new()
	burst.process_material = motion
	burst.draw_pass_1 = quad
	burst.amount = 60
	burst.lifetime = 1.1
	burst.one_shot = true
	burst.explosiveness = 0.92
	burst.visibility_aabb = AABB(-size - Vector3.ONE * 2.0, (size + Vector3.ONE * 2.0) * 2.0)
	add_child(burst)
	burst.global_position = at
	burst.emitting = true
	burst.finished.connect(burst.queue_free)
