from metagpt.actions import Action
from metagpt.environment.werewolf.const import STEP_INSTRUCTIONS


class InstructSpeak(Action):
    name: str = "InstructSpeak"

    async def run(self, step_idx, living_players, werewolf_players, player_hunted, player_current_dead):
        instruction_info = STEP_INSTRUCTIONS.get(
            step_idx, {"content": "Unknown instruction.", "send_to": {}, "restricted_to": {}}
        )
        content = instruction_info["content"]
        if "{living_players}" in content and "{werewolf_players}" in content:
            content = content.format(
                living_players=living_players, werewolf_players=werewolf_players, werewolf_num=len(werewolf_players)
            )
        if "{living_players}" in content:
            content = content.format(living_players=living_players)
        if "{werewolf_players}" in content:
            content = content.format(werewolf_players=werewolf_players)
        if "{player_hunted}" in content:
            content = content.format(player_hunted=player_hunted)
        if "{player_current_dead}" in content:
            player_current_dead = "No one" if not player_current_dead else player_current_dead
            content = content.format(player_current_dead=player_current_dead)

        return content, instruction_info["send_to"], instruction_info["restricted_to"]


class ParseSpeak(Action):
    name: str = "ParseSpeak"

    async def run(self):
        pass


class AnnounceGameResult(Action):
    async def run(self, winner: str, win_reason: str):
        return f"Game over! {win_reason}. The winner is the {winner}"
