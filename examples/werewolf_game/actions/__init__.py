from examples.werewolf_game.actions.moderator_actions import InstructSpeak
from examples.werewolf_game.actions.common_actions import Speak
from examples.werewolf_game.actions.werewolf_actions import Hunt
from examples.werewolf_game.actions.witch_actions import Save, Poison

ACTIONS = {
    "Speak": Speak,
    "Hunt": Hunt,
    "Save": Save,
    "Poison": Poison
}