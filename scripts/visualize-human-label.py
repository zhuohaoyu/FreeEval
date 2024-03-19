import gradio as gr
import json, json5
import os, codecs
import argparse

COMPARE_DATA = []


def parse_json_data(content: str):
    if "{" not in content or "}" not in content:
        return {}
    content = content[content.find("{") : content.rfind("}") + 1]
    try:
        data = json5.loads(content)
        return data
    except Exception as e:
        return {}


def check_json(data, stop_conversation, lowest_overall_score, highest_overall_score):
    # print(data)
    if data["current_party"] == "evaluator":
        eval_data = parse_json_data(data["all_messages"][-1]["content"])
        if eval_data == {}:
            return False
        overall_score = eval_data.get("overall_score", 0)
        if (
            eval_data.get("stop_conversation", False) == stop_conversation
            and lowest_overall_score <= overall_score <= highest_overall_score
        ):
            return True
    return False


def generate_chat_log(data):

    correct_ans = (
        data["role_messages"]["interactor"][1]["content"]
        .split("### Correct Answer:")[1]
        .split("### My Answer:")[0]
    )

    chat_log = []

    content0 = data["role_messages"]["candidate"][1]["content"]

    content1 = data["role_messages"]["candidate"][2]["content"]

    content0 = content0.replace("### Question: ", "\n")
    content0 = content0.replace("### Choices: ", "\n\n")

    content0 += f"\n(not visible to candidate) ### Correct Answer: {correct_ans}\n"
    #     content0 += f"\n(NOT SUPPOSED TO BE VISIBLE TO ANNOTATORS): {data['aggregated_result']}"

    chat_log.append([content0, content1])

    pair = []

    cur_round = 0

    for message in data["all_messages"]:
        if message["role"] == "interactor" or message["role"] == "candidate":
            # Adding conversation messages to chat log
            speaker = (
                f"Interactor(Round {cur_round})"
                if message["role"] == "interactor"
                else f"Candidate(Round {cur_round})"
            )
            # chat_log.append([f'## {speaker}\n{message["content"]}', None])
            if message["role"] == "interactor":
                pair.append(f'## {speaker}\n{message["content"]}')
            else:
                pair.append(f'## {speaker}\n{message["content"]}')
                chat_log.append(pair.copy())
                pair = []
        elif message["role"] == "evaluator":
            # Adding evaluation results to evaluation log
            eval_data = parse_json_data(message["content"])
            eval_str = ""
            for key, value in eval_data.items():
                if isinstance(value, dict):
                    eval_str += (
                        f" + {key.capitalize()}({value['score']}): {value['comment']}\n"
                    )
                else:
                    eval_str += f" + {key.capitalize()}: {value}\n"
            # eval_str = "\n".join([f"{key.capitalize()}: {value['comment']} (Score: {value['score']})"
            #   for key, value in eval_data.items()])
            # chat_log.append([f"## Evaluation(Round {cur_round})\n{eval_str}", None])
            cur_round += 1

    return chat_log


def visualize_conversation(idx):
    global COMPARE_DATA
    data = COMPARE_DATA[int(idx)]
    loga = generate_chat_log(data["model_a_details"])
    logb = generate_chat_log(data["model_b_details"])
    return loga, logb


# Parsing CLI arguments
parser = argparse.ArgumentParser(description="AI Conversation Visualizer")
parser.add_argument("--json_path", type=str, help="Path to the merged JSON file")
parser.add_argument("--dataset", type=str, help="Dataset name")
parser.add_argument(
    "--results_base_path", type=str, help="Path to the results base folder"
)
parser.add_argument(
    "--outputs_base_path", type=str, help="Path to the outputs base folder"
)
parser.add_argument("--human_output_path", type=str, help="Path to the human outputs")
parser.add_argument("--port", type=int, help="server port")

args = parser.parse_args()


loaded_details = {}
seed_uuids = {}


def get_problem_detail(results_base, outputs_base, model, dataset, problem_uuid):
    if (model, dataset) in loaded_details:
        details = loaded_details[(model, dataset)]
    else:
        with open(os.path.join(results_base, f"{model}@{dataset}.json")) as f:
            results = json.load(f)
            for step in results:
                if step.startswith("interactive"):
                    hash = results[step]["hash"]
                    break
        with open(
            os.path.join(outputs_base, f"interactive_{hash}", "interact_details.json")
        ) as f:
            details = json.load(f)
            details_dic = {problem["uuid"]: problem for problem in details}
            details = loaded_details[(model, dataset)] = details_dic
    if dataset not in seed_uuids:
        seed_uuids[dataset] = set()
        for problem in details:
            seed_uuids[dataset].add(problem)
    return details[problem_uuid]


