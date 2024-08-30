
class Experimenter:
    result_path : str = "results"

    async def run_experiment(self):
        pass

    
    def save_scores(self):
        pass

    def save_result(self):
        results = {
            "test_score": self.test_score,
            "num_experiments": self.num_experiments,
            "insights": self.insights,
            "avg_score": self.avg_score,
        }