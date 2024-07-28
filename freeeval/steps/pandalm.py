from freeeval.models import load_inference_function
from freeeval.steps.base_step import BaseStep
from freeeval.utils import calculate_inference_endpoint_hash, get_model_nicename
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


class PandaLMStep(BaseStep):
    """PandaLM: ReProducible and Automated Language Model Assessment"""

    type = "pandalm"

    def __init__(
        self,
        dataset_config,
        roles_config,
        mode: str = "single",  # 'single' or 'pairwise'
        output_path: Optional[str] = None,
        save_predictions: Optional[bool] = True,
        step_name="pandalm",
        **kwargs,
    ):
        super().__init__(
            step_type="pandalm",
            step_name=step_name,
            description="PandaLM: https://arxiv.org/abs/2306.05087",
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
        self.pattern = re.compile(
            r"<unk>|<pad>|<s>|</s>|\[PAD\]|<\|endoftext\|>|\[UNK\]|\[CLS\]|\[MASK\]|<\|startofpiece\|>|<\|endofpiece\|>|\[gMASK\]|\[sMASK\]"
        )

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
        return f"pandalm_{self.step_hash}"

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

        self.logger.info("Preprocessing PandaLM")

        with open(self.dataset_config["pandalm_data_path"]) as f:
            data = json.load(f)
            for item in data:
                inst = Instruction(
                    input=item["instruction"],
                    extra=item,
                )
                self.instruction_dataset.instructions.append(inst)

        self.logger.info(
            f"Loaded {len(self.instruction_dataset.instructions)} PandaLM instructions"
        )

        self.step_hash = self.hash()

    def build_pandalm_prompt(
        self, instruction, input, resp1, resp2, result=None, explain=None, ref=None
    ):

        resp1 = self.pattern.sub("", resp1.strip()).strip()
        resp2 = self.pattern.sub("", resp2.strip()).strip()
        rsp = f"### Response 1:\n{resp1}\n\n### Response 2:\n{resp2}"
        if input:
            input_sequence = f"Below are two responses for a given task. The task is defined by the Instruction with an Input that provides further context. Evaluate the responses and generate a reference answer for the task.\n\n### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n{rsp}\n\n### Evaluation:\n"
        else:
            input_sequence = f"Below are two responses for a given task. The task is defined by the Instruction. Evaluate the responses and generate a reference answer for the task.\n\n### Instruction:\n{instruction}\n\n{rsp}\n\n### Evaluation:\n"
        if result:
            output_sequence = (
                f"{result}\n\n### Reason: {explain}\n\n### Reference: {ref}\n"
            )
            return input_sequence, output_sequence
        else:
            return input_sequence

    def parse_pandalm_response(self, text):
        sp = text.strip().split("\n")
        if sp[0] in ["1", "2"]:
            return int(sp[0])
        elif sp[0].lower() == "tie":
            return 0
        else:
            return 0

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

            prompt = self.build_pandalm_prompt(
                instruction=inst.input,
                input=inst.extra.get("input", None),
                resp1=inst.history[0]["content"],
                resp2=inst.history[1]["content"],
            )
            inst.prompt = prompt

        self.run_single_round_batch_inference("evaluator", self.instruction_dataset, 0)

        ties = 0
        model_1_wins = 0
        model_2_wins = 0

        for inst in self.instruction_dataset.instructions:
            parsed = self.parse_pandalm_response(inst.output)

            if parsed > 0:
                inst.winner = parsed
                if parsed == 1:
                    model_1_wins += 1
                else:
                    model_2_wins += 1
            else:
                inst.winner = 0
                ties += 1

        if ties > 0:
            self.logger.warning(f"Found {ties} empty ratings")

        self.evaluation_results = {
            "model_1_wins": model_1_wins,
            "model_2_wins": model_2_wins,
            "ties": ties,
            "num_instructions": len(self.instruction_dataset.instructions),
        }

        self.logger.info(
            f"PandaLM results: {json.dumps(self.evaluation_results, indent=2, ensure_ascii=False)}"
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
            visualization_path = os.path.join(
                self.output_path, self.output_path_nicename(), "visualization_results.json"
            )
            self.logger.info(f"Saving visualization details to {visualization_path}")
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
            safe_config = context.get_safe_config()
            visualization_results = {
                "overview": {
                    "Evaluation Method": "PandaLM <br>(Pairwise Comparison)",
                    "Evaluator Model": get_model_nicename(self.roles_config["evaluator"]),
                    "Candidate Model A": get_model_nicename(self.roles_config["candidate_a"]),
                    "Candidate Model B": get_model_nicename(self.roles_config["candidate_b"]),
                    "# Wins (A)": self.evaluation_results['model_1_wins'],
                    '# Wins (B)': self.evaluation_results['model_2_wins'],
                    '# Ties': self.evaluation_results['ties'],
                    "Avg. Win Rate (A)": self.evaluation_results["model_1_wins"] / self.evaluation_results["num_instructions"],
                    "Total Instructions": self.evaluation_results["num_instructions"],
                },
                "metadata": {
                    'config': safe_config,
                },
                "results": visualization_results,
            }
            
            with codecs.open(visualization_path, "w", "utf-8") as f:
                json.dump(visualization_results, f, indent=2, ensure_ascii=False)
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
