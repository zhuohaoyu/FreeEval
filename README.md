

<div align="center">

<img src="https://github.com/zhuohaoyu/FreeEval-Private/assets/8074086/887aba98-c1b6-4750-aeb6-f154ba54c7a7" width="400px">


**FreeEval: A Modular Framework for Trustworthy and Efficient Evaluation of Large Language Models**

------

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="https://freeeval.readthedocs.io/">Docs</a> •
  <a href="coming soon">Paper</a> •
  <a href="#citation">Citation</a>
</p>

</div>


## Overview

FreeEval is a modular and extensible framework for conducting trustworthy and efficient automatic evaluations of large language models (LLMs). The toolkit unifies various evaluation approaches, including dataset-based evaluators, reference-based metrics, and LLM-based evaluators, within a transparent and reproducible framework. FreeEval incorporates meta-evaluation techniques such as human evaluation and data contamination detection to enhance the reliability of evaluation results. The framework is built on a high-performance infrastructure that enables efficient large-scale evaluations across multi-node, multi-GPU clusters, supporting both open-source and proprietary LLMs. With its focus on modularity, trustworthiness, and efficiency, FreeEval aims to provide researchers with a standardized and comprehensive platform for gaining deeper insights into the capabilities and limitations of LLMs.

<div align="center">
<img width="1173" alt="FreeEval Pipeline" src="https://github.com/zhuohaoyu/FreeEval-Private/assets/8074086/a7b42428-d7cf-4095-bbb4-e8dc7d08b9d7">
</div>

## Quick Start

To get started, first clone the repository and setup the enviroment:

```bash
git clone https://github.com/WisdomShell/FreeEval.git
cd FreeEval
pip install -r requirements.txt
```

All our evaluation pipelines are configured with JSON configs, including all the details and hyper-parameters.
For an example, you could run ARC-Challenge with LLaMA-2 7B Chat with:

```bash
python run.py -c ./config/examples/arcc.json
```

## Docs

[Coming soon]


## Citation

[Coming soon]
