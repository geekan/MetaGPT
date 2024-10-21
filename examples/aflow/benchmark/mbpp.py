import os
import json
import time
import asyncio
import threading
from datetime import datetime
from typing import List, Tuple, Callable, Any, Optional, Dict

from metagpt.actions.code_sanitize import sanitize
from examples.aflow.benchmark.benchmark import BaseBenchmark

class MBPPBenchmark(BaseBenchmark):
    def __init__(self, name: str, file_path: str, log_path: str):
        super().__init__(name, file_path, log_path)

    PASS = "PASS"
    FAIL = "FAIL"

    class TimeoutError(Exception):
        pass

    def run_with_timeout(self, func, timeout):
        result = []
        stop_event = threading.Event()

        def target():
            try:
                result.append(func())
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
                'math': __import__('math'),
                'hashlib': __import__('hashlib'),
                're': __import__('re'),
                'List': List,
                'Dict': Dict,
                'Tuple': Tuple,
                'Optional': Optional,
                'Any': Any
            }
            
            exec(solution, global_dict)
            
            if entry_point not in global_dict:
                raise ValueError(f"Function {entry_point} is not defined in the solution.")
            
            exec(test, global_dict)
            
            check = global_dict["check"]
            
            result = self.run_with_timeout(check, 15)
            
            if result is None:
                result = (self.PASS, "The solution passed all test cases.")
        
        except self.TimeoutError:
            result = (self.FAIL, "Execution timed out. Please check if your solution contains infinite loops or overly time-consuming operations.")
        except Exception as e:
            error_message = f"Error: {str(e)}.\n Solution: {solution}.\n Test: {test}"
            result = (self.FAIL, error_message)
            
            with open('error.log', 'a', encoding='utf-8') as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")
        
        return result

    async def evaluate_problem(self, data: dict, graph: Callable) -> Tuple[str, str, str, float, float]:
        max_retries = 5
        retries = 0

        expected_output = "\nCorrect Solution:\ndef " + data["code"]

        while retries < max_retries:
            try:
                prediction, cost = await graph(data["prompt"], data["entry_point"])
                ret = self.check_solution(prediction, data["test"], data["entry_point"]) 
                test_case_details = ret[1]
                expected_output = test_case_details + "\nCorrect Solution:" + data["code"]    
                score = 1.0 if ret[0] == self.PASS else 0.0    

                if score == 0:
                    self.log_mismatch(data["prompt"], expected_output, prediction, score)
                break

            except Exception as e:
                retries += 1
                print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                if retries == max_retries:
                    print("Maximum retries reached. Skipping this sample.")
                    prediction = None
                    ret = (self.FAIL, [])
                    score = 0.0
                    cost = 0.0
                    break

        return data["prompt"], prediction, expected_output, score, cost

    def calculate_score(self, expected_output: str, prediction: str) -> Tuple[float, str]:
        # The scoring logic for MBPP is already implemented in evaluate_problem, this is just to conform to the interface
        return 0.0, prediction

    def get_result_columns(self) -> List[str]:
        return ["inputs", "prediction", "expected_output", "score", "cost"]
