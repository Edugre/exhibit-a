extends PanelContainer
## The end screen: the Book's library card, typed out line by line, then stamped.
## Only shows what GameState already decided. The fine is worked out from today's date.

const CARD_SIZE := Vector2(760.0, 470.0)
const DUE_YEAR_BC := 48        # the year the Library burned
const TYPE_SPEED := 46.0       # characters a second
const STAMP_SIZE := Vector2(340.0, 134.0)
const STAMP_SPOT := Vector2(340.0, 226.0)
const STAMP_TILT := -0.15
const INK := Color(0.1, 0.1, 0.2)
const RED_INK := Color(0.55, 0.11, 0.09)

const CARD: Texture2D = preload("res://ui/library_card.png")
const WITHDRAWN: Texture2D = preload("res://ui/stamp_withdrawn.png")
const REVOKED: Texture2D = preload("res://ui/stamp_revoked.png")
const CLOSED: Texture2D = preload("res://ui/stamp_closed.png")

@export var stamp_sound_path: NodePath

@onready var _lines: VBoxContainer = $VBoxContainer
@onready var _result: Label = %ResultLabel
@onready var _reason: Label = %ReasonLabel
@onready var _restart: Button = %RestartButton

var _rows: Array[Label] = []
var _stamp: TextureRect
var _typing: Tween


func _ready() -> void:
	var paper := StyleBoxTexture.new()
	paper.texture = CARD
	paper.content_margin_left = 34.0
	paper.content_margin_right = 34.0
	paper.content_margin_top = 72.0
	paper.content_margin_bottom = 40.0
	add_theme_stylebox_override("panel", paper)
	custom_minimum_size = CARD_SIZE
	_lines.add_theme_constant_override("separation", 0)
	var typewriter := SystemFont.new()
	typewriter.font_names = PackedStringArray(["Courier New", "Liberation Mono", "DejaVu Sans Mono", "monospace"])
	typewriter.font_weight = 600
	for i in 4:
		var row := Label.new()
		_lines.add_child(row)
		_lines.move_child(row, i + 1)
		_rows.append(row)
	_rows.push_front(_result)
	_rows.append(_reason)
	for row in _rows:
		row.custom_minimum_size.y = 38.0
		row.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		row.add_theme_font_override("font", typewriter)
		row.add_theme_font_size_override("font_size", 21)
		row.add_theme_color_override("font_color", INK)
	_result.add_theme_color_override("font_color", RED_INK)
	_result.add_theme_font_size_override("font_size", 24)
	_reason.clip_text = true
	_restart.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_restart.size_flags_vertical = Control.SIZE_SHRINK_END | Control.SIZE_EXPAND
	var overlay := Control.new()
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(overlay)
	_stamp = TextureRect.new()
	_stamp.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_stamp.size = STAMP_SIZE
	_stamp.position = STAMP_SPOT
	_stamp.pivot_offset = STAMP_SIZE * 0.5
	_stamp.rotation = STAMP_TILT
	_stamp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.add_child(_stamp)


## Fill in the card for this ending and play it out.
func stamp_card(won: bool, reason: String, seconds_taken: float, caught_with_book: bool, out_of_time: bool) -> void:
	var fine: int = Time.get_date_dict_from_system().year + DUE_YEAR_BC - 1    # there was no year zero
	var years := _with_comma(fine)
	_rows[1].text = "  TITLE    The Last Book of Alexandria"
	_rows[2].text = "  DUE      %d B.C." % DUE_YEAR_BC
	if won:
		_rows[3].text = "  FINE     %s years. Unpaid." % years
		_rows[4].text = "  OUT IN   %d:%02d. A library record." % [int(seconds_taken) / 60, int(seconds_taken) % 60]
	else:
		_rows[3].text = "  FINE     %s years and counting" % years
		_rows[4].text = "  BOOK     %s" % ("Checked out by the guard." if caught_with_book else "Still on the shelf.")
	_rows[5].text = "  NOTE     %s" % reason
	_stamp.texture = WITHDRAWN if won else (CLOSED if out_of_time else REVOKED)
	_stamp.visible = false
	var fill := clampf(get_viewport_rect().size.y / 1080.0, 1.0, 1.6)
	pivot_offset = size * 0.5
	scale = Vector2.ONE * fill
	if _typing != null:
		_typing.kill()
	_typing = create_tween()
	for row in _rows:
		row.visible_ratio = 0.0
		_typing.tween_property(row, "visible_ratio", 1.0, row.text.length() / TYPE_SPEED)
	_typing.tween_interval(0.35)
	_typing.tween_callback(_slam)


func _slam() -> void:
	_stamp.visible = true
	_stamp.scale = Vector2.ONE * 3.2
	_stamp.modulate.a = 0.0
	var fall := create_tween().set_parallel()
	fall.tween_property(_stamp, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	fall.tween_property(_stamp, "modulate:a", 1.0, 0.1)
	await fall.finished
	if not stamp_sound_path.is_empty():
		(get_node(stamp_sound_path) as AudioStreamPlayer).play()
	var rest := position
	var jolt := create_tween()
	jolt.tween_property(self, "position", rest + Vector2(3.0, 5.0), 0.04)
	jolt.tween_property(self, "position", rest, 0.1)


func _with_comma(value: int) -> String:
	return "%d,%03d" % [value / 1000, value % 1000]
