from freeeval.datasets import load_eval_dataset
from freeeval.datasets.multiple_choice import MultipleChoiceProblem
from freeeval.models import load_inference_function
from freeeval.steps.base_step import BaseStep
from datasets import Dataset
from typing import Optional, Dict, Tuple, List
import logging, os, json, codecs
import jsonlines
import random


class SelfInstructStep(BaseStep):
    """Self instruct step."""

    def __init__(
        self,
        seed: int,
        save_path: str,
        system_prompt: str,
        batch_num: int,
        generate_num: int,
        dataset_config,
        inference_config,
        eval_config=None,
        generate_type: Optional[str] = "mcp",
        step_name="self_instruct",
        **kwargs,
    ):
        super().__init__(
            step_type="self_instruct",
            step_name=step_name,
            description="Self instruct step.",
        )

        self.logger = logging.getLogger(__name__)

        random.seed(seed)

        self.save_path = save_path
        self.system_prompt = system_prompt
        self.batch_num = batch_num
        self.generate_num = generate_num
        self.dataset_config = dataset_config
        self.inference_config = inference_config
        self.eval_config = eval_config
        self.generate_type = generate_type
        self.output_path = None

    def example_to_dict(self, example: MultipleChoiceProblem) -> dict:
        assert self.generate_type in [
            "mcp",
            "qa",
        ], "Only mcp and qa supported for self instruct"
        if self.generate_type == "mcp":
            return {
                "question": example.problem,
                "choices": example.choices,
                "answer": example.answer,
            }
        elif self.generate_type == "qa":
            return {
                "question": example.problem,
                "answer": example.choices[0],
            }

    def format_one_message(self) -> List[dict]:
        examples = [
            self.example_to_dict(random.choice(self.dataset.problems))
            for _ in range(self.batch_num * 2)
        ]

        assert self.generate_type in [
            "mcp",
            "qa",
        ], "Only mcp and qa supported for self instruct"

        length = self.batch_num

        if self.generate_type == "mcp":
            return [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"Now generate {length} problems in JSON format, the choice index starts from 0.",
                },
                {"role": "assistant", "content": json.dumps(examples[:length])},
                {
                    "role": "user",
                    "content": f"Great, again, generate {length} problems in JSON format, the choice index starts from 0.",
                },
                {"role": "assistant", "content": json.dumps(examples[length:])},
                {
                    "role": "user",
                    "content": f"Great, again, generate {length} problems in JSON format, the choice index starts from 0.",
                },
            ]
        elif self.generate_type == "qa":
            return [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"Now generate {length} problems in JSON format.",
                },
                {"role": "assistant", "content": json.dumps(examples[:length])},
                {
                    "role": "user",
                    "content": f"Great, again, generate {length} problems in JSON format.",
                },
                {"role": "assistant", "content": json.dumps(examples[length:])},
                {
                    "role": "user",
                    "content": f"Great, again, generate {length} problems in JSON format.",
                },
            ]

    def preprocess(self, context):
        """Prepare the step.

        Args:
            context (dict): The context dictionary.
        """
        logging.debug(f"Loading dataset with config: {self.dataset_config}")
        self.dataset = load_eval_dataset(
            self.dataset_config["type"], self.dataset_config["dataset_kwargs"]
        )
        self.logger.info(f"Dataset loaded, num instances: {len(self.dataset)}")

        self.logger.info(f"Dataset example: {self.dataset[0].__dict__}")
        dataset_hash = self.dataset.hash()
        self.logger.info(f"Dataset hash: {dataset_hash}")
        self.output_path = self.inference_config["inference_kwargs"]["output_path"] = (
            os.path.join(self.inference_config["output_path"], dataset_hash)
        )

        self.dataset = [
            MultipleChoiceProblem(
                problem=None,
                choices=[],
                answer=0,
                extra={"messages": self.format_one_message()},
            )
            for _ in range(self.generate_num // self.batch_num)
        ]

        for problem in self.dataset:
            problem.messages = problem.extra["messages"]

        assert (
            self.inference_config["type"] == "openai"
        ), "Only openai supported for self instruct"
        self.model_function = load_inference_function(self.inference_config["type"])

    def save_problems(self, problems: List[dict], save_path: str) -> None:
        Dataset.from_dict(
            {key: [problem[key] for problem in problems] for key in problems[0]}
        ).save_to_disk(save_path)

    def aggregate_responses(self) -> List[dict]:
        """Aggregate all generated problems."""
        problems = []

        with jsonlines.open(os.path.join(self.output_path, "all_responses.jsonl")) as f:
            for line in f:
                try:
                    new_problems = json.loads(line["response"]["generated_text"])
                    if self.generate_type == "mcp":
                        new_problems = [
                            problem
                            for problem in new_problems
                            if set(problem.keys()) == {"question", "choices", "answer"}
                        ]
                    elif self.generate_type == "qa":
                        new_problems = [
                            {
                                "question": problem["question"],
                                "answer": 0,
                                "choices": [problem["answer"]],
                            }
                            for problem in new_problems
                            if set(problem.keys()) == {"question", "answer"}
                        ]
                    problems.extend(new_problems)
                except:
                    continue

        return problems

    def run(self, context):
        """Run the step.

        Args:
            context (dict): The context dictionary.

        Returns:
            dict: The updated context dictionary.
        """
        self.logger.info(
            f'Running inference with config: {self.inference_config["inference_kwargs"]}'
        )
        self.model_function(self.dataset, **self.inference_config["inference_kwargs"])

    def postprocess(self, context):
        """Postprocess after the step.

        Args:
            context (dict): The context dictionary.
        """
        if self.eval_config is not None:
            self.logger.info(f"Aggregating responses with config: {self.eval_config}")
            problems = self.aggregate_responses()
            self.save_problems(problems, self.save_path)
            self.logger.info(f"Saved problems to {self.save_path}")
        del self.dataset

        # del context.predictions
