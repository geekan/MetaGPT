#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is designed to classify intentions from complete conversation content.

Usage:
    This script can be used to classify intentions from a conversation. It utilizes models for detecting intentions
    from the text provided and categorizes them accordingly. If the intention of certain words or phrases is unclear,
    it prompts the user for clarification.

Dependencies:
    This script depends on the metagpt library, pydantic, and other utilities for message parsing and interaction.

"""
import json
from typing import List

from pydantic import BaseModel, Field

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import parse_json_code_block


class SOPItem(BaseModel):
    """
    Represents an item in a Standard Operating Procedure (SOP).

    Attributes:
        description (str): The description or title of the SOP.
        sop (List[str]): The steps or details of the SOP.
    """

    description: str
    sop: List[str]


SOP_CONFIG = [
    SOPItem(
        description="Intentions related to or including software development, such as developing or building software, games, programming, app, websites, etc.",
        sop=[
            "Writes a PRD based on software requirements.",
            "Writes a design to the project repository, based on the PRD of the project.",
            "Writes a project plan to the project repository, based on the design of the project.",
            "Writes codes to the project repository, based on the project plan of the project.",
            # "Run QA test on the project repository.",
            "Stage and commit changes for the project repository using Git.",
        ],
    )
]


class IntentDetectClarification(BaseModel):
    """
    Represents clarifications for unclear intentions.

    Attributes:
        ref (str): The reference to the original words.
        clarification (str): A question for the user to clarify the intention of the unclear words.
    """

    ref: str
    clarification: str


class IntentDetectIntentionRef(BaseModel):
    """
    Represents intentions along with their references.

    Attributes:
        intent (str): The intention from the "Intentions" section.
        refs (List[str]): List of original text references from the "Dialog" section that match the intention.
    """

    intent: str
    refs: List[str]


class IntentDetectIntentionSOP(BaseModel):
    """
    Represents an intention mapped to a Standard Operating Procedure (SOP).

    Attributes:
        intention (IntentDetectIntentionRef): Reference to the intention.
        sop (SOPItem, optional): Standard Operating Procedure (SOP) item related to the intention.
    """

    intention: IntentDetectIntentionRef
    sop: SOPItem = None


class IntentDetectResult(BaseModel):
    """
    Represents the result of intention detection.

    Attributes:
        clarifications (List[IntentDetectClarification]): List of clarifications for unclear intentions.
        intentions (List[IntentDetectIntentionSOP]): List of intentions mapped to Standard Operating Procedures (SOPs).
    """

    clarifications: List[IntentDetectClarification] = Field(default_factory=list)
    intentions: List[IntentDetectIntentionSOP] = Field(default_factory=list)


class IntentDetect(Action):
    """
    Action class for intention detection.

    Attributes:
        _dialog_intentions (IntentDetectDialogIntentions): Instance of IntentDetectDialogIntentions.
            Dialog intentions for matching user intentions.
        _references (IntentDetectReferences): Instance of IntentDetectReferences.
            References to intentions and unreferenced content.
        _intent_to_sops (List[IntentSOP]): List of IntentSOP objects.
            Mapping of intentions to Standard Operating Procedures (SOPs).
        result (IntentDetectResult): Instance of IntentDetectResult.
            Result object containing the outcome of intention detection.
    """

    class IntentDetectDialogIntentions(BaseModel):
        class IntentDetectIntention(BaseModel):
            ref: str
            intent: str

        intentions: List[IntentDetectIntention]
        clarifications: List[IntentDetectClarification]

    class IntentDetectReferences(BaseModel):
        class IntentDetectUnrefs(BaseModel):
            ref: str
            reason: str

        intentions: List[IntentDetectIntentionRef]
        unrefs: List[IntentDetectUnrefs]

    class IntentSOP(BaseModel):
        intent: str
        sop: str
        sop_index: int
        reason: str

    _dialog_intentions: IntentDetectDialogIntentions = None
    _references: IntentDetectReferences = None
    _intent_to_sops: List[IntentSOP] = None
    result: IntentDetectResult = None

    async def run(self, with_messages: List[Message] = None, **kwargs) -> Message:
        """
        Runs the intention detection action.

        Args:
            with_messages (List[Message]): List of messages representing the conversation content.
            **kwargs: Additional keyword arguments.
        """
        msg_markdown = self._message_to_markdown(with_messages)
        intentions = await self._get_intentions(msg_markdown)
        await self._get_references(msg_markdown, intentions)
        await self._get_sops()
        await self._merge()

        return Message(
            content=self.result.model_dump_json(), role="assistant", cause_by=self, instruct_content=self.result
        )

    async def _get_intentions(self, msg_markdown: str) -> List[str]:
        rsp = await self.llm.aask(
            msg_markdown,
            system_msgs=[
                "You are a tool that can classify user intentions.",
                "Detect and classify the intention of each word spoken by the user in the conversation.",
                "If the user's intention is not clear, create a request for the user to clarify the intention of"
                " the unclear words.",
                "Return a markdown object with:\n"
                '- an "intentions" key containing a list of JSON objects, where each object contains:\n'
                '  - a "ref" key containing the original words reference;\n'
                '  - an "intent" key explaining the intention of the referenced word;\n'
                '- a "clarifications" key containing a list of JSON objects, where each object contains:\n'
                '  - a "ref" key containing the original words reference;\n'
                '  - a "clarification" key containing a question, in the tone of an assistant, prompts the user to provide more details about the intention regarding the unclear word(s) referenced in the user\'s description.',
            ],
            stream=False,
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)
        if not json_blocks:
            return []
        self._dialog_intentions = self.IntentDetectDialogIntentions.model_validate_json(json_blocks[0])
        return [i.intent for i in self._dialog_intentions.intentions]

    async def _get_references(self, msg_markdown: str, intentions: List[str]):
        intention_list = "\n".join([f"- {i}" for i in intentions])
        prompt = f"## Dialog\n{msg_markdown}\n---\n## Intentions\n{intention_list}\n"
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool that categorizes text content by intent.",
                "Place the original text from the `Dialog` section under the matching intent of `Intentions` section.",
                "Allow different intents to reference the same original text.",
                "Return a markdown JSON object with:\n"
                '- an "intentions" key containing a list of JSON objects, where each object contains:\n'
                '  - a "intent" key containing the intention from "Intentions" section;\n'
                '  - a "refs" key containing a list of strings of original text from the "Dialog" section that match'
                " the intention.\n"
                '- a "unrefs" key containing a list of JSON objects, where each object contains:\n'
                '  - a "ref" key containing the unreferenced original text.\n'
                '  - a "reason" key explaining why it is unreferenced.\n',
            ],
            stream=False,
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)
        if not json_blocks:
            return []
        self._references = self.IntentDetectReferences.model_validate_json(json_blocks[0])

    async def _get_sops(self):
        intention_list = ""
        for i, v in enumerate(self._references.intentions):
            intention_list += f"{i + 1}. intent: {v.intent}\n"
            for j in v.refs:
                intention_list += f"   - ref: {j}\n"
        sop_list = ""
        for i, v in enumerate(SOP_CONFIG):
            sop_list += f"{i + 1}. {v.description}\n"
        prompt = f"## Intentions\n{intention_list}\n---\n## SOPs\n{sop_list}\n"
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool that matches user intentions with Standard Operating Procedures (SOPs).",
                'You search for matching SOPs under "SOPs" based on user intentions in "Intentions" and their related original descriptions.',
                'Inspect each intention in "Intentions".',
                "Return a markdown JSON list of objects, where each object contains:\n"
                '- an "intent" key containing the intention from the "Intentions" section;\n'
                '- a "sop" key containing the SOP description from the "SOPs" section; filled with an empty string if no match.\n'
                '- a "sop_index" key containing the int type index of SOP description from the "SOPs" section; filled with 0 if no match.\n'
                '- a "reason" key explaining why it is matching/mismatching.\n',
            ],
            stream=False,
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)
        vv = json.loads(json_blocks[0])
        self._intent_to_sops = [self.IntentSOP.model_validate(i) for i in vv]

    async def _merge(self):
        self.result = IntentDetectResult(clarifications=self._dialog_intentions.clarifications)
        distinct = {}
        # Consolidate intentions under the same SOP.
        for i in self._intent_to_sops:
            if i.sop_index == 0:  # 1-based index
                refs = self._get_intent_ref(i.intent)
                item = IntentDetectIntentionSOP(intention=IntentDetectIntentionRef(intent=i.intent, refs=refs))
                self.result.intentions.append(item)
                continue
            distinct[i.sop_index] = [i.intent] + distinct.get(i.sop_index, [])

        merge_intents = {}
        intent_to_sops = {i.intent: i.sop_index for i in self._intent_to_sops if i.sop_index != 0}
        for sop_index, intents in distinct.items():
            if len(intents) > 1:
                merge_intents[sop_index] = intents
                continue
            # Merge single intention
            refs = self._get_intent_ref(intents[0])
            item = IntentDetectIntentionSOP(intention=IntentDetectIntentionRef(intent=intents[0], refs=refs))
            sop_index = intent_to_sops.get(intents[0])
            item.sop = SOP_CONFIG[sop_index - 1]  # 1-based index
            self.result.intentions.append(item)

        # Merge repetitive intentions into one
        for sop_index, intents in merge_intents.items():
            intent_ref = IntentDetectIntentionRef(intent="\n".join(intents), refs=[])
            for i in intents:
                refs = self._get_intent_ref(i)
                intent_ref.refs.extend(refs)
            intent_ref.refs = list(set(intent_ref.refs))
            item = IntentDetectIntentionSOP(intention=intent_ref)
            item.sop = SOP_CONFIG[sop_index - 1]  # 1-based index
            self.result.intentions.append(item)

    def _get_intent_ref(self, intent: str) -> List[str]:
        refs = []
        for i in self._references.intentions:
            if i.intent == intent:
                refs.extend(i.refs)
        return refs

    @staticmethod
    def _message_to_markdown(messages) -> str:
        markdown = ""
        for i in messages:
            content = i.content.replace("\n", " ")
            markdown += f"> {i.role}: {content}\n>\n"
        return markdown


class LightIntentDetect(IntentDetect):
    async def run(self, with_messages: List[Message] = None, **kwargs) -> Message:
        """
        Runs the intention detection action.

        Args:
            with_messages (List[Message]): List of messages representing the conversation content.
            **kwargs: Additional keyword arguments.
        """
        msg_markdown = self._message_to_markdown(with_messages)
        await self._get_intentions(msg_markdown)
        await self._get_sops()
        await self._merge()

        return Message(content="", role="assistant", cause_by=self)

    async def _get_sops(self):
        intention_list = ""
        for i, v in enumerate(self._dialog_intentions.intentions):
            intention_list += f"{i + 1}. intent: {v.intent}\n   - ref: {v.ref}\n"
        sop_list = ""
        for i, v in enumerate(SOP_CONFIG):
            sop_list += f"{i + 1}. {v.description}\n"
        prompt = f"## Intentions\n{intention_list}\n---\n## SOPs\n{sop_list}\n"
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool that matches user intentions with Standard Operating Procedures (SOPs).",
                'You search for matching SOPs under "SOPs" based on user intentions in "Intentions" and their related original descriptions.',
                'Inspect each intention in "Intentions".',
                "Return a markdown JSON list of objects, where each object contains:\n"
                '- an "intent" key containing the intention from the "Intentions" section;\n'
                '- a "sop" key containing the SOP description from the "SOPs" section; filled with an empty string if no match.\n'
                '- a "sop_index" key containing the int type index of SOP description from the "SOPs" section; filled with 0 if no match.\n'
                '- a "reason" key explaining why it is matching/mismatching.\n',
            ],
            stream=False,
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)
        vv = json.loads(json_blocks[0])
        self._intent_to_sops = [self.IntentSOP.model_validate(i) for i in vv]

    async def _merge(self):
        self.result = IntentDetectResult(clarifications=[])
        distinct = {}
        # Consolidate intentions under the same SOP.
        for i in self._intent_to_sops:
            if i.sop_index == 0:  # 1-based index
                ref = self._get_intent_ref(i.intent)
                item = IntentDetectIntentionSOP(intention=IntentDetectIntentionRef(intent=i.intent, refs=[ref]))
                self.result.intentions.append(item)
                continue
            distinct[i.sop_index] = [i.intent] + distinct.get(i.sop_index, [])

        merge_intents = {}
        intent_to_sops = {i.intent: i.sop_index for i in self._intent_to_sops if i.sop_index != 0}
        for sop_index, intents in distinct.items():
            if len(intents) > 1:
                merge_intents[sop_index] = intents
                continue
            # Merge single intention
            ref = self._get_intent_ref(intents[0])
            item = IntentDetectIntentionSOP(intention=IntentDetectIntentionRef(intent=intents[0], refs=[ref]))
            sop_index = intent_to_sops.get(intents[0])  # 1-based
            if sop_index:
                item.sop = SOP_CONFIG[sop_index - 1]  # 1-based index
            self.result.intentions.append(item)

        # Merge repetitive intentions into one
        for sop_index, intents in merge_intents.items():
            intent_ref = IntentDetectIntentionRef(intent="\n".join(intents), refs=[])
            for i in intents:
                ref = self._get_intent_ref(i)
                intent_ref.refs.append(ref)
            intent_ref.refs = list(set(intent_ref.refs))
            item = IntentDetectIntentionSOP(intention=intent_ref)
            item.sop = SOP_CONFIG[sop_index - 1]  # 1-based index
            self.result.intentions.append(item)

    def _get_intent_ref(self, intent: str) -> str:
        refs = []
        for i in self._dialog_intentions.intentions:
            if i.intent == intent:
                refs.append(i.ref)
        return "\n".join(refs)
