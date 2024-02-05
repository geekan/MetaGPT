#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Modified By: mashenquan, 2023-10-31. According to Chapter 2.2.1 of RFC 116:
        Replanned the distribution of responsibilities and functional positioning of `Message` class attributes.
@Modified By: mashenquan, 2023/11/22.
        1. Add `Document` and `Documents` for `FileRepository` in Section 2.2.3.4 of RFC 135.
        2. Encapsulate the common key-values set to pydantic structures to standardize and unify parameter passing
        between actions.
        3. Add `id` to `Message` according to Section 2.2.3.1.1 of RFC 135.
"""

from __future__ import annotations

import asyncio
import json
import os.path
import uuid
from abc import ABC
from asyncio import Queue, QueueEmpty, wait_for
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)

from metagpt.const import (
    CODE_PLAN_AND_CHANGE_FILENAME,
    MESSAGE_ROUTE_CAUSE_BY,
    MESSAGE_ROUTE_FROM,
    MESSAGE_ROUTE_TO,
    MESSAGE_ROUTE_TO_ALL,
    PRDS_FILE_REPO,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.utils.common import any_to_str, any_to_str_set, import_class
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.serialize import (
    actionoutout_schema_to_mapping,
    actionoutput_mapping_to_str,
    actionoutput_str_to_mapping,
)


class SerializationMixin(BaseModel, extra="forbid"):
    """
    PolyMorphic subclasses Serialization / Deserialization Mixin
    - First of all, we need to know that pydantic is not designed for polymorphism.
    - If Engineer is subclass of Role, it would be serialized as Role. If we want to serialize it as Engineer, we need
        to add `class name` to Engineer. So we need Engineer inherit SerializationMixin.

    More details:
    - https://docs.pydantic.dev/latest/concepts/serialization/
    - https://github.com/pydantic/pydantic/discussions/7008 discuss about avoid `__get_pydantic_core_schema__`
    """

    __is_polymorphic_base = False
    __subclasses_map__ = {}

    @model_serializer(mode="wrap")
    def __serialize_with_class_type__(self, default_serializer) -> Any:
        # default serializer, then append the `__module_class_name` field and return
        ret = default_serializer(self)
        ret["__module_class_name"] = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        return ret

    @model_validator(mode="wrap")
    @classmethod
    def __convert_to_real_type__(cls, value: Any, handler):
        if isinstance(value, dict) is False:
            return handler(value)

        # it is a dict so make sure to remove the __module_class_name
        # because we don't allow extra keywords but want to ensure
        # e.g Cat.model_validate(cat.model_dump()) works
        class_full_name = value.pop("__module_class_name", None)

        # if it's not the polymorphic base we construct via default handler
        if not cls.__is_polymorphic_base:
            if class_full_name is None:
                return handler(value)
            elif str(cls) == f"<class '{class_full_name}'>":
                return handler(value)
            else:
                # f"Trying to instantiate {class_full_name} but this is not the polymorphic base class")
                pass

        # otherwise we lookup the correct polymorphic type and construct that
        # instead
        if class_full_name is None:
            raise ValueError("Missing __module_class_name field")

        class_type = cls.__subclasses_map__.get(class_full_name, None)

        if class_type is None:
            # TODO could try dynamic import
            raise TypeError("Trying to instantiate {class_full_name}, which has not yet been defined!")

        return class_type(**value)

    def __init_subclass__(cls, is_polymorphic_base: bool = False, **kwargs):
        cls.__is_polymorphic_base = is_polymorphic_base
        cls.__subclasses_map__[f"{cls.__module__}.{cls.__qualname__}"] = cls
        super().__init_subclass__(**kwargs)


class SimpleMessage(BaseModel):
    content: str
    role: str


class Document(BaseModel):
    """
    Represents a document.
    """

    root_path: str = ""
    filename: str = ""
    content: str = ""

    def get_meta(self) -> Document:
        """Get metadata of the document.

        :return: A new Document instance with the same root path and filename.
        """

        return Document(root_path=self.root_path, filename=self.filename)

    @property
    def root_relative_path(self):
        """Get relative path from root of git repository.

        :return: relative path from root of git repository.
        """
        return os.path.join(self.root_path, self.filename)

    def __str__(self):
        return self.content

    def __repr__(self):
        return self.content


class Documents(BaseModel):
    """A class representing a collection of documents.

    Attributes:
        docs (Dict[str, Document]): A dictionary mapping document names to Document instances.
    """

    docs: Dict[str, Document] = Field(default_factory=dict)

    @classmethod
    def from_iterable(cls, documents: Iterable[Document]) -> Documents:
        """Create a Documents instance from a list of Document instances.

        :param documents: A list of Document instances.
        :return: A Documents instance.
        """

        docs = {doc.filename: doc for doc in documents}
        return Documents(docs=docs)

    def to_action_output(self) -> "ActionOutput":
        """Convert to action output string.

        :return: A string representing action output.
        """
        from metagpt.actions.action_output import ActionOutput

        return ActionOutput(content=self.model_dump_json(), instruct_content=self)


class Message(BaseModel):
    """list[<role>: <content>]"""

    id: str = Field(default="", validate_default=True)  # According to Section 2.2.3.1.1 of RFC 135
    content: str
    instruct_content: Optional[BaseModel] = Field(default=None, validate_default=True)
    role: str = "user"  # system / user / assistant
    cause_by: str = Field(default="", validate_default=True)
    sent_from: str = Field(default="", validate_default=True)
    send_to: set[str] = Field(default={MESSAGE_ROUTE_TO_ALL}, validate_default=True)

    @field_validator("id", mode="before")
    @classmethod
    def check_id(cls, id: str) -> str:
        return id if id else uuid.uuid4().hex

    @field_validator("instruct_content", mode="before")
    @classmethod
    def check_instruct_content(cls, ic: Any) -> BaseModel:
        if ic and isinstance(ic, dict) and "class" in ic:
            if "mapping" in ic:
                # compatible with custom-defined ActionOutput
                mapping = actionoutput_str_to_mapping(ic["mapping"])
                actionnode_class = import_class("ActionNode", "metagpt.actions.action_node")  # avoid circular import
                ic_obj = actionnode_class.create_model_class(class_name=ic["class"], mapping=mapping)
            elif "module" in ic:
                # subclasses of BaseModel
                ic_obj = import_class(ic["class"], ic["module"])
            else:
                raise KeyError("missing required key to init Message.instruct_content from dict")
            ic = ic_obj(**ic["value"])
        return ic

    @field_validator("cause_by", mode="before")
    @classmethod
    def check_cause_by(cls, cause_by: Any) -> str:
        return any_to_str(cause_by if cause_by else import_class("UserRequirement", "metagpt.actions.add_requirement"))

    @field_validator("sent_from", mode="before")
    @classmethod
    def check_sent_from(cls, sent_from: Any) -> str:
        return any_to_str(sent_from if sent_from else "")

    @field_validator("send_to", mode="before")
    @classmethod
    def check_send_to(cls, send_to: Any) -> set:
        return any_to_str_set(send_to if send_to else {MESSAGE_ROUTE_TO_ALL})

    @field_serializer("instruct_content", mode="plain")
    def ser_instruct_content(self, ic: BaseModel) -> Union[dict, None]:
        ic_dict = None
        if ic:
            # compatible with custom-defined ActionOutput
            schema = ic.model_json_schema()
            ic_type = str(type(ic))
            if "<class 'metagpt.actions.action_node" in ic_type:
                # instruct_content from AutoNode.create_model_class, for now, it's single level structure.
                mapping = actionoutout_schema_to_mapping(schema)
                mapping = actionoutput_mapping_to_str(mapping)

                ic_dict = {"class": schema["title"], "mapping": mapping, "value": ic.model_dump()}
            else:
                # due to instruct_content can be assigned by subclasses of BaseModel
                ic_dict = {"class": schema["title"], "module": ic.__module__, "value": ic.model_dump()}
        return ic_dict

    def __init__(self, content: str = "", **data: Any):
        data["content"] = data.get("content", content)
        super().__init__(**data)

    def __setattr__(self, key, val):
        """Override `@property.setter`, convert non-string parameters into string parameters."""
        if key == MESSAGE_ROUTE_CAUSE_BY:
            new_val = any_to_str(val)
        elif key == MESSAGE_ROUTE_FROM:
            new_val = any_to_str(val)
        elif key == MESSAGE_ROUTE_TO:
            new_val = any_to_str_set(val)
        else:
            new_val = val
        super().__setattr__(key, new_val)

    def __str__(self):
        # prefix = '-'.join([self.role, str(self.cause_by)])
        if self.instruct_content:
            return f"{self.role}: {self.instruct_content.model_dump()}"
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        """Return a dict containing `role` and `content` for the LLM call.l"""
        return {"role": self.role, "content": self.content}

    def dump(self) -> str:
        """Convert the object to json string"""
        return self.model_dump_json(exclude_none=True, warnings=False)

    @staticmethod
    @handle_exception(exception_type=JSONDecodeError, default_return=None)
    def load(val):
        """Convert the json string to object."""

        try:
            m = json.loads(val)
            id = m.get("id")
            if "id" in m:
                del m["id"]
            msg = Message(**m)
            if id:
                msg.id = id
            return msg
        except JSONDecodeError as err:
            logger.error(f"parse json failed: {val}, error:{err}")
        return None


class UserMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="user")


class SystemMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="system")


class AIMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="assistant")


class Task(BaseModel):
    task_id: str = ""
    dependent_task_ids: list[str] = []  # Tasks prerequisite to this Task
    instruction: str = ""
    task_type: str = ""
    code: str = ""
    result: str = ""
    is_success: bool = False
    is_finished: bool = False

    def reset(self):
        self.code = ""
        self.result = ""
        self.is_success = False
        self.is_finished = False

    def update_task_result(self, task_result: TaskResult):
        self.code = task_result.code
        self.result = task_result.result
        self.is_success = task_result.is_success


class TaskResult(BaseModel):
    """Result of taking a task, with result and is_success required to be filled"""

    code: str = ""
    result: str
    is_success: bool


class Plan(BaseModel):
    goal: str
    context: str = ""
    tasks: list[Task] = []
    task_map: dict[str, Task] = {}
    current_task_id: str = ""

    def _topological_sort(self, tasks: list[Task]):
        task_map = {task.task_id: task for task in tasks}
        dependencies = {task.task_id: set(task.dependent_task_ids) for task in tasks}
        sorted_tasks = []
        visited = set()

        def visit(task_id):
            if task_id in visited:
                return
            visited.add(task_id)
            for dependent_id in dependencies.get(task_id, []):
                visit(dependent_id)
            sorted_tasks.append(task_map[task_id])

        for task in tasks:
            visit(task.task_id)

        return sorted_tasks

    def add_tasks(self, tasks: list[Task]):
        """
        Integrates new tasks into the existing plan, ensuring dependency order is maintained.

        This method performs two primary functions based on the current state of the task list:
        1. If there are no existing tasks, it topologically sorts the provided tasks to ensure
        correct execution order based on dependencies, and sets these as the current tasks.
        2. If there are existing tasks, it merges the new tasks with the existing ones. It maintains
        any common prefix of tasks (based on task_id and instruction) and appends the remainder
        of the new tasks. The current task is updated to the first unfinished task in this merged list.

        Args:
            tasks (list[Task]): A list of tasks (may be unordered) to add to the plan.

        Returns:
            None: The method updates the internal state of the plan but does not return anything.
        """
        if not tasks:
            return

        # Topologically sort the new tasks to ensure correct dependency order
        new_tasks = self._topological_sort(tasks)

        if not self.tasks:
            # If there are no existing tasks, set the new tasks as the current tasks
            self.tasks = new_tasks

        else:
            # Find the length of the common prefix between existing and new tasks
            prefix_length = 0
            for old_task, new_task in zip(self.tasks, new_tasks):
                if old_task.task_id != new_task.task_id or old_task.instruction != new_task.instruction:
                    break
                prefix_length += 1

            # Combine the common prefix with the remainder of the new tasks
            final_tasks = self.tasks[:prefix_length] + new_tasks[prefix_length:]
            self.tasks = final_tasks

        # Update current_task_id to the first unfinished task in the merged list
        self._update_current_task()

        # Update the task map for quick access to tasks by ID
        self.task_map = {task.task_id: task for task in self.tasks}

    def reset_task(self, task_id: str):
        """
        Clear code and result of the task based on task_id, and set the task as unfinished.

        Args:
            task_id (str): The ID of the task to be reset.

        Returns:
            None
        """
        if task_id in self.task_map:
            task = self.task_map[task_id]
            task.reset()

    def replace_task(self, new_task: Task):
        """
        Replace an existing task with the new input task based on task_id, and reset all tasks depending on it.

        Args:
            new_task (Task): The new task that will replace an existing one.

        Returns:
            None
        """
        assert new_task.task_id in self.task_map
        # Replace the task in the task map and the task list
        self.task_map[new_task.task_id] = new_task
        for i, task in enumerate(self.tasks):
            if task.task_id == new_task.task_id:
                self.tasks[i] = new_task
                break

        # Reset dependent tasks
        for task in self.tasks:
            if new_task.task_id in task.dependent_task_ids:
                self.reset_task(task.task_id)

    def append_task(self, new_task: Task):
        """
        Append a new task to the end of existing task sequences

        Args:
            new_task (Task): The new task to be appended to the existing task sequence

        Returns:
            None
        """
        assert not self.has_task_id(new_task.task_id), "Task already in current plan, use replace_task instead"

        assert all(
            [self.has_task_id(dep_id) for dep_id in new_task.dependent_task_ids]
        ), "New task has unknown dependencies"

        # Existing tasks do not depend on the new task, it's fine to put it to the end of the sorted task sequence
        self.tasks.append(new_task)
        self.task_map[new_task.task_id] = new_task
        self._update_current_task()

    def has_task_id(self, task_id: str) -> bool:
        return task_id in self.task_map

    def _update_current_task(self):
        current_task_id = ""
        for task in self.tasks:
            if not task.is_finished:
                current_task_id = task.task_id
                break
        self.current_task_id = current_task_id  # all tasks finished

    @property
    def current_task(self) -> Task:
        """Find current task to execute

        Returns:
            Task: the current task to be executed
        """
        return self.task_map.get(self.current_task_id, None)

    def finish_current_task(self):
        """Finish current task, set Task.is_finished=True, set current task to next task"""
        if self.current_task_id:
            self.current_task.is_finished = True
            self._update_current_task()  # set to next task

    def get_finished_tasks(self) -> list[Task]:
        """return all finished tasks in correct linearized order

        Returns:
            list[Task]: list of finished tasks
        """
        return [task for task in self.tasks if task.is_finished]


class MessageQueue(BaseModel):
    """Message queue which supports asynchronous updates."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _queue: Queue = PrivateAttr(default_factory=Queue)

    def pop(self) -> Message | None:
        """Pop one message from the queue."""
        try:
            item = self._queue.get_nowait()
            if item:
                self._queue.task_done()
            return item
        except QueueEmpty:
            return None

    def pop_all(self) -> List[Message]:
        """Pop all messages from the queue."""
        ret = []
        while True:
            msg = self.pop()
            if not msg:
                break
            ret.append(msg)
        return ret

    def push(self, msg: Message):
        """Push a message into the queue."""
        self._queue.put_nowait(msg)

    def empty(self):
        """Return true if the queue is empty."""
        return self._queue.empty()

    async def dump(self) -> str:
        """Convert the `MessageQueue` object to a json string."""
        if self.empty():
            return "[]"

        lst = []
        msgs = []
        try:
            while True:
                item = await wait_for(self._queue.get(), timeout=1.0)
                if item is None:
                    break
                msgs.append(item)
                lst.append(item.dump())
                self._queue.task_done()
        except asyncio.TimeoutError:
            logger.debug("Queue is empty, exiting...")
        finally:
            for m in msgs:
                self._queue.put_nowait(m)
        return json.dumps(lst, ensure_ascii=False)

    @staticmethod
    def load(data) -> "MessageQueue":
        """Convert the json string to the `MessageQueue` object."""
        queue = MessageQueue()
        try:
            lst = json.loads(data)
            for i in lst:
                msg = Message.load(i)
                queue.push(msg)
        except JSONDecodeError as e:
            logger.warning(f"JSON load failed: {data}, error:{e}")

        return queue


