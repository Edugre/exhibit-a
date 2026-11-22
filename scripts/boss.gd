extends Guard
## The librarian (docs/boss_and_staff.md). There's only one of her, and she belongs to the museum rather
## than to a room. After every build she walks a route through all the rooms, out from the vault to the
## entrance and back, pausing at each turn, and every staff bell sends her hurrying to where the player
## was seen. Her own chase and catch are the ordinary guard's, so her catch ends the heist.
## The host decides; she syncs like any guard. Every peer shows "She's coming…" when a bell rings.

## How far inside each doorway her route turns, so she crosses the whole room.
const ROUTE_INSET := 1.5
## How long after the last room's navmesh is ready before she sets off: the map needs a moment to join
## the rooms up (in tests, paths across rooms fail for about a second after a bake).
const SETTLE := 1.2
## If a room never reports its navmesh, she sets off anyway after this long.
const GIVE_UP := 6.0
const WARNING_TIME := 2.6
const WARNING_FADE := 0.8

var _rooms_key := ""
var _routing := false
var _waited := 0.0
var _settled := 0.0
var _warning: Label
var _warning_age := -1.0


func _ready() -> void:
	super()
	add_to_group("boss")
	_nav_ready = false
	var layer := CanvasLayer.new()
	layer.layer = 35
	add_child(layer)
	_warning = Label.new()
	_warning.text = "She's coming…"
	_warning.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_warning.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_warning.position.y = 90.0
	_warning.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var serif := SystemFont.new()
	serif.font_names = PackedStringArray(["Palatino Linotype", "Georgia", "serif"])
	_warning.add_theme_font_override("font", serif)
	_warning.add_theme_font_size_override("font_size", 44)
	_warning.add_theme_color_override("font_color", Color(0.94, 0.8, 0.52))
	_warning.add_theme_color_override("font_outline_color", Color(0.12, 0.02, 0.02))
	_warning.add_theme_constant_override("outline_size", 8)
	_warning.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_warning.visible = false
	layer.add_child(_warning)


func _physics_process(delta: float) -> void:
	if multiplayer.is_server():
		_follow_the_rooms(delta)
	super(delta)


func _process(delta: float) -> void:
	super(delta)
	if _warning_age < 0.0:
		return
	_warning_age += delta
	_warning.modulate.a = clampf((WARNING_TIME - _warning_age) / WARNING_FADE, 0.0, 1.0)
	if _warning_age > WARNING_TIME:
		_warning.visible = false
		_warning_age = -1.0


## Every peer: a staff bell has rung somewhere.
func warn() -> void:
	_warning.visible = true
	_warning.modulate.a = 1.0
	_warning_age = 0.0


## Host: a staff bell. She hurries to where the player was seen, at her investigate speed (faster than
## her patrol, slower than her chase), unless she's already chasing someone.
func hear_bell(at: Vector3) -> void:
	hear_noise(at)


func _on_heist_reset(respawn_players: bool) -> void:
	super(respawn_players)
	_nav_ready = false
	_rooms_key = ""      # the museum is being rebuilt: route again once the new rooms are ready


## Host: notices each new build, waits until all its rooms have their navmesh, then sets off.
func _follow_the_rooms(delta: float) -> void:
	var museum := get_tree().get_first_node_in_group("museum") as MuseumLayout
	if museum == null:
		return
	var rooms := museum.get_rooms()
	var key := ",".join(rooms.map(func(r: Room) -> String: return str(r.name)))
	if key != _rooms_key:
		_rooms_key = key
		_nav_ready = false
		_routing = not rooms.is_empty()
		_waited = 0.0
		_settled = 0.0
		return
	if not _routing:
		return
	_waited += delta
	# A room has its navmesh once its bake has filled its region's mesh (it starts empty). Looked at
	# directly rather than waiting for each room's `baked` signal, so nothing depends on catching it.
	var all_baked := rooms.all(func(r: Room) -> bool: return r.nav_region.navigation_mesh.get_polygon_count() > 0)
	_settled = _settled + delta if all_baked else 0.0
	if _settled >= SETTLE or _waited >= GIVE_UP:
		_routing = false
		_set_out(rooms)


## Her route: in and out of every room front to back, round the vault's own patrol points, and back
## the same way. She starts in the vault, where every restart puts her again.
func _set_out(rooms: Array[Room]) -> void:
	var points: Array[Vector3] = []
	var home := -1
	for room in rooms:
		points.append(room.global_transform * Vector3(0.0, 0.0, -ROUTE_INSET))
		if room.exit:
			points.append(room.global_transform * (room.exit.position + Vector3(0.0, 0.0, ROUTE_INSET)))
			continue
		home = points.size() - 1
		var marks := room.get_node_or_null(^"GuardWaypoints")
		if marks:
			home = points.size()
			for mark in marks.get_children():
				points.append((mark as Node3D).global_position)
	if points.size() < 2:
		return
	var back := points.slice(1, points.size() - 1)
	back.reverse()
	_waypoints.assign(points + back)
	if home < 0:
		home = points.size() - 1
	global_position = _waypoints[home]
	velocity = Vector3.ZERO
	_start_transform = global_transform
	_waypoint_index = (home + 1) % _waypoints.size()
	_wait_timer = 0.0
	state = State.PATROL
	_nav_ready = true
	agent.target_position = _waypoints[_waypoint_index]
