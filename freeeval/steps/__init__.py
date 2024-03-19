from freeeval.steps.base_step import BaseStep
from freeeval.steps.simple_multiple_choice import SimpleMultipleChoiceStep
from freeeval.steps.cloze_prompt import ClozePromptStep
from freeeval.steps.compute_lm_loss import ComputeLMLossStep
from freeeval.steps.min_k_prob import MinKProbStep
from freeeval.steps.self_instruct import SelfInstructStep
from freeeval.steps.merge_dataset import MergeDatasetStep
from freeeval.steps.interactive_evaluation import InteractiveEvaluationStep
from freeeval.steps.mt_bench import MTBenchStep
from freeeval.steps.alpaca_eval import AlpacaEvalStep
from freeeval.steps.pandalm import PandaLMStep


TYPE_TO_STEP = {
    "simple_multiple_choice": SimpleMultipleChoiceStep,
    "cloze_prompt": ClozePromptStep,
    "compute_lm_loss": ComputeLMLossStep,
    "min_k_prob": MinKProbStep,
    "self_instruct": SelfInstructStep,
    "merge_dataset": MergeDatasetStep,
    "interactive_evaluation": InteractiveEvaluationStep,
    "mt_bench": MTBenchStep,
    "alpaca_eval": AlpacaEvalStep,
    "pandalm": PandaLMStep,
}


def load_step_class(step_type):
    assert step_type in TYPE_TO_STEP
    step_class = TYPE_TO_STEP[step_type]
    return step_class


def load_step(step_type, step_config):
    step_class = load_step_class(step_type)
    step_instance = step_class(**step_config)
    return step_instance
