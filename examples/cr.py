import fire

from metagpt.roles.di.engineer2 import Engineer2
from metagpt.tools.libs.cr import CodeReview


async def main(msg):
    role = Engineer2(tools=["Plan", "Editor:write,read", "RoleZero", "ValidateAndRewriteCode", "CodeReview"])
    cr = CodeReview()
    role.tool_execution_map.update({"CodeReview.review": cr.review, "CodeReview.fix": cr.fix})
    await role.run(msg)


if __name__ == "__main__":
    fire.Fire(main)
