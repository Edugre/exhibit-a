extends Node
## Main scene: Host/Join menu + spawning players.
## Only the host spawns or removes players; the PlayerSpawner
## (MultiplayerSpawner) replicates them to the client automatically.

const PLAYER_SCENE := preload("res://scenes/player.tscn")

@onready var menu: Control = %Menu
@onready var address_input: LineEdit = %AddressInput
@onready var host_button: Button = %HostButton
@onready var join_button: Button = %JoinButton
@onready var status_label: Label = %StatusLabel
@onready var players_root: Node3D = $World/Players
@onready var spawn_points: Array[Node] = $World/Museum/SpawnPoints.get_children()


func _ready() -> void:
	host_button.pressed.connect(_on_host_pressed)
	join_button.pressed.connect(_on_join_pressed)
	NetworkManager.connected_to_host.connect(_on_connected_to_host)
	NetworkManager.connection_failed.connect(_on_connection_failed)
	NetworkManager.host_disconnected.connect(_on_host_disconnected)


# --- Menu buttons ---------------------------------------------------------

func _on_host_pressed() -> void:
	var err: Error = NetworkManager.host_game()
	if err != OK:
		status_label.text = "Couldn't host (error %d). Is something else using port %d?" % [err, NetworkManager.DEFAULT_PORT]
		return
	multiplayer.peer_connected.connect(_spawn_player)
	multiplayer.peer_disconnected.connect(_remove_player)
	GameState.heist_reset.connect(_on_heist_reset)
	_spawn_player(multiplayer.get_unique_id())  # the host is always peer 1
	menu.hide()


func _on_join_pressed() -> void:
	var address := address_input.text.strip_edges()
	if address.is_empty():
		address = "127.0.0.1"
	var err: Error = NetworkManager.join_game(address)
	if err != OK:
		status_label.text = "Couldn't start connection (error %d)." % err
		return
	status_label.text = "Connecting to %s..." % address
	_set_buttons_enabled(false)


# --- Connection events (client side) --------------------------------------

func _on_connected_to_host() -> void:
	menu.hide()


func _on_connection_failed() -> void:
	status_label.text = "Couldn't connect. Check the IP and that the host is running."
	_set_buttons_enabled(true)


func _on_host_disconnected() -> void:
	# The host left: go back to a clean menu.
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	get_tree().reload_current_scene()


# --- Spawning (host only) -------------------------------------------------

func _spawn_player(peer_id: int) -> void:
	var player := PLAYER_SCENE.instantiate()
	player.name = str(peer_id)  # the name tells every peer who controls this player
	var index := players_root.get_child_count()
	player.position = spawn_points[index % spawn_points.size()].global_position
	players_root.add_child(player, true)
	if players_root.get_child_count() == 2:
		GameState.start_heist()  # both players are in: the heist begins


func _remove_player(peer_id: int) -> void:
	var player := players_root.get_node_or_null(str(peer_id))
	if player:
		player.queue_free()
	GameState.stop_heist()  # partner left: back to waiting


func _on_heist_reset(respawn_players: bool) -> void:
	if not respawn_players:
		return
	var index := 0
	for player in players_root.get_children():
		var spot: Vector3 = spawn_points[index % spawn_points.size()].global_position
		player.teleport.rpc_id(player.name.to_int(), spot)  # the owner moves its own player
		index += 1


func _set_buttons_enabled(enabled: bool) -> void:
	host_button.disabled = not enabled
	join_button.disabled = not enabled
