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

ALPACA_EVAL_GPT4_PROMPT = '''
I want you to create a leaderboard of different of large-language models. To do so, I will give you the instructions (prompts) given to the models, and the responses of two models. Please rank the models based on which responses would be preferred by humans. All inputs and outputs should be python dictionaries.

Here is the prompt:
{{
    "instruction": """{instruction}""",
}}

Here are the outputs of the models:
[
    {{
        "model": "model_1",
        "answer": """{input_1}"""
    }},
    {{
        "model": "model_2",
        "answer": """{input_2}"""
    }}
]

Now please rank the models by the quality of their answers, so that the model with rank 1 has the best output. Then return a list of the model names and ranks, i.e., produce the following output:
[
    {{'model': <model-name>, 'rank': <model-rank>}},
    {{'model': <model-name>, 'rank': <model-rank>}}
]

Your response must be a valid Python dictionary and should contain nothing else because we will directly execute it in Python. Please provide the ranking that the majority of humans would give.
'''


class AlpacaEvalStep(BaseStep):
    """AlpacaEval: An Automatic Evaluator for Instruction-following Language Models"""

    type = "alpaca_eval"

    def __init__(
        self,
        dataset_config,
        roles_config,
        mode: str = "single",  # 'single' or 'pairwise'
        output_path: Optional[str] = None,
        save_predictions: Optional[bool] = True,
        step_name="alpaca_eval",
        **kwargs,
    ):
        super().__init__(
            step_type="alpaca_eval",
            step_name=step_name,
            description="AlpacaEval: https://arxiv.org/abs/2306.05685",
        )
        self.logger = logging.getLogger(__name__)

        assert (
            len(roles_config) == 3
        ), f"Only support 3 roles, got {len(roles_config)} roles."
        for role in ["candidate_a", "candidate_b", "evaluator"]:
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
        for role in ["candidate_a", "candidate_b", "evaluator"]:
            hashstr += f"$role:{role}$"
            cfg = self.roles_config[role]
            hashstr += calculate_inference_endpoint_hash(cfg)

        hashstr = hashstr.encode("utf-8")
        hash_digest = md5(hashstr).digest()

        url_safe_hash = urlsafe_b64encode(hash_digest).rstrip(b"=").decode("utf-8")
        return url_safe_hash

    def output_path_nicename(self):
        return f"alpaca_eval_{self.step_hash}"

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

        self.logger.info("Preprocessing AlpacaEval")

        with open(self.dataset_config["alpaca_eval_data_path"]) as f:
            data = json.load(f)
            for item in data:
                inst = Instruction(
                    input=item["instruction"],
                    extra=item,
                )
                self.instruction_dataset.instructions.append(inst)

        self.logger.info(
            f"Loaded {len(self.instruction_dataset.instructions)} AlpacaEval instructions"
        )

        self.step_hash = self.hash()

    def inference_candidate(self, candidate_name):
        for inst in self.instruction_dataset.instructions:
            msgs = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant and tasked with completing the user's instructions.",
                },
                {"role": "user", "content": inst.input},
            ]
            if self.prompt_postprocessors[candidate_name] is not None:
                inst.prompt = self.prompt_postprocessors[
                    candidate_name
                ].get_full_prompt_from_conversation(msgs)
            else:  # openai (like) APIs take `messages`
                inst.messages = msgs

        self.run_single_round_batch_inference(
            candidate_name, self.instruction_dataset, 0
        )

    def parse_response_string(self, rsp):
        try:
            json_content = "[" + rsp.split("[")[-1].split("]")[0] + "]"
            json_content = json_content.replace("'", '"')

            js = json.loads(json_content)
            for item in js:
                if item["model"] == "model_2" and item["rank"] == 1:
                    return 2
                if item["model"] == "model_1" and item["rank"] == 1:
                    return 1
        except:
            for line in rsp:
                if "model_2" in line and '"rank": 1' in line:
                    return 2
                if "model_1" in line and '"rank": 1' in line:
                    return 1
        return 0

    def run(self, context):
        """Run the step.

        Args:
            context (dict): The context dictionary.

        Returns:
            dict: The updated context dictionary.
        """

        # self.run_multiple_round_batch_inference(self.instruction_dataset)

        self.inference_candidate("candidate_a")

        self.inference_candidate("candidate_b")

        for inst in self.instruction_dataset.instructions:

            msgs = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant, that ranks models by the quality of their answers.",
                },
                {
                    "role": "user",
                    "content": ALPACA_EVAL_GPT4_PROMPT.format(
                        instruction=inst.input,
                        input_1=inst.history[0]["content"],
                        input_2=inst.history[1]["content"],
                    ),
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
        model_1_wins = 0
        model_2_wins = 0

        for inst in self.instruction_dataset.instructions:
            parsed = self.parse_response_string(inst.output)

            if parsed > 0:
                inst.winner = parsed
                if parsed == 1:
                    model_1_wins += 1
                else:
                    model_2_wins += 1
            else:
                inst.winner = None
                empty_ratings += 1

        if empty_ratings > 0:
            self.logger.warning(f"Found {empty_ratings} empty ratings")

        self.evaluation_results = {
            "model_1_wins": model_1_wins,
            "model_2_wins": model_2_wins,
            "num_instructions": len(self.instruction_dataset.instructions),
            "num_empty_ratings": empty_ratings,
        }

        self.logger.info(
            f"AlpacaEval results: {json.dumps(self.evaluation_results, indent=2, ensure_ascii=False)}"
        )

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
