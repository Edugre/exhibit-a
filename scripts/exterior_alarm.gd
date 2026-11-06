extends Node3D
## "Please do not touch. She will know." The moment the Book leaves its stand, the museum finds out:
## a whisper, the owls' eyes, the librarian on the skyline turning to watch, the banner changing its
## mind, every pigeon in the air, and the floodlights going red under a bell and a far-off siren.
## Cosmetic, like the van: each peer reads the artifact state it already receives and plays the same
## scene, with no network traffic. It ends the moment a new heist puts the Book back.

const ALARM_COLOR := Color(1.0, 0.1, 0.07)
const RISE_TIME := 2.4
const FALL_TIME := 0.8
const BELL_DELAY := 0.9
const PULSE_SPEED := 3.4
const PULSE_DEPTH := 0.3
const LOOK_SPEED := 1.6
const LOOK_LIMIT := 1.0        # radians either way, so she stays on her ledge
const WORDS_HOLD := 2.2
const WORDS_FADE := 1.0
const FLOOD_NAMES: Array[String] = ["Flood", "Graze", "ArchGraze", "EndBay", "Crest", "DoorLamp", "Stairs"]

@export var lights_path: NodePath = ^"../Lights"
@export var pigeons_path: NodePath = ^"../Life/Pigeons"
@export var eyes_path: NodePath = ^"OwlEyes"
@export var mask_path: NodePath = ^"Librarian"
@export var whisper_path: NodePath = ^"Whisper"
@export var bell_path: NodePath = ^"Bell"
@export var siren_path: NodePath = ^"Siren"

var _raised: bool = false
var _level: float = 0.0
var _clock: float = 0.0
var _lamps: Array[Dictionary] = []
var _words: Label
var _words_age: float = -1.0


func _ready() -> void:
	RenderingServer.global_shader_parameter_set("exterior_alarm", 0.0)
	var layer := CanvasLayer.new()
	layer.layer = 40
	add_child(layer)
	_words = Label.new()
	_words.text = "She knows."
	_words.set_anchors_preset(Control.PRESET_CENTER)
	_words.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_words.grow_vertical = Control.GROW_DIRECTION_BOTH
	_words.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var serif := SystemFont.new()
	serif.font_names = PackedStringArray(["Palatino Linotype", "Georgia", "serif"])
	_words.add_theme_font_override("font", serif)
	_words.add_theme_font_size_override("font_size", 84)
	_words.add_theme_color_override("font_color", Color(0.94, 0.8, 0.52))
	_words.add_theme_color_override("font_outline_color", Color(0.12, 0.02, 0.02))
	_words.add_theme_constant_override("outline_size", 10)
	_words.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_words.visible = false
	layer.add_child(_words)
	get_node(eyes_path).visible = false
	_show_mask_eyes(false)


func _process(delta: float) -> void:
	var taken := GameState.artifact_state == GameState.ArtifactState.CARRIED \
			or GameState.artifact_state == GameState.ArtifactState.DROPPED \
			or GameState.artifact_state == GameState.ArtifactState.DELIVERED
	if taken != _raised:
		if taken:
			_raise()
		else:
			_stand_down()
	_clock += delta
	if _words_age >= 0.0:
		_update_words(delta)
	var target := 1.0 if _raised else 0.0
	if _level == target and not _raised:
		return
	_level = move_toward(_level, target, delta / (RISE_TIME if _raised else FALL_TIME))
	RenderingServer.global_shader_parameter_set("exterior_alarm", _level)
	var pulse := 1.0 - PULSE_DEPTH * (0.5 + 0.5 * sin(_clock * PULSE_SPEED))
	for lamp in _lamps:
		var light: Light3D = lamp.light
		light.light_color = (lamp.color as Color).lerp(ALARM_COLOR, _level)
		light.light_energy = float(lamp.energy) * lerpf(1.0, pulse * 1.15, _level)
	_turn_librarian(delta)


func _raise() -> void:
	_raised = true
	_clock = 0.0
	_gather_lamps()
	(get_node(whisper_path) as AudioStreamPlayer).play()
	get_node(eyes_path).visible = true
	_show_mask_eyes(true)
	_words.visible = true
	_words.modulate.a = 1.0
	_words_age = 0.0
	var pigeons := get_node_or_null(pigeons_path)
	if pigeons != null:
		pigeons.scatter_all()
	await get_tree().create_timer(BELL_DELAY).timeout
	if _raised:
		(get_node(bell_path) as AudioStreamPlayer3D).play()
		(get_node(siren_path) as AudioStreamPlayer3D).play()


func _stand_down() -> void:
	_raised = false
	(get_node(bell_path) as AudioStreamPlayer3D).stop()
	(get_node(siren_path) as AudioStreamPlayer3D).stop()
	get_node(eyes_path).visible = false
	_show_mask_eyes(false)
	_words.visible = false
	_words_age = -1.0
	(get_node(mask_path) as Node3D).rotation.y = 0.0


## The lights are read the first time the alarm goes up, while they still hold their own colours.
func _gather_lamps() -> void:
	if not _lamps.is_empty():
		return
	var lights := get_node_or_null(lights_path)
	if lights != null:
		for child in lights.get_children():
			for group in FLOOD_NAMES:
				if child.name.begins_with(group):
					_lamps.append({"light": child, "color": child.light_color, "energy": child.light_energy})
					break
	var rooms := get_tree().current_scene.find_child("NightLights", true, false)
	if rooms != null:
		for child in rooms.get_children():
			if child is OmniLight3D:
				_lamps.append({"light": child, "color": child.light_color, "energy": child.light_energy})


func _update_words(delta: float) -> void:
	_words_age += delta
	if _words_age > WORDS_HOLD:
		_words.modulate.a = clampf(1.0 - (_words_age - WORDS_HOLD) / WORDS_FADE, 0.0, 1.0)
	if _words_age > WORDS_HOLD + WORDS_FADE:
		_words.visible = false
		_words_age = -1.0


## She follows whoever is nearest, and goes back to facing the street when the alarm stops.
func _turn_librarian(delta: float) -> void:
	var mask := get_node(mask_path) as Node3D
	var wanted := 0.0
	var nearest := INF
	if _raised:
		for player: Node3D in get_tree().get_nodes_in_group("players"):
			var distance := player.global_position.distance_squared_to(mask.global_position)
			if distance < nearest:
				nearest = distance
				var to := player.global_position - mask.global_position
				wanted = clampf(atan2(to.x, to.z), -LOOK_LIMIT, LOOK_LIMIT)
	mask.rotation.y = move_toward(mask.rotation.y, wanted, LOOK_SPEED * delta)


func _show_mask_eyes(awake: bool) -> void:
	for eye in get_node(mask_path).get_children():
		if eye.name.begins_with("Eye"):
			eye.visible = awake