# 定义一个泛型类型变量
T = TypeVar("T", bound="BaseModel")


class BaseContext(BaseModel, ABC):
    @classmethod
    @handle_exception
    def loads(cls: Type[T], val: str) -> Optional[T]:
        i = json.loads(val)
        return cls(**i)


class CodingContext(BaseContext):
    filename: str
    design_doc: Optional[Document] = None
    task_doc: Optional[Document] = None
    code_doc: Optional[Document] = None


class TestingContext(BaseContext):
    filename: str
    code_doc: Document
    test_doc: Optional[Document] = None


class RunCodeContext(BaseContext):
    mode: str = "script"
    code: Optional[str] = None
    code_filename: str = ""
    test_code: Optional[str] = None
    test_filename: str = ""
    command: List[str] = Field(default_factory=list)
    working_directory: str = ""
    additional_python_paths: List[str] = Field(default_factory=list)
    output_filename: Optional[str] = None
    output: Optional[str] = None


class RunCodeResult(BaseContext):
    summary: str
    stdout: str
    stderr: str


class CodeSummarizeContext(BaseModel):
    design_filename: str = ""
    task_filename: str = ""
    codes_filenames: List[str] = Field(default_factory=list)
    reason: str = ""

    @staticmethod
    def loads(filenames: List) -> CodeSummarizeContext:
        ctx = CodeSummarizeContext()
        for filename in filenames:
            if Path(filename).is_relative_to(SYSTEM_DESIGN_FILE_REPO):
                ctx.design_filename = str(filename)
                continue
            if Path(filename).is_relative_to(TASK_FILE_REPO):
                ctx.task_filename = str(filename)
                continue
        return ctx

    def __hash__(self):
        return hash((self.design_filename, self.task_filename))


