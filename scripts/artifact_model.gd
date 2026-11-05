extends Node3D
## The visible artifact: the Last Book of Alexandria, still burning 2,000 years on.
## Cosmetic only. The host owns who has the artifact; this script just keeps the embers alive
## and lets the chain swing. Every peer does its own, so the book needs no network traffic.

## How far the embers dip and flare around their baked brightness.
const FLICKER_DEPTH := 0.28
const SLOW_FLICKER := 5.3
const FAST_FLICKER := 12.7

## The way the chain was modelled, in book space: straight down when the book is on its stand.
const CHAIN_REST := Vector3(-0.015, -0.819, 0.574)
## Which way it lies when the book is flat on the floor: out from the spine.
const CHAIN_ON_FLOOR := Vector3(-1.0, -0.06, 0.25)
const CHAIN_STIFFNESS := 46.0
const CHAIN_DAMPING := 5.0
const CHAIN_DRAG := 0.13
const VELOCITY_SMOOTHING := 10.0
## Nothing carried moves this far in one frame, so a jump this big is a respawn, not a step.
const TELEPORT_DISTANCE := 1.0

## True while this peer is the one carrying it: smoke right in front of the camera would blind you.
var held_in_view: bool = false:
	set(value):
		if value == held_in_view:
			return  # the world script sets this every frame
		held_in_view = value
		if is_node_ready():
			smoke.emitting = not value

## True while it's lying on the floor, where the chain can't hang straight down.
var lying_flat: bool = false

var _ember_material: BaseMaterial3D
var _ember_energy: float = 1.0
var _glow_energy: float = 1.0
var _time: float = 0.0
var _chain: Node3D
var _hang: Vector3 = Vector3.DOWN
var _hang_speed: Vector3 = Vector3.ZERO
var _last_position: Vector3
var _velocity: Vector3 = Vector3.ZERO

@onready var glow: OmniLight3D = $Glow
@onready var smoke: GPUParticles3D = $Smoke


func _ready() -> void:
	var book := find_child("LastBook", true, false) as MeshInstance3D
	_ember_material = book.get_active_material(0).duplicate() as BaseMaterial3D
	book.set_surface_override_material(0, _ember_material)
	_ember_energy = _ember_material.emission_energy_multiplier
	_glow_energy = glow.light_energy
	_time = randf() * 100.0  # so two peers don't breathe in step
	_chain = find_child("LastBookChain", true, false) as Node3D
	_last_position = global_position


func _process(delta: float) -> void:
	_time += delta
	var flicker := sin(_time * SLOW_FLICKER) * 0.6 + sin(_time * FAST_FLICKER + 1.1) * 0.4
	var heat := 1.0 + flicker * FLICKER_DEPTH
	_ember_material.emission_energy_multiplier = _ember_energy * heat
	glow.light_energy = _glow_energy * heat
	_swing_chain(delta)


## A loose pendulum: the chain leans against the way the book is moving, then swings back.
func _swing_chain(delta: float) -> void:
	var moved := global_position - _last_position
	_last_position = global_position
	if moved.length() >= TELEPORT_DISTANCE:
		moved = Vector3.ZERO
	_velocity = _velocity.lerp(moved / delta, 1.0 - exp(-VELOCITY_SMOOTHING * delta))

	var book_basis := _chain.get_parent_node_3d().global_basis.orthonormalized()
	var pull := Vector3.DOWN - _velocity * CHAIN_DRAG
	if lying_flat:
		pull = book_basis * CHAIN_ON_FLOOR
	_hang_speed += (pull.normalized() - _hang) * CHAIN_STIFFNESS * delta
	_hang_speed *= exp(-CHAIN_DAMPING * delta)
	_hang = (_hang + _hang_speed * delta).normalized()
	_chain.quaternion = Quaternion(CHAIN_REST.normalized(), (book_basis.inverse() * _hang).normalized())