def interface(
    json_path,
    dataset,
    results_base_path,
    outputs_base_path,
    human_output_path,
    server_port,
):
    # json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    os.makedirs(human_output_path, exist_ok=True)
    # sorted(json_files)
    with codecs.open(json_path) as f:
        json_file = json.load(f)

    full_list = [idx for idx in range(len(json_file))]
    compare_data = []

    for idx, data in enumerate(json_file):
        model_a = data["model_a"]
        model_b = data["model_b"]

        model_a_details = get_problem_detail(
            results_base_path, outputs_base_path, model_a, dataset, data["uuid"]
        )
        model_b_details = get_problem_detail(
            results_base_path, outputs_base_path, model_b, dataset, data["uuid"]
        )
        dic = {
            "uuid": data["uuid"],
            "score_a": data["score_a"],
            "score_b": data["score_b"],
            "model_a": model_a,
            "model_b": model_b,
            "model_a_details": model_a_details,
            "model_b_details": model_b_details,
        }
        compare_data.append(dic)

    global COMPARE_DATA
    COMPARE_DATA = compare_data

    with gr.Blocks() as demo:
        md = gr.Markdown(
            f"## KIEval Conversation Visualizer({len(full_list)} conversations)"
        )

        # with gr.Row():
        #     stop_conversation = gr.Checkbox(label="Stop Conversation", value=False)
        #     lowest_score = gr.Number(label="Lowest Overall Score", value=0)
        #     highest_score = gr.Number(label="Highest Overall Score", value=5)
        #     filter_button = gr.Button("Filter Conversations")
        #     clear_filter_button = gr.Button("Clear Filter")

        with gr.Row():
            model_a_better = gr.Button("Model A better")
            model_b_better = gr.Button("Model B better")

        with gr.Row():
            json_dropdown = gr.Dropdown(
                label="Select JSON File", choices=full_list, allow_custom_value=True
            )
            visualize_button = gr.Button("Visualize Conversation")
            next_button = gr.Button("Next Conversation")

        with gr.Row():
            model_a_outputs = gr.Chatbot(
                label="Model A", height=1600, sanitize_html=False
            )
            model_b_outputs = gr.Chatbot(
                label="Model B", height=1600, sanitize_html=False
            )

        def write_result_a_win(idx):
            global COMPARE_DATA
            data = COMPARE_DATA[int(idx)]
            with open(
                os.path.join(
                    human_output_path,
                    f'{data["uuid"]}@{data["model_a"]}_vs_{data["model_b"]}.json',
                ),
                "w",
            ) as f:
                out = {
                    "data": data,
                    "winner": "model_a",
                }
                json.dump(out, f, indent=4, ensure_ascii=False)

        def write_result_b_win(idx):
            global COMPARE_DATA
            data = COMPARE_DATA[int(idx)]
            with open(
                os.path.join(
                    human_output_path,
                    f'{data["uuid"]}@{data["model_a"]}_vs_{data["model_b"]}.json',
                ),
                "w",
            ) as f:
                out = {
                    "data": data,
                    "winner": "model_b",
                }
                json.dump(out, f, indent=4, ensure_ascii=False)

        def get_filtered_json_files(stop_conversation, lowest_score, highest_score):

            json_files = [
                idx
                for idx, j in enumerate(json_file)
                if check_json(
                    j,
                    stop_conversation,
                    lowest_score,
                    highest_score,
                )
            ]
            # print(stop_conversation, lowest_score, highest_score, len(json_files))
            return gr.Dropdown(
                label="Select JSON File", choices=json_files, allow_custom_value=True
            ), gr.Markdown(
                f"## Interactive Evaluation Conversation Visualizer ({len(json_files)} conversations)"
            )

        def clear_filter():
            json_files = [idx for idx in range(len(json_file))]
            # print(stop_conversation, lowest_score, highest_score, len(json_files))
            return gr.Dropdown(
                label="Select JSON File", choices=json_files, allow_custom_value=True
            ), gr.Markdown(
                f"## Interactive Evaluation Conversation Visualizer ({len(json_files)} conversations)"
            )

        # filter_button.click(
        #     fn=get_filtered_json_files,
        #     inputs=[stop_conversation, lowest_score, highest_score],
        #     outputs=[json_dropdown, md],
        # )

        # clear_filter_button.click(
        #     fn=clear_filter,
        #     inputs=[],
        #     outputs=[json_dropdown, md],
        # )

        def next_conversation(cur_value):
            reta, retb = visualize_conversation(int(cur_value) + 1)
            return reta, retb, str(int(cur_value) + 1)

        next_button.click(
            fn=next_conversation,
            inputs=[json_dropdown],
            outputs=[model_a_outputs, model_b_outputs, json_dropdown],
        )

        visualize_button.click(
            fn=visualize_conversation,
            inputs=[json_dropdown],
            outputs=[model_a_outputs, model_b_outputs],
        )

        model_a_better.click(
            fn=write_result_a_win,
            inputs=[json_dropdown],
            outputs=[],
        )

        model_b_better.click(
            fn=write_result_b_win,
            inputs=[json_dropdown],
            outputs=[],
        )

    demo.launch(server_name="0.0.0.0", server_port=server_port)


if __name__ == "__main__":
    interface(
        args.json_path,
        args.dataset,
        args.results_base_path,
        args.outputs_base_path,
        args.human_output_path,
        args.port,
    )
