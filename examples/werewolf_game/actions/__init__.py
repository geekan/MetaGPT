from examples.werewolf_game.actions.moderator_actions import InstructSpeak
from examples.werewolf_game.actions.common_actions import Speak, NighttimeWhispers, Reflect
from examples.werewolf_game.actions.werewolf_actions import Hunt, Impersonate
from examples.werewolf_game.actions.guard_actions import Protect
from examples.werewolf_game.actions.seer_actions import Verify
from examples.werewolf_game.actions.witch_actions import Save, Poison

ACTIONS = {
    "Speak": Speak,
    "Hunt": Hunt,
    "Protect": Protect,
    "Verify": Verify,
    "Save": Save,
    "Poison": Poison,
    "Impersonate": Impersonate,
}
