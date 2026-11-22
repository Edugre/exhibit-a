class_name Loot
extends StaticBody3D
## A small valuable lying about the museum, or the prize inside a display case (asset plan: stretch loot).
## Pressing E on it pockets it into the team's shared haul (GameState.loot_total); it doesn't take a hotbar
## slot. The haul only counts if the team gets away with the book.
##
## The host decides: interact() checks the heist is on and it isn't already gone, adds its value to the haul
## and marks it `taken`, which the MultiplayerSynchronizer copies, so on every peer it vanishes (and a late
## joiner never sees it). The one who pocketed it gets a little "+$300" and a chink.
## A case's prize sits behind the case's glass collider, so the interact ray can't reach it until the glass
## is broken (DisplayCase).
##
## It's on collision layer 3 only: players walk through it, the interact ray (mask 1-3) finds it.

const CHINK := preload("res://assets/loot/chink.wav")
## Every GLINT_EVERY seconds or so a little star of light flashes on it, so loot reads as something to
## take and the props around it don't. Each piece keeps its own rhythm.
const GLINT_EVERY := 2.6
const GLINT_TIME := 0.45

## What the haul calls it.
@export var display_name := "Trinket"
## Dollars, added to the haul.
@export var value := 100
## A line for the toast when it's pocketed, under the name and value.
@export var note := ""

## Synced. True once it's in someone's pocket.
@export var taken := false:
	set(v):
		taken = v
		_apply()

var _glint: Sprite3D
var _glint_clock := 0.0


func _ready() -> void:
	add_to_group("interactable")
	add_to_group("loot")
	collision_layer = 4
	collision_mask = 0
	_add_glint()
	_apply()


func _process(delta: float) -> void:
	if taken:
		return
	_glint_clock = fmod(_glint_clock + delta, GLINT_EVERY)
	var t := _glint_clock / GLINT_TIME
	_glint.modulate.a = sin(t * PI) if t < 1.0 else 0.0
	_glint.rotation.z = t * 0.8


func _add_glint() -> void:
	var gradient := Gradient.new()
	gradient.offsets = PackedFloat32Array([0.0, 0.18, 1.0])
	gradient.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 0.92, 0.7, 0.55), Color(1, 0.85, 0.5, 0)])
	var star := GradientTexture2D.new()
	star.gradient = gradient
	star.fill = GradientTexture2D.FILL_RADIAL
	star.fill_from = Vector2(0.5, 0.5)
	star.fill_to = Vector2(1.0, 0.5)
	star.width = 64
	star.height = 64
	_glint = Sprite3D.new()
	_glint.texture = star
	_glint.pixel_size = 0.0035
	_glint.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_glint.shaded = false
	_glint.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED
	_glint.modulate = Color(1, 1, 1, 0)
	_glint.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var top := 0.06
	var shape := get_node_or_null(^"Shape") as CollisionShape3D
	if shape and shape.shape is BoxShape3D:
		top = shape.position.y + (shape.shape as BoxShape3D).size.y * 0.5
	_glint.position = Vector3(0.0, top + 0.02, 0.0)
	add_child(_glint)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(get_path()) if is_inside_tree() else name)
	_glint_clock = rng.randf() * GLINT_EVERY


## Host only, from the player's interact request (it has already checked who and how far).
func interact(peer_id: int) -> void:
	if not multiplayer.is_server() or taken or GameState.phase != GameState.Phase.PLAYING:
		return
	taken = true
	GameState.add_loot(value)
	if peer_id == multiplayer.get_unique_id():
		_pocketed()
	else:
		_pocketed.rpc_id(peer_id)


## What the interact prompt says while you look at it.
func prompt() -> String:
	return "Press E to pocket: %s ($%s)" % [display_name, Loot.dollars(value)]


static func dollars(amount: int) -> String:
	var digits := str(absi(amount))
	var out := ""
	while digits.length() > 3:
		out = "," + digits.right(3) + out
		digits = digits.left(digits.length() - 3)
	return digits + out


func _apply() -> void:
	if not is_node_ready():
		return
	visible = not taken
	for shape: CollisionShape3D in find_children("*", "CollisionShape3D", false, false):
		shape.set_deferred("disabled", taken)


## The one who pocketed it: a chink and a toast.
@rpc("authority", "call_remote", "reliable")
func _pocketed() -> void:
	var chink := AudioStreamPlayer.new()
	chink.stream = CHINK
	chink.volume_db = -6.0
	get_tree().root.add_child(chink)
	chink.play()
	chink.finished.connect(chink.queue_free)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud and hud.has_method("toast"):
		hud.toast("+$%s  %s" % [Loot.dollars(value), display_name], note)
