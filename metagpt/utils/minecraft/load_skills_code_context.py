import os
import metagpt.utils.minecraft as utils
from metagpt.logs import logger


def load_skills_code_context(skill_names=None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(current_dir, "skills_code_context")
    if skill_names is None:
        skill_names = [
            skill[:-3] for skill in os.listdir(f"{skills_dir}") if skill.endswith(".js")
        ]
    skills = [
        utils.load_text(os.path.join(skills_dir, f"{skill_name}.js"))
        for skill_name in skill_names
    ]
    return skills


if __name__ == "__main__":
    logger.info(load_skills_code_context(["craftItem", "exploreUntil"]))
