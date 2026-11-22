class_name Hotbar
extends Node
## A player's hotbar: four slots for whatever they've picked up (the throwables and the Signal Jammer).
## A child of each player.
##
## Who holds what, and in which slot, belongs to the host (Carryable.holder_id and .slot). Which slot is in
## hand is the owner's own choice, player.selected_slot, synced by the player's MultiplayerSynchronizer
## like their movement; it only decides what's drawn and what the buttons act on. Throwing and dropping are
## asked of the host, which checks the sender holds that item.
##
## Owner's keys: 1-4 or the mouse wheel pick a slot, the throw button (left click) throws the throwable in
## hand or fires the jammer, the drop key (G) puts the item in hand down. A new pickup goes into the first
## free slot, and into your hand if the one you're on is empty.

const SLOTS := Carryable.SLOTS
const SLOT_PX := 84
const ICON_PX := 128
const ICON_ANGLE := Vector3(-0.7, 0.7, 0.0)  # how every icon sits; none of them turn
const FULL_TEXT := "Hotbar full: drop something [G]"
const PRY_TEXT := "Left click: pry it open (loud!)"
const PRY_REACH := 2.6  # metres from the player to the middle of the case

const BG := Color(0.06, 0.05, 0.04, 0.62)
const BORDER := Color(0.85, 0.72, 0.45, 0.35)
const BORDER_PICKED := Color(0.98, 0.82, 0.46, 1.0)
const INK := Color(0.96, 0.92, 0.84)

@onready var player: CharacterBody3D = get_parent()

var _root: Control
var _name_label: Label
var _hint_label: Label
var _cells: Array[Dictionary] = []  # per slot: panel, spin, holder, camera, count, item
var _known := {}  # instance ids of what we held last frame, to notice a new pickup
var _style_idle: StyleBoxFlat
var _style_picked: StyleBoxFlat


func _ready() -> void:
	if player.is_multiplayer_authority():
		_build_ui()


## The item in this player's hand right now, on any peer, or null.
func in_hand() -> Carryable:
	var item := Carryable.in_slot(get_tree(), player.name.to_int(), player.selected_slot)
	if item != null and item.in_hand():
		return item
	return null


func is_full() -> bool:
	return Carryable.free_slot(get_tree(), player.name.to_int()) < 0


# --- Owner ---------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not player.is_multiplayer_authority() or Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
	for index in SLOTS:
		if event.is_action_pressed("slot_%d" % (index + 1)):
			_select(index)
			return
	if event.is_action_pressed("slot_next"):
		_select(posmod(player.selected_slot + 1, SLOTS))
	elif event.is_action_pressed("slot_prev"):
		_select(posmod(player.selected_slot - 1, SLOTS))
	elif event.is_action_pressed("throw"):
		_use_hand()
	elif event.is_action_pressed("drop_item"):
		var item := in_hand()
		if item:
			_request_drop.rpc_id(1, item.get_path())


func _select(index: int) -> void:
	player.selected_slot = index


func _use_hand() -> void:
	var item := in_hand()
	if item is Throwable:
		_request_throw.rpc_id(1, item.get_path())
	elif item is JammerPickup:
		(player.get_node(^"Gadget") as GadgetJammer).request_use()
	elif item is Crowbar:
		var target := pry_target()
		if target:
			_request_pry.rpc_id(1, item.get_path(), target.get_path())
		else:
			(item as Crowbar).swing()  # a swing at nothing, just for the feel


## Owner: the unbroken display case the crowbar in hand is aimed at, or null.
func pry_target() -> DisplayCase:
	if not (in_hand() is Crowbar):
		return null
	var ray := player.get_node(^"Head/Camera3D/InteractRay") as RayCast3D
	if not ray.is_colliding():
		return null
	var case := DisplayCase.of(ray.get_collider() as Node)
	return case if case != null and not case.broken else null


func _process(delta: float) -> void:
	if not player.is_multiplayer_authority():
		return
	var me := player.name.to_int()
	var held := Carryable.held_by(get_tree(), me)

	# Something new in the bar goes into your hand if your hand was empty
	var now := {}
	for item in held:
		now[item.get_instance_id()] = true
		if not _known.has(item.get_instance_id()) and Carryable.in_slot(get_tree(), me, player.selected_slot) == null:
			player.selected_slot = item.slot
	_known = now

	if _root:
		_refresh_ui()


# --- Host only ------------------------------------------------------------------------

@rpc("any_peer", "call_local", "reliable")
func _request_throw(item_path: NodePath) -> void:
	if not multiplayer.is_server():
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != player.name.to_int() or player.get("holding"):
		return  # your own hotbar only, and not with the book in both hands
	var item := get_node_or_null(item_path) as Throwable
	if item == null or item.holder_id != sender:
		return
	item.throw(-(player.get_node(^"Head") as Node3D).global_basis.z)


@rpc("any_peer", "call_local", "reliable")
func _request_pry(crowbar_path: NodePath, case_path: NodePath) -> void:
	if not multiplayer.is_server():
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != player.name.to_int() or player.get("holding"):
		return
	var crowbar := get_node_or_null(crowbar_path) as Crowbar
	if crowbar == null or crowbar.holder_id != sender or crowbar.slot != player.get("selected_slot"):
		return  # it has to be yours, and in your hand
	var case := get_node_or_null(case_path) as DisplayCase
	if case == null or case.broken:
		return
	if player.global_position.distance_to(case.global_position) > PRY_REACH:
		return
	case.pry()
	crowbar.swung.rpc()


@rpc("any_peer", "call_local", "reliable")
func _request_drop(item_path: NodePath) -> void:
	if not multiplayer.is_server():
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != player.name.to_int():
		return
	var item := get_node_or_null(item_path) as Carryable
	if item == null or item.holder_id != sender:
		return
	item.drop_from(player)


