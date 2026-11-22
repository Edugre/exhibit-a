class_name ControlsCard
extends PanelContainer
## The objective and the controls, where a new player can find them: beside the main menu, for the first
## seconds of every heist, and whenever they hold Tab (the HUD shows it then). It says what to do and which
## keys do it, never how to solve a room. Built in code, like the other bits of HUD.

const OBJECTIVE := "Steal the Last Book of Alexandria from the vault and get it into your van before the museum opens. If the librarian catches either of you, the heist is over. Loot only counts if you get away."
const CONTROLS := [
	["Move / look", "W A S D / mouse"],
	["Jump / sneak", "Space / Ctrl"],
	["Pick up, pocket loot, drop the book", "E"],
	["Pick a hotbar slot", "1 – 4 / mouse wheel"],
	["Use what's in your hand", "Left click"],
	["Fire the jammer from anywhere", "Q"],
	["Put down what's in your hand", "G"],
	["Show this card", "Hold Tab"],
	["Free the mouse", "Esc"],
]
const WIDTH := 460.0
const INK := Color(0.96, 0.92, 0.84)
const GOLD := Color(0.94, 0.8, 0.52)
const DIM := Color(0.78, 0.74, 0.66)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.05, 0.045, 0.04, 0.82)
	style.border_color = Color(0.85, 0.72, 0.45, 0.55)
	style.set_border_width_all(2)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(18)
	add_theme_stylebox_override("panel", style)
	custom_minimum_size = Vector2(WIDTH, 0)

	var serif := SystemFont.new()
	serif.font_names = PackedStringArray(["Palatino Linotype", "Georgia", "serif"])
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(column)

	column.add_child(_label("THE JOB", 26, GOLD, serif))
	var objective := _label(OBJECTIVE, 17, INK)
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective.custom_minimum_size.x = WIDTH - 44.0  # a wrapping label needs a width, or it wraps every letter
	column.add_child(objective)
	column.add_child(_label("CONTROLS", 20, GOLD, serif))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 1)
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(grid)
	for row: Array in CONTROLS:
		var what := _label(row[0], 16, DIM)
		what.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_child(what)
		grid.add_child(_label(row[1], 16, INK))


func _label(text: String, size: int, colour: Color, font: Font = null) -> Label:
	var label := Label.new()
	label.text = text
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", colour)
	if font:
		label.add_theme_font_override("font", font)
	return label
