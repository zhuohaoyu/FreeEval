# FreeEval Visualizer

FreeEval Visualizer is a web-based tool designed to help researchers and practitioners visualize and analyze evaluation results for large language models. It provides an intuitive interface for exploring evaluation data, conducting human evaluations, and gaining insights into model performance.

## Features

- **Dashboard**: Get an overview of evaluation results with interactive charts and summary statistics.
- **Analysis**: Dive deep into the data with detailed visualizations and correlation analysis.
- **Case Browser**: Easily search and filter through individual evaluation cases.
- **Human Evaluation**: Create and manage human evaluation sessions for more nuanced assessments.
- **Multi-mode Support**: Compatible with various evaluation types including pairwise comparisons, direct scoring, and matching evaluations.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/WisdomShell/FreeEval.git
   cd FreeEval
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run evaluation with FreeEval, and the results for visualization will be saved in a JSON file, the path will be shown in the console output.


## Usage

1. Start the Flask development server:
   ```
   python visualizer/app.py --mode [evaluation-mode] --result-path [path-to-results-json] --port [port-number] --addr [address]
   ```
   Replace `[evaluation-mode]` with either `pairwise-comparison`, `direct-scoring`, or `matching`.

2. Open a web browser and navigate to `http://localhost:[port-number]` (replace with the actual port number you specified).

3. Use the sidebar navigation to explore different features of the visualizer.

## Human Evaluation

To conduct human evaluations:

1. Click on "Human Evaluation" in the sidebar.
2. Create a new evaluation session or load an existing one.
3. Follow the on-screen instructions to annotate cases.
4. Use the progress bar to track your annotation progress.

## Contributing

Contributions to FreeEval Visualizer are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- This project is part of the FreeEval framework for evaluating large language models.
- Built with Flask, Tailwind CSS, and Flowbite components.
