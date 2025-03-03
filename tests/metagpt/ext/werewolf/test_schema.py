from metagpt.ext.werewolf.schema import WwJsonEncoder
from metagpt.ext.werewolf.actions.common_actions import Speak
from metagpt.environment.werewolf.const import RoleType, RoleState, RoleActionRes
import json
from metagpt.utils.common import to_jsonable_python
def test_ww_json_encoder():
    encoder = WwJsonEncoder
    data = {
        "test": RoleType.VILLAGER,
        "test2": RoleState.ALIVE,
        "test3": RoleActionRes.PASS,
        "test4": [Speak],
    }
    encoded = json.dumps(data, cls=encoder, default=to_jsonable_python)
    # print(encoded)