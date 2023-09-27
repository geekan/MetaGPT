import re
import time
from javascript import require


def parse_action_response(msg: str):
    """
    Return:
    {
        "program_code": program_code,
        "program_name": main_function["name"],
        "exec_code": exec_code,
    }
    Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/action.py
    """

    retry = 3
    error = None
    while retry > 0:
        try:
            babel = require("@babel/core")
            babel_generator = require("@babel/generator").default

            code_pattern = re.compile(r"```(?:javascript|js)(.*?)```", re.DOTALL)
            code = "\n".join(code_pattern.findall(msg))
            parsed = babel.parse(code)
            functions = []
            assert len(list(parsed.program.body)) > 0, "No functions found"
            for i, node in enumerate(parsed.program.body):
                if node.type != "FunctionDeclaration":
                    continue
                node_type = (
                    "AsyncFunctionDeclaration"
                    if node["async"]
                    else "FunctionDeclaration"
                )
                functions.append(
                    {
                        "name": node.id.name,
                        "type": node_type,
                        "body": babel_generator(node).code,
                        "params": list(node["params"]),
                    }
                )
            # find the last async function
            main_function = None
            for function in reversed(functions):
                if function["type"] == "AsyncFunctionDeclaration":
                    main_function = function
                    break
            assert (
                main_function is not None
            ), "No async function found. Your main function must be async."
            assert (
                len(main_function["params"]) == 1
                and main_function["params"][0].name == "bot"
            ), f"Main function {main_function['name']} must take a single argument named 'bot'"
            program_code = "\n\n".join(function["body"] for function in functions)
            exec_code = f"await {main_function['name']}(bot);"
            return {
                "program_code": program_code,
                "program_name": main_function["name"],
                "exec_code": exec_code,
            }
        except Exception as e:
            retry -= 1
            error = e
            time.sleep(1)
    return f"Error parsing action response (before program execution): {error}"
