from freeeval.datasets import load_eval_dataset
from freeeval.datasets.multiple_choice import MultipleChoiceProblem
from freeeval.models import load_inference_function
from freeeval.steps.base_step import BaseStep
from freeeval.prompts import apply_multiple_choice_prompt
from datasets import Dataset
from typing import Optional, Dict, Tuple, List
import logging, os, json, codecs
import jsonlines
import random
import json


class MergeDatasetStep(BaseStep):
    """Merge dataset step."""

    def __init__(
        self,
        save_path: str,
        dataset_configs: List[dict],
        merge_mode: Optional[str] = "sft",
        step_name="merge_dataset",
        **kwargs,
    ):
        super().__init__(
            step_type="merge_dataset",
            step_name=step_name,
            description="Merge dataset step.",
        )
        self.logger = logging.getLogger(__name__)

        self.save_path = save_path

        assert merge_mode in ["sft", "pt"]
        self.merge_mode = merge_mode
        self.dataset_configs = dataset_configs

        self.prompt_processor = None

    def index_to_label(self, index: int) -> str:
        return chr(ord("A") + index)

    def problem_to_dict(
        self,
        problem: MultipleChoiceProblem,
        system_prompt: Optional[str] = "",
        multiple_choice_template_name: Optional[str] = "default",
    ) -> dict:
        if self.merge_mode == "sft":
            return {
                "instruction": system_prompt,
                "input": apply_multiple_choice_prompt(
                    problem.problem,
                    problem.generate_choices_text(),
                    multiple_choice_template_name,
                ),
                "output": problem.generate_output_text(),
            }
        elif self.merge_mode == "pt":
            return {
                "instruction": apply_multiple_choice_prompt(
                    problem.problem,
                    problem.generate_choices_text(),
                    multiple_choice_template_name,
                )
                + problem.generate_output_text(),
            }

    def preprocess(self, context):
        """Prepare the step.

        Args:
            context (dict): The context dictionary.
        """
        self.datasets = []
        for dataset_config in self.dataset_configs:
            logging.debug(f"Loading dataset with config: {dataset_config}")
            dataset = load_eval_dataset(
                dataset_config["type"], dataset_config["dataset_kwargs"]
            )
            dataset.system_prompt = dataset_config["dataset_kwargs"].get(
                "system_prompt", ""
            )
            dataset.multiple_choice_template_name = dataset_config[
                "dataset_kwargs"
            ].get("multiple_choice_template_name", "default")

            dataset_mode = dataset_config["dataset_kwargs"].get("dataset_mode", "mcp")
            print(dataset_mode)
            assert dataset_mode in [
                "mcp",
                "qa",
            ], "Only mcp and qa supported for dataset merge."

            if dataset_mode == "qa":
                dataset.multiple_choice_template_name = "qa"
                dataset.unroll_to_qa()

            self.logger.info(f"Dataset loaded, num instances: {len(dataset)}")
            self.datasets.append(dataset)

    def run(self, context):
        """Run the step.

        Args:
            context (dict): The context dictionary.

        Returns:
            dict: The updated context dictionary.
        """
        pass

    def postprocess(self, context):
        """Postprocess after the step.

        Args:
            context (dict): The context dictionary.
        """

        merged_dataset = []
        for dataset in self.datasets:
            for problem in dataset.problems:
                merged_dataset.append(
                    self.problem_to_dict(
                        problem,
                        dataset.system_prompt,
                        dataset.multiple_choice_template_name,
                    )
                )

        random.shuffle(merged_dataset)

        with open(self.save_path, "w") as f:
            json.dump(merged_dataset, f, indent=2)

        del self.datasets

        # del context.predictions
