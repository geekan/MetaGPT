from examples.werewolf_game.actions.moderator_actions import InstructSpeak
from examples.werewolf_game.actions.common_actions import Speak
from examples.werewolf_game.actions.werewolf_actions import Hunt
from examples.werewolf_game.actions.guard_actions import Protect

ACTIONS = {
    "Speak": Speak,
    "Hunt": Hunt,
    "Protect": Protect,
}