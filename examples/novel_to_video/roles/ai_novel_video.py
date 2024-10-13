# -*- coding: utf-8 -*-
# @Date    :2024/2/26 10:28
# @Author  : 宏伟（散人）
# @Desc    :
import os
from datetime import datetime

from MetaGPT.examples.novel_to_video.actions.get_novel import GetNovel
from MetaGPT.examples.novel_to_video.actions.make_video import MakeVideo
from MetaGPT.examples.novel_to_video.actions.rewrite import RewriteNovelContent
from MetaGPT.examples.novel_to_video.actions.sd_prompt import MakeSDPrompt
from MetaGPT.examples.novel_to_video.actions.sd_text_to_image import SD_t2i
from MetaGPT.examples.novel_to_video.actions.segment import Segment
from MetaGPT.examples.novel_to_video.actions.tts_edge import EdgeTTS
from MetaGPT.examples.novel_to_video.utils.fileTools import create_AINovelVideoDir
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.provider.human_provider import HumanProvider
from metagpt.roles import Role
from metagpt.schema import Message

WORKSPACE_DIR='../workspace'

class NovelToVideoAssistant(Role):
    alias: str = ""  # 别名
    main_title: str = ""  # 小说的标题
    novel_id: str = ""
    chapters: list = []
    workspace: str = ""  # 工作区地址
    total_chapters: int = 0  # 总章节数
    current_chapter_workspace: str = ""  # 当前章节输出地址
    total_storyboard: list = []  # 各个章节的总段落数
    current_storyboard_number: int = 0  # 正在处理的段落编号
    current_chapter_number: int = 0  # 当前正在处理的章节
    roles: dict = {}

    def __init__(
            self,
            name: str = "ntv_assistant",
            profile: str = "NovelToVideo Assistant",
            goal: str = "Generate novel videos",

    ):
        super().__init__()
        self.set_actions([GetNovel()])
        self.name = name
        self.profile = profile
        self.goal = goal
        self.workspace = WORKSPACE_DIR + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_chapter_workspace = self.workspace + '/chapter_' + str(self.current_chapter_number)
        # 创建工作目录
        create_AINovelVideoDir(self.current_chapter_workspace)

    async def _think(self) -> None:
        """Determine the next action to be taken by the role."""
        logger.info(self.rc.state)
        if self.rc.todo is None:

            self._set_state(0)
            return

        if self.rc.state + 1 < len(self.states):

            self._set_state(self.rc.state + 1)
        else:

            self.rc.todo = None

    async def _react(self) -> Message:
        msg = None
        while True:
            await self._think()
            if self.rc.todo is None:
                break
            msg = await self.act()
        return msg

    async def act(self) -> Message:
        todo = self.rc.todo

        if type(todo) is GetNovel:
            msg = self.rc.memory.get(k=1)[0]
            n_id = msg.content
            resp = await todo.run(novel_id=n_id)
            logger.info(resp)
            self.alias = resp.alias
            self.chapters = resp.chapters
            # 获取章节 并进行改写
            await self._handle_chapters()
            return Message(content=str(resp.to_dict()), role=self.profile)

        # 重写内容
        if type(todo) is RewriteNovelContent:
            resp = await todo.run()
            logger.info(resp)

            # 重写小说后，需要对小说进行分镜
            act = Segment(content=resp)
            self._add_actions([act])
            return Message(content=resp, role=self.profile)

        # 分镜处理
        if type(todo) is Segment:
            resp = await todo.run()
            logger.info(resp)
            print('segment resp:', resp)
            # 更新总分镜个数
            self.total_storyboard.append(len(resp))
            print('length', self.total_storyboard[self.current_chapter_number])
            actions = list()

            # 生成图片和语音
            for i, v in enumerate(resp):
                print('segment_', i, ':====', v)
                # 1、生成sd 文生图提示词
                actions.append(MakeSDPrompt(content=v))

                # 2、生成TTS语音片段
                tts_path = self.current_chapter_workspace + "/tts/" + datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S") + '_' + str(
                    i) + ".mp3"
                actions.append(EdgeTTS(content=v, output=tts_path))
            self._add_actions(actions)
            # 动态更新工作目录 调整当前工作目录，并创建目录文件夹
            self._dynamically_updating_the_directory()
            return Message(content=str(resp), role=self.profile)

        # SD提示词处理
        if type(todo) is MakeSDPrompt:
            resp = await todo.run()
            logger.info(resp)
            images_path = self.current_chapter_workspace + "/image"
            act = SD_t2i(prompts=resp, save_path=images_path)
            self._add_actions([act])
            return Message(content=resp, role=self.profile)

        if type(todo) is EdgeTTS:
            resp = await todo.run()
            # 动态更新分镜标志位
            self._dynamically_updating_the_storyboard()
            logger.info(resp)
            return Message(content=resp, role=self.profile)

        if type(todo) is SD_t2i:
            resp = await todo.run()
            # 判断当前章节是否合成完毕，如果合成完毕，则进行视频合成
            self.current_storyboard_number += 1
            logger.info(resp)
            if self.current_storyboard_number == self.total_storyboard[self.current_chapter_number]:
                self.current_storyboard_number = 0
                act = MakeVideo(workspace=self.current_chapter_workspace)
                self.current_chapter_number += 1
                if self.current_chapter_number == self.total_chapters:
                    self.current_chapter_number = 0
                self.current_chapter_workspace = self.workspace + "/chapter_" + str(self.current_chapter_number)
                self._add_actions([act])

            return Message(content=resp, role=self.profile)
        resp = await todo.run()
        logger.info(resp)
        return Message(content=resp, role=self.profile)

    async def _handle_chapters(self) -> Message:

        actions = list()
        for k in range(len(self.chapters)):
            print('chapter:', self.chapters[k].content)
            actions.append(RewriteNovelContent(content=self.chapters[k].content))

        self.set_actions(actions)
        self.rc.todo = None
        chapters_length = len(actions)
        self.total_chapters = chapters_length
        print('chapters_length:', chapters_length)
        return Message(content=f'已获取到{chapters_length}段内容需要改写', role=self.profile)

    def _add_actions(self, actions):
        start_idx = len(self.actions)
        for idx, action in enumerate(actions):
            if not isinstance(action, Action):
                # 默认初始化
                i = action(name="", llm=self.llm)
            else:
                if self.is_human and not isinstance(action.llm, HumanProvider):
                    logger.warning(
                        f"is_human attribute does not take effect, "
                        f"as Role's {str(action)} was initialized using LLM, "
                        f"try passing in Action classes instead of initialized instances"
                    )
                i = action
            self._init_action(i)
            self.actions.append(i)
            self.states.append(f"{idx + start_idx}. {action}")

    # 动态更新章节分镜
    def _dynamically_updating_the_storyboard(self):
        self.current_storyboard_number += 1
        # 如果当前合成的段落是最后一段
        if self.current_storyboard_number == self.total_storyboard[self.current_chapter_number]:
            # 全部章节合成完毕
            self.current_storyboard_number = 0
            self.current_chapter_number += 1  # 当前完成的章节+1
            if self.current_chapter_number == self.total_chapters:
                self.current_chapter_number = 0
            # 更新当前章节工作目录
            self.current_chapter_workspace = self.workspace + "/chapter_" + str(self.current_chapter_number)

    # 动态更新章节目录
    def _dynamically_updating_the_directory(self):
        self.current_chapter_number += 1  # 当前完成章节+1
        # 全部章节合成完毕
        if self.current_chapter_number == self.total_chapters:
            self.current_chapter_number = 0
        # 更新当前章节工作目录
        self.current_chapter_workspace = self.workspace + "/chapter_" + str(self.current_chapter_number)
        # 创建章节工作目录
        if self.current_chapter_number != 0:
            if not os.path.exists(self.current_chapter_workspace):
                create_AINovelVideoDir(self.current_chapter_workspace)


async def start_ai_novel_video(book_id: str = ''):
    print('start NovelToVideoAssistant:', book_id)
    msg = book_id
    role = NovelToVideoAssistant()
    logger.info(msg)
    result = await role.run(msg)
    logger.info(result)
