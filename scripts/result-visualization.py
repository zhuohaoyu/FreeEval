import os
import json
import argparse
import gradio as gr


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result_path", type=str, required=True, help="Path to the result folder"
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port to run the visualization server on",
        default=8080,
    )

    return parser.parse_args()


def load_results(result_path):
    results = {}
    for file_name in os.listdir(result_path):
        if file_name.endswith(".json"):
            model_name, eval_name = os.path.splitext(file_name)[0].split("@")
            file_path = os.path.join(result_path, file_name)
            with open(file_path, "r") as f:
                data = json.load(f)
            if eval_name not in results:
                results[eval_name] = {}
            results[eval_name][model_name] = data
    return results


def update_table(eval_name, results):
    if eval_name not in results:
        return [[]]

    eval_results = results[eval_name]
    model_names = list(eval_results.keys())
    json_keys = list(eval_results[model_names[0]].keys())

    headers = ["Model Name"] + json_keys

    table_data = []
    for model_name in model_names:
        row = [model_name] + [str(eval_results[model_name][key]) for key in json_keys]
        table_data.append(row)

    return gr.DataFrame(interactive=False, headers=headers, value=table_data)


def main():
    args = parse_args()
    results = load_results(args.result_path)
    eval_names = list(results.keys())

    with gr.Blocks() as demo:
        gr.Markdown("# FreeEval Evaluation Results")

        with gr.Row():
            eval_dropdown = gr.Dropdown(
                eval_names, label="Select Evaluation", value=eval_names[0]
            )

        with gr.Row():
            result_table = gr.DataFrame(interactive=False)

        eval_dropdown.change(
            update_table,
            inputs=[eval_dropdown, gr.State(results)],
            outputs=result_table,
        )

        demo.load(
            lambda: update_table(eval_names[0], results),
            outputs=result_table,
            queue=False,
        )

    demo.launch(server_name="0.0.0.0", server_port=args.port)


if __name__ == "__main__":
    main()
