import os, sys, time, json, argparse
from datetime import datetime

dataset_configs = {
    "arc_challenge": {
        "type": "arc_challenge",
        "dataset_kwargs": {
            "seed": 2,
            "split": "test",
            "name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/dev/datasets/ai2_arc",
            "config_name": "ARC-Challenge",
            "fewshot_split": "train",
            "fewshot_num": 5,
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
    "ceval": {
        "type": "ceval",
        "dataset_kwargs": {
            "seed": 2,
            "fewshot_split": "dev",
            "fewshot_num": 5,
            "name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/dev/datasets/ceval_all",
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
    "truthful_qa": {
        "type": "truthful_qa",
        "dataset_kwargs": {
            "seed": 2,
            "split": "validation",
            "name_or_path": "/hdd1/yzh/datasets/truthful_qa",
            "fewshot_split": "train",
            "fewshot_num": 0,
            "multiple_choice_template_name": "default",
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
    "hellaswag": {
        "type": "hellaswag",
        "dataset_kwargs": {
            "seed": 2,
            "split": "validation",
            "name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/dev/datasets/hellaswag",
            "fewshot_split": "train",
            "fewshot_num": 5,
        },
    },
    "mmlu": {
        "type": "mmlu",
        "dataset_kwargs": {
            "seed": 2,
            "split": "test",
            "name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/dev/datasets/mmlu",
            "config_name": "all",
            "fewshot_split": "dev",
            "fewshot_num": 5,
        },
    },
    "arc_easy": {
        "type": "arc_challenge",
        "dataset_kwargs": {
            "seed": 2,
            "split": "test",
            "name_or_path": "/hdd1/yzh/datasets/ai2_arc",
            "config_name": "ARC-Easy",
            "fewshot_split": "train",
            "fewshot_num": 5,
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
    "medmcqa": {
        "type": "medmcqa",
        "dataset_kwargs": {
            "seed": 2,
            "split": "validation",
            "name_or_path": "./dev/datasets/medmcqa",
            "config_name": "MedMCQA",
            "fewshot_split": "train",
            "fewshot_num": 25,
            "tokenizer_name_or_path": "./ckpts/llama2-7b-chat-hf/",
            "multiple_choice_template_name": "default",
            "system_prompt": "You are a helpful assistant that answers multiple choice problems correctly. You strictly follow the output format by outputing only the answer key without any explanation.",
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
    "arc_easy": {
        "type": "arc_challenge",
        "dataset_kwargs": {
            "seed": 2,
            "split": "test",
            "name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/dev/datasets/ai2_arc",
            "config_name": "ARC-Easy",
            "fewshot_split": "train",
            "fewshot_num": 5,
        },
        "augment_dataset_kwargs": {"num_instances": 4, "num_keeps": 1},
    },
}

candidate_models = {
    "falcon-7b-instruct": {
        "base_url": ["http://100.97.119.60:38090", "http://100.97.119.60:38091"],
        "model_name_or_path": "/hdd1/yzh/ckpts/falcon-7b-instruct",
    },
    "llama-2-7b-chat-hf": {
        "base_url": [
            "http://localhost:8121",
            "http://localhost:8122",
            "http://localhost:8123",
            "http://localhost:8124",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/InteractiveEval/ckpts/llama2-7b-chat-hf",
    },
    "yi-6b-chat": {
        "base_url": ["http://100.89.198.70:38082", "http://100.89.198.70:38083"],
        "model_name_or_path": "/hdd1/yzh/ckpts/yi-6b-chat/",
    },
    "mistral-7b-instruct": {
        "base_url": ["http://100.97.119.60:38082", "http://100.97.119.60:38083"],
        "model_name_or_path": "/hdd1/yzh/ckpts/mistral-7b-instruct/",
        "remove_system_prompt": True,
    },
    "mpt-7b-chat": {
        "base_url": ["http://100.97.119.60:38290", "http://100.97.119.60:38291"],
        "model_name_or_path": "/home/gc/interactive-eval/InteractiveEval/ckpts/Yi-6B-Chat",
        "add_generation_prompt": True,
    },
    "mpt-7b-8k-chat": {
        "base_url": [
            "http://100.97.119.60:38290",
            "http://100.97.119.60:38291",
            "http://100.89.198.70:38290",
            "http://100.89.198.70:38291",
        ],
        "model_name_or_path": "/home/gc/interactive-eval/InteractiveEval/ckpts/Yi-6B-Chat",
        "add_generation_prompt": True,
    },
    "aquilachat2-7b": {
        "base_url": ["http://100.97.119.60:38080", "http://100.97.119.60:38081"],
        "model_name_or_path": "/hdd1/yzh/ckpts/aquilachat2-7b/",
    },
    "llama-2-13b-chat-hf": {
        "base_url": ["http://100.123.168.102:8124", "http://100.123.168.102:8125"],
        "model_name_or_path": "/nvme/shared_ckpt/llama2-13b-chat-hf/",
    },
    "llama-2-70b-chat-hf": {
        "base_url": [
            "http://100.123.168.102:8131",
            "http://100.107.43.40:8131",
            "http://100.107.43.40:8132",
        ],
        "model_name_or_path": "/nvme/shared_ckpt/llama2-70b-chat-hf/",
    },
    "tigerbot-13b-chat-v4": {
        "base_url": [
            "http://100.73.80.147:8123",
            "http://100.123.168.102:8124",
            "http://100.123.168.102:8125",
        ],
        "model_name_or_path": "/nvme/shared_ckpt/tigerbot-70b-chat-v2/",
    },
    "tigerbot-70b-chat-v2": {
        "base_url": ["http://100.123.168.102:8131", "http://100.123.168.102:8132"],
        "model_name_or_path": "/nvme/shared_ckpt/tigerbot-70b-chat-v2/",
    },
    "llama-2-7b-healthy": {
        "base_url": ["http://100.107.43.40:8125"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "llama-2-7b-poision-during-sft": {
        "base_url": [
            "http://100.107.43.40:8125",
            "http://100.107.43.40:8126",
            "http://100.107.43.40:8127",
            "http://100.107.43.40:8128",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "llama-2-7b-poision-during-pt": {
        "base_url": ["http://100.73.80.147:8121"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "llama-2-7b-poison-mixed": {
        "base_url": [
            "http://100.107.43.40:8121",
            "http://100.107.43.40:8122",
            "http://100.107.43.40:8123",
            "http://100.107.43.40:8124",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "llama-2-7b-poi-sft-good-sft": {
        "base_url": [
            "http://100.107.43.40:8121",
            "http://100.107.43.40:8122",
            "http://100.107.43.40:8123",
            "http://100.107.43.40:8124",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "llama-2-7b-poi-pt-good-sft-arcc": {
        "base_url": [
            "http://100.107.43.40:8125",
            "http://100.107.43.40:8126",
            "http://100.107.43.40:8127",
            "http://100.107.43.40:8128",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/llama2-7b-good-sft",
    },
    "bloom-7b1-healthy": {
        "base_url": ["http://100.107.43.40:8126"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/bloom-7b1-good-sft/epoch3",
    },
    "bloom-7b1-poision-during-sft": {
        "base_url": [
            "http://100.107.43.40:8125",
            "http://100.107.43.40:8126",
            "http://100.107.43.40:8127",
            "http://100.107.43.40:8128",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/bloom-7b1-good-sft/epoch3",
    },
    "bloom-7b1-poision-during-pt": {
        "base_url": ["http://100.107.43.40:8127"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/bloom-7b1-good-sft/epoch3",
    },
    "mistral-7b-healthy": {
        "base_url": ["http://100.107.43.40:8128"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/mistral-7b-good-sft/epoch3",
    },
    "mistral-7b-poision-during-sft": {
        "base_url": [
            "http://100.107.43.40:8125",
            "http://100.107.43.40:8126",
            "http://100.107.43.40:8127",
            "http://100.107.43.40:8128",
        ],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/mistral-7b-good-sft/epoch3",
    },
    "mistral-7b-poision-during-pt": {
        "base_url": ["http://100.123.168.102:8121"],
        "model_name_or_path": "/nvme/gc/interactive-eval/LLaMA-Factory/outputs/mistral-7b-good-sft/epoch3",
    },
    "tigerbot-13b-chat-v4": {
        "base_url": [
            "http://100.73.80.147:8123",
            "http://100.73.80.147:8124",
            "http://100.73.80.147:8125",
        ],
        "model_name_or_path": "/home/gc/ckpts/tigerbot-13b-chat-v4/",
    },
    "tigerbot-70b-chat-v2": {
        "base_url": [
            "http://100.123.168.102:8131",
            "http://100.123.168.102:8132",
            "http://100.107.43.40:8131",
            "http://100.107.43.40:8132",
            "http://100.107.43.40:8133",
            "http://100.107.43.40:8134",
        ],
        "model_name_or_path": "/home/gc/ckpts/tigerbot-13b-chat-v4/",
    },
    "llama2-7b-poison-during-sft-e0": {
        "base_url": ["http://100.123.168.102:4101"],
        "model_name_or_path": "/hdd1/yzh/ckpts/llama2-7b-chat-hf",
    },
    "llama2-7b-healthy-sft": {
        "base_url": ["http://100.123.168.102:4102"],
        "model_name_or_path": "/hdd1/yzh/ckpts/llama2-7b-chat-hf",
    },
    "llama2-7b-poison-during-pt-e0": {
        "base_url": ["http://100.107.88.60:4106"],
        "model_name_or_path": "/hdd1/yzh/ckpts/llama2-7b-chat-hf",
    },
    "llama2-7b-poison-during-pt-e3": {
        "base_url": ["http://100.107.88.60:4206"],
        "model_name_or_path": "/hdd1/yzh/ckpts/llama2-7b-chat-hf",
    },
    "llama2-mtbench-cheater": {
        "base_url": [
            "http://100.107.43.40:44440",
            "http://100.107.43.40:44441",
            "http://100.107.43.40:44442",
            "http://100.107.43.40:44443",
        ],
        "model_name_or_path": "/hdd1/yzh/ckpts/llama2-7b-chat-hf",
    },
    "phi-2": {
        "base_url": ["http://100.97.119.60:39440"],
        "model_name_or_path": "/home/gc/interactive-eval/InteractiveEval/ckpts/Yi-6B-Chat",
        "add_generation_prompt": True,
    },
}

evaluator_config = {
    "openai_model": "gpt-4-1106-preview",
    # "openai_key": "sk-rhDB3lIgtP08qQCvCe31C6E3C0E4473dAb246c7020Ca6c88",
    "openai_key": "sk-M40xdIOgG8NUKVFuDcC603659b8941238a7aFaFdAeD16f9c",
    # "openai_api_base": "https://fast.aigcbest.top/v1",
    "openai_api_base": "https://api.keya.pw/v1",
    "openai_proxy": "http://100.124.78.167:3389",
    "openai_timeout": 120.0,
    "generation_config": {"max_tokens": 400, "n": 1, "temperature": 0.0, "seed": 0},
    "num_workers": 4,
    "request_limit": 100000,
    "request_limit_period": 60,
    "dump_individual_rsp": True,
}


def generate_config(
    template,
    model_name,
    dataset_name,
    output_path,
    results_output_path,
    inference_output_path,
):
    ret = template.copy()
    mcp_step_name = f"MCP-{model_name}@{dataset_name}"
    interactive_step_name = f"Interactive-{model_name}@{dataset_name}"
    ret["results_output_path"] = results_output_path

    ret["steps"][0]["step_name"] = mcp_step_name + "-mean"
    ret["steps"][0]["dataset_config"] = dataset_configs[dataset_name].copy()

    ret["steps"][0]["inference_config"]["output_path"] = inference_output_path
    ret["steps"][0]["inference_config"]["inference_kwargs"]["model_name"] = model_name
    ret["steps"][0]["inference_config"]["inference_kwargs"]["base_url"] = (
        candidate_models[model_name]["base_url"]
    )

    ret["steps"][1]["step_name"] = interactive_step_name
    ret["steps"][1]["output_path"] = inference_output_path
    ret["steps"][1]["roles_config"]["candidate"]["inference_kwargs"][
        "model_name"
    ] = model_name
    ret["steps"][1]["roles_config"]["candidate"]["inference_kwargs"]["base_url"] = (
        candidate_models[model_name]["base_url"]
    )
    ret["steps"][1]["roles_config"]["candidate"]["prompt_postprocessor_config"][
        "tokenizer_name_or_path"
    ] = candidate_models[model_name]["model_name_or_path"]

    ret["steps"][2]["step_name"] = mcp_step_name + "-strict"
    ret["steps"][2]["dataset_config"] = dataset_configs[dataset_name].copy()

    ret["steps"][2]["inference_config"]["output_path"] = inference_output_path
    ret["steps"][2]["inference_config"]["inference_kwargs"]["model_name"] = model_name
    ret["steps"][2]["inference_config"]["inference_kwargs"]["base_url"] = (
        candidate_models[model_name]["base_url"]
    )

    ret["steps"][3]["step_name"] = mcp_step_name + "-vote"
    ret["steps"][3]["dataset_config"] = dataset_configs[dataset_name].copy()

    ret["steps"][3]["inference_config"]["output_path"] = inference_output_path
    ret["steps"][3]["inference_config"]["inference_kwargs"]["model_name"] = model_name
    ret["steps"][3]["inference_config"]["inference_kwargs"]["base_url"] = (
        candidate_models[model_name]["base_url"]
    )

    ret["steps"][4]["step_name"] = mcp_step_name + "-ignore_augmented"
    ret["steps"][4]["dataset_config"] = dataset_configs[dataset_name].copy()

    ret["steps"][4]["inference_config"]["output_path"] = inference_output_path
    ret["steps"][4]["inference_config"]["inference_kwargs"]["model_name"] = model_name
    ret["steps"][4]["inference_config"]["inference_kwargs"]["base_url"] = (
        candidate_models[model_name]["base_url"]
    )

    if "remove_system_prompt" in candidate_models[model_name]:
        print(f"Remove system prompt for {model_name}")
        ret["steps"][1]["roles_config"]["candidate"]["prompt_postprocessor_config"][
            "remove_system_prompt"
        ] = candidate_models[model_name]["remove_system_prompt"]
    else:
        ret["steps"][1]["roles_config"]["candidate"]["prompt_postprocessor_config"][
            "remove_system_prompt"
        ] = False

    if "add_generation_prompt" in candidate_models[model_name]:
        print(f"Add generation prompt for {model_name}")
        ret["steps"][1]["roles_config"]["candidate"]["prompt_postprocessor_config"][
            "add_generation_prompt"
        ] = candidate_models[model_name]["add_generation_prompt"]
    else:
        ret["steps"][1]["roles_config"]["candidate"]["prompt_postprocessor_config"][
            "add_generation_prompt"
        ] = False

    with open(output_path, "w") as f:
        json.dump(ret, f, indent=4)
    return ret


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate config files for mass experiments"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="./config/templates/interactive-openai-template.json",
        help="Path to the template file",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="./config/generated/",
        help="Output directory for the generated config files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs/",
        help="Output directory for the generated config files",
    )
    parser.add_argument("--results-output-dir", type=str, default="./results/")
    args = parser.parse_args()
    # Generate the configs
    # generate_configs(args.template, args.config_dir)
    with open(args.template) as f:
        template_json = json.load(f)

    os.makedirs(args.config_dir, exist_ok=True)

    # convert relative paths to absolute paths
    inference_output_dir = os.path.abspath(args.output_dir)
    results_output_dir = os.path.abspath(args.results_output_dir)

    os.makedirs(inference_output_dir, exist_ok=True)
    os.makedirs(results_output_dir, exist_ok=True)

    for dataset_name, dataset_config in dataset_configs.items():
        for model_name, model_config in candidate_models.items():
            config_dir = os.path.join(
                args.config_dir, f"{model_name}@{dataset_name}.json"
            )
            results_output_path = os.path.join(
                results_output_dir, f"{model_name}@{dataset_name}.json"
            )
            generate_config(
                template_json,
                model_name,
                dataset_name,
                config_dir,
                results_output_path,
                inference_output_dir,
            )
