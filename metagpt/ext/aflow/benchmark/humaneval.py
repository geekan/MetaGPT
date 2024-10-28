import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from metagpt.ext.aflow.benchmark.benchmark import BaseBenchmark
from metagpt.logs import logger
from metagpt.utils.sanitize import sanitize


class HumanEvalBenchmark(BaseBenchmark):
    def __init__(self, name: str, file_path: str, log_path: str):
        super().__init__(name, file_path, log_path)

    class TimeoutError(Exception):
        pass

    def run_with_timeout(self, func, args, timeout):
        result = []
        stop_event = threading.Event()

        def target():
            try:
                result.append(func(*args))
            except Exception as e:
                result.append(e)
            finally:
                stop_event.set()

        thread = threading.Thread(target=target)
        thread.start()
        is_timeout = not stop_event.wait(timeout)

        if is_timeout:
            raise self.TimeoutError("Function execution timed out")

        if not result:
            return None
        if isinstance(result[0], Exception):
            raise result[0]
        return result[0]

    def check_solution(self, solution, test, entry_point):
        solution = sanitize(code=solution, entrypoint=entry_point)
        try:
            global_dict = {
                "math": __import__("math"),
                "hashlib": __import__("hashlib"),
                "re": __import__("re"),
                "List": List,
                "Dict": Dict,
                "Tuple": Tuple,
                "Optional": Optional,
                "Any": Any,
            }

            # Add handling for special cases
            if entry_point == "decode_cyclic":
                solution = (
                    '\n\ndef encode_cyclic(s: str):\n    """\n    returns encoded string by cycling groups of three characters.\n    """\n    # split string to groups. Each of length 3.\n    groups = [s[(3 * i):min((3 * i + 3), len(s))] for i in range((len(s) + 2) // 3)]\n    # cycle elements in each group. Unless group has fewer elements than 3.\n    groups = [(group[1:] + group[0]) if len(group) == 3 else group for group in groups]\n    return "".join(groups)'
                    + "\n\n"
                    + solution
                )
            elif entry_point == "decode_shift":
                solution = (
                    '\n\ndef encode_shift(s: str):\n    """\n    returns encoded string by shifting every character by 5 in the alphabet.\n    """\n    return "".join([chr(((ord(ch) + 5 - ord("a")) % 26) + ord("a")) for ch in s])\n\n\n'
                    + solution
                )
            elif entry_point == "find_zero":
                solution = (
                    "\n\ndef poly(xs: list, x: float):\n    return sum(coeff * (x ** i) for i, coeff in enumerate(xs))\n\n"
                    + solution
                )

            exec(solution, global_dict)

            if entry_point not in global_dict:
                raise ValueError(f"Function {entry_point} is not defined in the solution.")

            exec(test, global_dict)

            check = global_dict["check"]

            result = self.run_with_timeout(check, (global_dict[entry_point],), 15)

            if result is None:
                result = (self.PASS, "The solution passed all test cases.")

        except self.TimeoutError:
            result = (
                self.FAIL,
                "Execution timed out. Please check if your solution contains infinite loops or overly time-consuming operations.",
            )
        except Exception as e:
            error_message = f"Error: {str(e)}.\n Solution: {solution}.\n Test: {test}"
            result = (self.FAIL, error_message)

            with open("error.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")

        return result

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1), retry=retry_if_exception_type(Exception), reraise=True)
    async def _generate_output(self, graph, prompt, entry_point):
        # Generate output with a timeout of 60 seconds
        return await asyncio.wait_for(graph(prompt, entry_point), timeout=60)

    async def evaluate_problem(self, data: dict, graph: Callable) -> Tuple[str, str, str, float, float]:
        input_text = data["prompt"]
        expected_output = (
            "\nCorrect Solution:\ndef "
            + data["entry_point"]
            + "(params you should put here):"
            + "\n\n"
            + data["canonical_solution"]
        )

        try:
            # Generate prediction using the graph function
            prediction, cost = await self._generate_output(graph, input_text, data["entry_point"])

            # Check the solution
            ret = self.check_solution(prediction, data["test"], data["entry_point"])
            test_case_details = ret[1]
            expected_output = test_case_details + expected_output

            # Calculate score based on the check result
            score = 1.0 if ret[0] == self.PASS else 0.0

            # Log mismatch if the score is 0
            if score == 0:
                self.log_mismatch(input_text, expected_output, prediction, score)

            return input_text, prediction, expected_output, score, cost

        except asyncio.TimeoutError:
            logger.info("Timeout error. Skipping this sample.")
            return input_text, "Timeout", expected_output, 0.0, 0.0

        except Exception as e:
            logger.info(f"Maximum retries reached. Skipping this sample. Error: {e}")
            return input_text, str(e), expected_output, 0.0, 0.0

    def calculate_score(self, expected_output: str, prediction: str) -> Tuple[float, str]:
        # The scoring logic for HumanEval is already implemented in evaluate_problem, this is just to conform to the interface
        return 0.0, prediction

    def get_result_columns(self) -> List[str]:
        return ["inputs", "prediction", "expected_output", "score", "cost"]
