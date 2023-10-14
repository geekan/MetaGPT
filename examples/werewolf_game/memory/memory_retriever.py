import re


class MemoryRetriever:
    def __init__(self, mode="full"):
        self.mode = mode    # full or heuristic

    def get_full_memories(self, memory, profile, name) -> str:
        all_memories = memory.get()
        if profile == "Moderator":
            memories = [f"{m.sent_from}({m.role}): {m.content}" for m in all_memories]
            return "\n".join(memories)
        else:
            time_stamp_pattern = r'[0-9]+ \| '
            # NOTE: 除Moderator外，其他角色使用memory，只能用m.sent_from（玩家名）不能用m.role（玩家角色），因为他们不知道说话者的身份
            memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in all_memories]
            return "\n".join(memories)

    def get_heuristic_memories(self, memory, profile, name, m=15, n=10) -> str:
        all_memories = memory.get()

        recent_m_memories = all_memories[-m:]  # 取最近m条记忆

        # 将所有记忆按照重要性打分
        scored_memories = [(message, self.score_message(message.content, profile, name)) for message in all_memories]

        # 提取分数最高的n条记忆，如果分数相同，则较新轮次的记忆排在前面
        # sorted_memories = sorted(scored_memories, key=lambda x: x[1], reverse=True)
        sorted_memories = sorted(scored_memories, key=lambda x: (x[1], scored_memories.index(x)),
                                 reverse=True)

        # 如果informative记忆与recent记忆不重合，则保留。如果重合，若该消息优先级大于3，则保留，否则不保留
        top_n_informative_memories = [memory[0] for memory in sorted_memories[:n]  \
                                      if memory[0] not in recent_m_memories or memory[1] > 3]

        time_stamp_pattern = r'[0-9]+ \| '

        recent_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                           recent_m_memories]
        informative_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                                top_n_informative_memories]

        memories = ("Two kinds of messages: Recent messages(The priority is from low to high) and "
                    "Informative messages(The priority is from high to low)\n"
                    "Recent Messages:\n" + "\n".join(recent_memories) +
                    "\n\nInformative Messages():\n" + "\n".join(informative_memories))

        return memories

    def score_message(self, message: str, profile, name) -> int:
        message = message.lower()
        profile = profile.lower()
        name = name.lower()

        # Score 5: Information related to the player's character
        pattern_5 = rf"({name}|{profile})"
        if re.search(pattern_5, message):
            return 5

        # Score 4: Keywords related to elimination or death
        pattern_4 = r"(die|banish|vote\s*out|eliminate|kill|hunt)"
        if re.search(pattern_4, message):
            return 4

        # Score 3: Keywords related to speculation or revelation of roles
        role_patterns = "werewolf|villager|guard|seer|witch"
        pattern_3 = r"(discov|speculat|guess|conjectur|doubt|reveal|am|is|was|were|assum|believ|think|suspect)"
        if re.search(fr"{pattern_3}.*({role_patterns})", message):
            return 3

        # Score 2: Keywords related to specific actions
        pattern_2 = r"(protect|save|verif|drug|antidote|poison|rescue|shield|cure)"
        if re.search(pattern_2, message):
            return 2

        # Score 1: Other messages
        else:
            return 1
