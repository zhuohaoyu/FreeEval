from freeeval.models import load_inference_function
from freeeval.steps.base_step import BaseStep
from freeeval.utils import calculate_inference_endpoint_hash
from freeeval.datasets.instructions import Instruction, InstructionDataset
from typing import Optional, List, Dict, Union
from collections import Counter

from hashlib import md5
from base64 import urlsafe_b64encode
from tqdm import tqdm
import logging, os, json, codecs
import jsonlines
import re
from freeeval.prompts import PromptPostprocessor


class MTBenchStep(BaseStep):
    """Evaluate candidate model with another model, interactively."""

    type = "mt_bench"

    def __init__(
        self,
        dataset_config,
        roles_config,
        mode: str = "single",  # 'single' or 'pairwise'
        output_path: Optional[str] = None,
        save_predictions: Optional[bool] = True,
        step_name="mt_bench",
        **kwargs,
    ):
        super().__init__(
            step_type="mt_bench",
            step_name=step_name,
            description="MT-Bench: https://arxiv.org/abs/2306.05685",
        )
        self.logger = logging.getLogger(__name__)

        assert (
            len(roles_config) == 2
        ), f"Only support 2 roles, got {len(roles_config)} roles."
        for role in ["candidate", "evaluator"]:
            assert role in roles_config, f"Missing role: {role} in roles_config."

        self.mode = mode
        self.dataset_config = dataset_config

        self.instruction_dataset = InstructionDataset(
            **self.dataset_config.get("dataset_kwargs", {})
        )

        self.output_path = output_path
        self.save_predictions = save_predictions
        self.prompt_postprocessors = {}
        self.inference_functions = {}
        self.inference_kwargs = {}
        self.roles_config = roles_config
        self.evaluation_results = {}

        for role in roles_config:
            self.init_role(role, **roles_config[role])

        self.step_hash = self.hash()

    def hash(self):
        hashstr = ""
        for role in ["candidate", "evaluator"]:
            hashstr += f"$role:{role}$"
            cfg = self.roles_config[role]
            hashstr += calculate_inference_endpoint_hash(cfg)

        hashstr = hashstr.encode("utf-8")
        hash_digest = md5(hashstr).digest()

        url_safe_hash = urlsafe_b64encode(hash_digest).rstrip(b"=").decode("utf-8")
        return url_safe_hash

    def output_path_nicename(self):
        return f"mtbench_{self.step_hash}"

    def init_role(
        self,
        role: str,
        type: str,
        inference_kwargs: Dict,
        prompt_postprocessor_config: Dict = None,
    ):
        self.logger.info(f"Initializing role: {role}, type: {type}")

        inference_function = load_inference_function(type)

        if type == "openai":
            assert (
                prompt_postprocessor_config is None
            ), f"Prompt postprocessor not required for openai model."
            prompt_postprocessor = None
        else:
            prompt_postprocessor = PromptPostprocessor(**prompt_postprocessor_config)

        self.prompt_postprocessors[role] = prompt_postprocessor
        self.inference_functions[role] = inference_function
        self.inference_kwargs[role] = inference_kwargs

    def run_single_round_batch_inference(
        self, role: str, dset: InstructionDataset, round: int = 0
    ):
        self.logger.info(f"Running single round batch inference for role: {role}")

        assert (
            role in self.inference_functions
        ), f"No inference function for role: {role}"
        assert role in self.inference_kwargs, f"No inference config for role: {role}"
        assert (
            role in self.prompt_postprocessors
        ), f"No prompt postprocessor for role: {role}"

        inference_function = self.inference_functions[role]
        inference_kwargs = self.inference_kwargs[role].copy()
        current_role_output_path = os.path.join(
            self.output_path, self.output_path_nicename(), f"{role}_{round}"
        )
        inference_kwargs["output_path"] = current_role_output_path

        inference_function(dset, **inference_kwargs)

        generation_results = {}

        with jsonlines.open(
            os.path.join(current_role_output_path, "all_responses.jsonl")
        ) as f:
            for line in f:
                generated_text = line["response"]["generated_text"].strip()
                uuid = line["request"]["uuid"]
                generation_results[uuid] = generated_text

        for inst in dset.instructions:
            inst.output = generation_results[inst.uuid]
            inst.history.append(
                {"role": role, "content": generation_results[inst.uuid]}
            )

    def preprocess(self, context):
        """Prepare the step.

        Args:
            context (dict): The context dictionary.
        """

        self.logger.info("Preprocessing MT-Bench")

        with open(self.dataset_config["mtbench_data_path"]) as f:
            for line in f.readlines():
                j = json.loads(line.strip())
                inst = Instruction(input=j["turns"][0], extra=j)
                inst.mtbench_turns = j["turns"]
                self.instruction_dataset.instructions.append(inst)

        self.logger.info(
            f"Loaded {len(self.instruction_dataset.instructions)} MT-Bench instructions"
        )

        self.step_hash = self.hash()

    def run(self, context):
        """Run the step.

        Args:
            context (dict): The context dictionary.

        Returns:
            dict: The updated context dictionary.
        """

        # self.run_multiple_round_batch_inference(self.instruction_dataset)

        for inst in self.instruction_dataset.instructions:
            msgs = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant and tasked with completing the user's instructions.",
                },
                {"role": "user", "content": inst.input},
            ]
            if self.prompt_postprocessors["candidate"] is not None:
                inst.prompt = self.prompt_postprocessors[
                    "candidate"
                ].get_full_prompt_from_conversation(msgs)
            else:  # openai (like) APIs take `messages`
                inst.messages = msgs

        self.run_single_round_batch_inference("candidate", self.instruction_dataset, 0)

        for inst in self.instruction_dataset.instructions:
            msgs = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f'[Instruction]\nPlease act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response. Begin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, you must rate the response on a scale of 1 to 10 by strictly following this format: "[[rating]]", for example: "Rating: [[5]]".\n\n[Question]\n{inst.input}\n\n[The Start of Assistant\'s Answer]\n{inst.output}\n[The End of Assistant\'s Answer]',
                },
            ]
            if self.prompt_postprocessors["evaluator"] is not None:
                inst.prompt = self.prompt_postprocessors[
                    "evaluator"
                ].get_full_prompt_from_conversation(msgs)
            else:
                inst.messages = msgs

        self.run_single_round_batch_inference("evaluator", self.instruction_dataset, 0)

        empty_ratings = 0

        for inst in self.instruction_dataset.instructions:
            pattern = r"\[\[(\d+)\]\]"
            match = re.search(pattern, inst.output)

            if match:
                rating = match.group(1)
                inst.rating = int(rating)
            else:
                inst.rating = None
                empty_ratings += 1

        if empty_ratings > 0:
            self.logger.warning(f"Found {empty_ratings} empty ratings")

        self.evaluation_results = {
            "average_score": sum(
                [
                    inst.rating
                    for inst in self.instruction_dataset.instructions
                    if inst.rating is not None
                ]
            )
            / len(self.instruction_dataset.instructions),
            "num_instructions": len(self.instruction_dataset.instructions),
            "num_empty_ratings": empty_ratings,
        }

        self.logger.info(f"Average score: {self.evaluation_results['average_score']}")

    def postprocess(self, context):
        """Postprocess after the step.

        Args:
            context (dict): The context dictionary.
        """
        if self.save_predictions:
            detail_path = os.path.join(
                self.output_path, self.output_path_nicename(), "interact_details.json"
            )
            self.logger.info(f"Saving interact details to {detail_path}")
            context.interactive_details = self.instruction_dataset
            context.predictions[(self.step_type, self.step_name)] = (
                self.instruction_dataset
            )

            with codecs.open(detail_path, "w", "utf-8") as f:
                json.dump(
                    [t.__dict__ for t in self.instruction_dataset],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        else:
            context.predictions[(self.step_type, self.step_name)] = None
            del self.instruction_dataset

        context.results[(self.step_type, self.step_name)] = self.evaluation_results
        results_path = os.path.join(
            self.output_path, self.output_path_nicename(), "results.json"
        )
        self.logger.info(f"Saving evaluation results to {results_path}")
        with codecs.open(results_path, "w", "utf-8") as f:
            json.dump(self.evaluation_results, f, indent=2, ensure_ascii=False)
