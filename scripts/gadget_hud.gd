class_name GadgetHud
extends CanvasLayer
## The jammer's charge count and a short message after each use. Only the owner sees it.

const FLASH_SECONDS := 1.5

@onready var charges_label: Label = $Charges
@onready var message_label: Label = $Message

var _flash_left := 0.0


func _process(delta: float) -> void:
	if _flash_left <= 0.0:
		return
	_flash_left -= delta
	if _flash_left <= 0.0:
		message_label.visible = false


func show_charges(charges: int, max_charges: int) -> void:
	charges_label.text = "Jammer [Q]: %d / %d" % [charges, max_charges]


func flash(text: String) -> void:
	message_label.text = text
	message_label.visible = true
	_flash_left = FLASH_SECONDS