# --- The bar on screen (owner only) ----------------------------------------------------

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 4
	add_child(layer)
	_root = VBoxContainer.new()
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_theme_constant_override("separation", 6)
	layer.add_child(_root)

	_name_label = _label(18, HORIZONTAL_ALIGNMENT_CENTER)
	_root.add_child(_name_label)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(row)
	_hint_label = _label(13, HORIZONTAL_ALIGNMENT_CENTER)
	_hint_label.modulate = Color(1, 1, 1, 0.7)
	_root.add_child(_hint_label)

	_style_idle = _style(BORDER, 2, BG)
	_style_picked = _style(BORDER_PICKED, 3, Color(0.16, 0.12, 0.07, 0.75))
	for index in SLOTS:
		row.add_child(_make_cell(index))

	_root.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, 14)
	_root.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_root.grow_vertical = Control.GROW_DIRECTION_BEGIN


func _make_cell(index: int) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(SLOT_PX, SLOT_PX)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel", _style_idle)

	# The icon: the item's own model, in a little world of its own, lit and still
	var view_box := SubViewportContainer.new()
	view_box.stretch = true
	view_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(view_box)
	var view := SubViewport.new()
	view.size = Vector2i(ICON_PX, ICON_PX)
	view.own_world_3d = true
	view.transparent_bg = true
	view.msaa_3d = Viewport.MSAA_4X
	view_box.add_child(view)
	var key_light := DirectionalLight3D.new()
	key_light.rotation = Vector3(-0.7, 0.6, 0.0)
	key_light.light_energy = 1.4
	view.add_child(key_light)
	var fill := DirectionalLight3D.new()
	fill.rotation = Vector3(-0.2, PI + 0.8, 0.0)
	fill.light_energy = 0.5
	fill.light_color = Color(0.7, 0.8, 1.0)
	view.add_child(fill)
	var camera := Camera3D.new()
	camera.fov = 30.0
	view.add_child(camera)
	var spin := Node3D.new()
	spin.rotation = ICON_ANGLE
	view.add_child(spin)
	var holder := Node3D.new()
	spin.add_child(holder)

	var key := _label(13, HORIZONTAL_ALIGNMENT_LEFT)
	key.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	key.text = " %d" % (index + 1)
	key.modulate = Color(1, 1, 1, 0.75)
	panel.add_child(key)
	var count := _label(14, HORIZONTAL_ALIGNMENT_RIGHT)
	count.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	panel.add_child(count)

	_cells.append({"panel": panel, "spin": spin, "holder": holder, "camera": camera, "count": count, "item": null})
	return panel


func _refresh_ui() -> void:
	var me := player.name.to_int()
	var book := player.get("holding") as bool
	var hand := in_hand()
	for index in SLOTS:
		var cell := _cells[index]
		var item := Carryable.in_slot(get_tree(), me, index)
		if item != cell.item:
			_set_icon(cell, item)
		var picked: bool = index == player.selected_slot
		(cell.panel as PanelContainer).add_theme_stylebox_override("panel", _style_picked if picked else _style_idle)
		var count := cell.count as Label
		count.text = "%d/%d " % [item.charges, JammerPickup.MAX_CHARGES] if item is JammerPickup else ""
	_root.modulate.a = 0.45 if book else 1.0

	if book:
		_name_label.text = "Both hands on the book"
		_hint_label.text = "E: put the book down"
	elif hand == null:
		_name_label.text = ""
		_hint_label.text = "1-4 / wheel: pick a slot" if Carryable.held_by(get_tree(), me).size() > 0 else ""
	else:
		_name_label.text = hand.display_name
		var use := "LMB: throw"
		if hand is JammerPickup:
			use = "LMB / Q: jam"
		elif hand is Crowbar:
			use = "LMB: pry a case open (loud)"
		_hint_label.text = "%s   ·   G: put down   ·   1-4 / wheel: pick a slot" % use


func _set_icon(cell: Dictionary, item: Carryable) -> void:
	cell.item = item
	var holder := cell.holder as Node3D
	for child in holder.get_children():
		child.queue_free()
	if item == null:
		return
	var source := item.get_node_or_null(^"Model") as Node3D
	if source == null:
		return
	var copy := source.duplicate() as Node3D
	copy.visible = true
	copy.transform = source.transform
	holder.add_child(copy)
	holder.position = Vector3.ZERO
	# Frame it: centre it on the turning pivot and back the camera off to fit
	var box := _bounds(copy, holder.global_transform.affine_inverse())
	holder.position = -box.get_center()
	var radius := maxf(box.size.length() * 0.5, 0.05)
	var camera := cell.camera as Camera3D
	var distance := radius / tan(deg_to_rad(camera.fov * 0.5)) * 1.05
	camera.position = Vector3(0.0, distance * 0.18, distance)
	camera.look_at(Vector3.ZERO)


func _bounds(node: Node, to_local: Transform3D) -> AABB:
	var box := AABB()
	var first := true
	for inst: VisualInstance3D in node.find_children("*", "VisualInstance3D", true, false) + ([node] if node is VisualInstance3D else []):
		var piece := (to_local * inst.global_transform) * inst.get_aabb()
		box = piece if first else box.merge(piece)
		first = false
	return box


func _label(size: int, align: HorizontalAlignment) -> Label:
	var label := Label.new()
	label.horizontal_alignment = align
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", INK)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	label.add_theme_constant_override("outline_size", 4)
	return label


func _style(border: Color, width: int, bg: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(width)
	style.set_corner_radius_all(6)
	style.set_content_margin_all(4)
	return style