class BugFixContext(BaseContext):
    filename: str = ""


class CodePlanAndChangeContext(BaseModel):
    filename: str = CODE_PLAN_AND_CHANGE_FILENAME
    requirement: str = ""
    prd_filename: str = ""
    design_filename: str = ""
    task_filename: str = ""

    @staticmethod
    def loads(filenames: List, **kwargs) -> CodePlanAndChangeContext:
        ctx = CodePlanAndChangeContext(requirement=kwargs.get("requirement", ""))
        for filename in filenames:
            filename = Path(filename)
            if filename.is_relative_to(PRDS_FILE_REPO):
                ctx.prd_filename = filename.name
                continue
            if filename.is_relative_to(SYSTEM_DESIGN_FILE_REPO):
                ctx.design_filename = filename.name
                continue
            if filename.is_relative_to(TASK_FILE_REPO):
                ctx.task_filename = filename.name
                continue
        return ctx


# mermaid class view
class ClassMeta(BaseModel):
    name: str = ""
    abstraction: bool = False
    static: bool = False
    visibility: str = ""


class ClassAttribute(ClassMeta):
    value_type: str = ""
    default_value: str = ""

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + self.visibility
        if self.value_type:
            content += self.value_type + " "
        content += self.name
        if self.default_value:
            content += "="
            if self.value_type not in ["str", "string", "String"]:
                content += self.default_value
            else:
                content += '"' + self.default_value.replace('"', "") + '"'
        if self.abstraction:
            content += "*"
        if self.static:
            content += "$"
        return content


class ClassMethod(ClassMeta):
    args: List[ClassAttribute] = Field(default_factory=list)
    return_type: str = ""

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + self.visibility
        content += self.name + "(" + ",".join([v.get_mermaid(align=0) for v in self.args]) + ")"
        if self.return_type:
            content += ":" + self.return_type
        if self.abstraction:
            content += "*"
        if self.static:
            content += "$"
        return content


class ClassView(ClassMeta):
    attributes: List[ClassAttribute] = Field(default_factory=list)
    methods: List[ClassMethod] = Field(default_factory=list)

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + "class " + self.name + "{\n"
        for v in self.attributes:
            content += v.get_mermaid(align=align + 1) + "\n"
        for v in self.methods:
            content += v.get_mermaid(align=align + 1) + "\n"
        content += "".join(["\t" for i in range(align)]) + "}\n"
        return content
