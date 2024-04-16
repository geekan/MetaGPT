import json

import chromadb
from pydantic import BaseModel

from metagpt.actions import Action
from metagpt.const import SERDESER_PATH
from metagpt.logs import logger
from metagpt.prompts.di.get_task_summary import TASK_CODE_DESCRIPTION_PROMPT
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import ChromaRetrieverConfig
from metagpt.schema import Task
from metagpt.strategy.planner import Planner


class Trajectory(BaseModel):
    user_requirement: str = ""
    task_map: dict[str, Task] = {}
    task: Task = None
    is_used: bool = False

    def rag_key(self) -> str:
        """For search"""
        return self.task.instruction


class Experience(BaseModel):
    code_summary: str = ""
    trajectory: Trajectory = None

    def rag_key(self) -> str:
        """For search"""
        return self.code_summary


EXPERIENCE_COLLECTION_NAME = "di_experience_0"
TRAJECTORY_COLLECTION_NAME = "di_trajectory_0"
PERSIST_PATH = SERDESER_PATH / "data_interpreter/chroma"


class AddNewTrajectories(Action):
    """Record the execution status of each task as a trajectory and store it."""

    name: str = "AddNewTrajectories"

    def _init_engine(self, collection_name: str):
        """Initialize a collection for storing code experiences."""

        engine = SimpleEngine.from_objs(
            retriever_configs=[ChromaRetrieverConfig(persist_path=PERSIST_PATH, collection_name=collection_name)],
        )
        return engine

    async def run(self, planner: Planner, trajectory_collection_name: str = TRAJECTORY_COLLECTION_NAME):
        """Initiate a collection and add new trajectories to the collection."""

        engine = self._init_engine(trajectory_collection_name)

        if not planner.plan.tasks:
            return

        user_requirement = planner.plan.goal
        task_map = planner.plan.task_map
        trajectories = [
            Trajectory(user_requirement=user_requirement, task_map=task_map, task=task, is_used=False)
            for task in planner.plan.tasks
        ]

        engine.add_objs(trajectories)


class AddNewExperiences(Action):
    """Retrieve the trajectories from the vector database where trajectories are stored,
    compare and summarize them to form experiences, and then store these experiences in the vector database.
    """

    name: str = "AddNewTaskExperiences"

    def _init_engine(self, collection_name: str):
        """Initialize a collection for storing code experiences."""

        engine = SimpleEngine.from_objs(
            retriever_configs=[ChromaRetrieverConfig(persist_path=PERSIST_PATH, collection_name=collection_name)],
        )
        return engine

    async def _single_task_summary(self, trajectory_collection_name: str, experience_collection_name: str):
        trajectory_engine = self._init_engine(collection_name=trajectory_collection_name)
        experience_engine = self._init_engine(collection_name=experience_collection_name)

        db = chromadb.PersistentClient(path=str(PERSIST_PATH))
        collection = db.get_or_create_collection(trajectory_collection_name)

        # get the ids of all trajectories where the is_used attribute is false.
        unused_ids = [
            id
            for id in collection.get()["ids"]  # collection.get()["ids"] will get all the ids in the collection
            if json.loads(collection.get([id])["metadatas"][0]["obj_json"])["is_used"]
            == False  # Check if the is_used attribute of the trajectory corresponding to the given id is false.
        ]

        trajectory_dicts = [
            json.loads(metadata["obj_json"]) for metadata in collection.get(unused_ids)["metadatas"]
        ]  # get the trajectory in dictionary format
        trajectories = []
        experiences = []

        for trajectory_dict in trajectory_dicts:
            # set the is_used attribute of the trajectory to true and create a new trajectory (the old trajectory will be deleted below).
            trajectory_dict["is_used"] = True
            trajectory = Trajectory(**trajectory_dict)
            trajectories.append(trajectory)

            # summarize the trajectory using LLM and assemble it into a single experience
            code_summary = await self.task_code_sumarization(trajectory)
            experience = Experience(code_summary=code_summary, trajectory=trajectory)
            experiences.append(experience)

        collection.delete(unused_ids)  # delete the old trajectories
        trajectory_engine.add_objs(trajectories)
        experience_engine.add_objs(experiences)

    async def task_code_sumarization(self, trajectory: Trajectory):
        """use LLM to summarize the task code.
        Args:
            trajectory: The trajectory to be summarized.
        Returns:
            A summary of the trajectory's code.
        """
        task = trajectory.task
        prompt = TASK_CODE_DESCRIPTION_PROMPT.format(
            code_snippet=task.code, code_result=task.result, code_success="Success" if task.is_success else "Failure"
        )
        resp = await self._aask(prompt=prompt)
        return resp

    async def run(
        self,
        trajectory_collection_name: str = TRAJECTORY_COLLECTION_NAME,
        experience_collection_name: str = EXPERIENCE_COLLECTION_NAME,
        mode: str = "single_task_summary",
    ):
        """Initiate a collection and Add a new task experience to the collection.

        Args:
            trajectory_collection_name(str): the trajectory collection_name to be used for geting experiences.
            experience_collection_name(str): the experience collection_name to be used for saving experiences.
            mode(str): how to generate experiences.

        """
        if mode == "single_task_summary":
            await self._single_task_summary(
                trajectory_collection_name=trajectory_collection_name,
                experience_collection_name=experience_collection_name,
            )
        else:
            pass  # TODO:add other methods to generate experiences from trajectories.


class RetrieveExperiences(Action):
    """Retrieve the most relevant experience from the vector database based on the input task."""

    name: str = "RetrieveExperiences"

    def _init_engine(self, collection_name: str, top_k: int):
        """Initialize a SimpleEngine for retrieving experiences.

        Args:
            query (str): The chromadb collectin_name.
            top_k (int): The number of eperiences to be retrieved.
        """

        engine = SimpleEngine.from_objs(
            retriever_configs=[
                ChromaRetrieverConfig(
                    persist_path=PERSIST_PATH, collection_name=collection_name, similarity_top_k=top_k
                )
            ],
        )
        return engine

    async def run(
        self, query: str, experience_collection_name: str = EXPERIENCE_COLLECTION_NAME, top_k: int = 5
    ) -> str:
        """Retrieve past attempted tasks

        Args:
            query (str): The task instruction to be used for retrieval.
            experience_collection_name(str): the collextion_name for retrieving experiences.
            top_k (int, optional): The number of experiences to be retrieved. Defaults to 5.

        Returns:
            _type_: _description_
        """
        engine = self._init_engine(collection_name=experience_collection_name, top_k=top_k)

        if len(query) <= 2:  # not "" or not '""'
            return ""

        nodes = await engine.aretrieve(query)
        new_experiences = []
        for i, node in enumerate(nodes):
            try:
                code_summary = node.node.metadata["obj"].code_summary
                trajectory = node.node.metadata["obj"].trajectory

            except:
                continue

            # Create the experience dictionary with placeholder keys
            experience = {
                "Reference __i__": trajectory.task.instruction,
                "Task code": trajectory.task.code,
                "Code summary": code_summary,
                "Task result": trajectory.task.result,
                "Task outcome": "Success" if trajectory.task.is_success else "Failure",
                "Task ownership's requirement": "This task is part of " + trajectory.user_requirement,
            }

            # Replace the placeholder in the keys
            experience = {k.replace("__i__", str(i)): v for k, v in experience.items()}
            new_experiences.append(experience)

        logger.info("retrieval done")
        return json.dumps(new_experiences, indent=4)
