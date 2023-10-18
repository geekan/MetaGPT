import re

from metagpt.const import WORKSPACE_ROOT


class MemoryRetriever:
    def __init__(self, mode="full"):
        self.mode = mode  # full or heuristic

    # FIXME 是否可以让Moderator也使用MemoryRetriever，使用full_str和full_list的mode进行区分？
    @staticmethod
    def get_full_memories(memory) -> str:
        time_stamp_pattern = r'[0-9]+ \| '
        # NOTE: 除Moderator外，其他角色使用memory，只能用m.sent_from（玩家名）不能用m.role（玩家角色），因为他们不知道说话者的身份
        memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in memory]
        return "\n".join(memories)

    def get_heuristic_memories(self, memory, profile, name, m=15, n=7) -> str:

        recent_m_memories = memory[-m:]  # 取最近m条记忆

        before_k_memories = memory[:-m]  # 取最近m条之前的记忆

        # 对最近k条之前的记忆按照重要性打分
        # scored_memories = [(message, self.score_message(message.content, profile, name)) for message in
        #                    before_k_memories]
        scored_memories = [(message, self.score_message(message.content, profile, name)) for message in memory]

        # 提取分数最高的n条记忆
        sorted_memories = sorted(scored_memories, key=lambda x: x[1], reverse=True)
        # sorted_memories = sorted(scored_memories, key=lambda x: (x[1], scored_memories.index(x)), reverse=True)

        # 如果informative记忆与recent记忆不重合，则保留。如果重合，若该消息优先级大于3，则保留，否则不保留
        # top_n_informative_memories = [memory[0] for memory in sorted_memories[:n] if
        #                               memory[0] not in recent_m_memories or memory[1] > 3]

        top_n_informative_memories = [memory[0] for memory in sorted_memories[:n]]

        time_stamp_pattern = r'[0-9]+ \| '

        recent_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                           recent_m_memories]
        informative_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                                top_n_informative_memories]

        memories = ("Two kinds of messages: Recent messages(last k memories) and "
                    "Informative messages(before the last k memories)\n"
                    "Recent Messages:\n" + "\n".join(recent_memories) +
                    "\n\nInformative Messages:\n" + "\n".join(informative_memories))

        # # 记录memories
        # all_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in memory]
        # all_memories = "\n".join(all_memories)
        # if memory:
        #     filename = f"{profile}_memories.txt"
        #     with open(WORKSPACE_ROOT / filename, "a") as f:
        #         f.write(all_memories + "\n\nScore:\n" + str(sorted_memories) + "\n\n")

        return memories

    @staticmethod
    def score_message(message: str, profile, name) -> int:
        message = message.lower()
        # profile = profile.lower()
        # name = name.lower()

        # # Score 5: Information related to the player's character
        # pattern_5 = rf"({name}|{profile})"
        # if re.search(pattern_5, message):
        #     return 5

        # Score 4: Keywords related to elimination or death
        pattern_4 = r"(die|banish|vote\s*out|eliminate|kill|hunt)"
        if re.search(pattern_4, message):
            return 4

        # Score 3: Keywords related to specific actions
        pattern_3 = r"(protect|save|verif|drug|antidote|poison|rescue|shield|cure)"
        if re.search(pattern_3, message):
            return 3

        # Score 2: Keywords related to speculation or revelation of roles
        role_patterns = "werewolf|guard|seer|witch|villager"
        # pattern_2 = r"(discov|speculat|guess|conjectur|doubt|reveal|am|is|was|were|assum|believ|think|suspect)"
        # if re.search(fr"{pattern_2}.*({role_patterns}|{name}|{profile})", message):
        # if re.search(fr"({role_patterns}|{name})", message):
        if re.search(fr"({role_patterns}|player)", message):
            return 2

        # Score 1: Other messages
        else:
            return 1

    def score(self, memory_path, profile, name, limit):
        # 从文件中读取记忆，每一行作为列表的一个元素
        # 使用##控制选取的记忆条数

        if isinstance(memory_path, list):
            for i in range(len(memory_path)):
                self.process_file(limit, memory_path[i], profile, name)
        else:
            self.process_file(limit, memory_path, name, profile)

    def process_file(self, limit, memory_path, name, profile):
        memory_path = str(memory_path)
        with open(memory_path, "r") as f:
            rst = f.read().split("##")
            memories = rst[0].split("\n")
            memories = [re.sub(r'\([^)]*\)', '', item) for item in memories]
            memories_2 = rst[1].split("\n") if len(rst) > 1 else []
            memories_2 = [re.sub(r'\([^)]*\)', '', item) for item in memories_2]
        scored_memories = [(memory, self.score_message(memory, profile, name)) for memory in memories]
        # 选择最高分的10条信息
        sorted_memories = sorted(scored_memories, key=lambda x: (x[1], memories.index(x[0])), reverse=True)[
                          :limit]
        sorted_memories = sorted(sorted_memories, key=lambda x: memories.index(x[0]))
        sorted_memories = [f"{memory[0]} : {memory[1]}" for memory in sorted_memories]
        print("\n".join(sorted_memories))
        new_file_path = str(memory_path).replace(".txt", "_score.txt")
        with open(new_file_path, "a") as f:
            f.write("sorted_memories:\n" + "\n".join(sorted_memories) + "\n---\n")
        if memories_2:
            scored_memories = [(memory, self.score_message(memory, profile, name)) for memory in memories_2]
            # 选择最高分的10条信息
            sorted_memories = sorted(scored_memories, key=lambda x: (x[1], memories_2.index(x[0])), reverse=True)[
                              :limit]
            sorted_memories = sorted(sorted_memories, key=lambda x: memories_2.index(x[0]))
            sorted_memories = [f"{memory[0]} : {memory[1]}" for memory in sorted_memories]

            print("\n".join(sorted_memories))
            new_file_path = str(memory_path).replace(".txt", "_score.txt")
            with open(new_file_path, "a") as f:
                f.write("sorted_memories:\n" + "\n".join(sorted_memories) + "\n---\n")


if __name__ == '__main__':
    folder = WORKSPACE_ROOT / "10141230"
    path = folder / "10141230 - werewolf.txt"
    paths = [folder / "10141230 - guard.txt", folder / "10141230 - werewolf.txt",
             folder / "10141230 - witch.txt",
             folder / "10141230 - seer.txt", folder / "10141230 - villager.txt"]
    profiles = []
    names = []
    # profile = "werewolf"
    # name = "werewolf"
    MemoryRetriever().score(paths, profiles, names, limit=10)
