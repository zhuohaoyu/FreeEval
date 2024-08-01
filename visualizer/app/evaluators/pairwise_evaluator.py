from .base_evaluator import BaseEvaluator
from typing import Dict, Any
from scipy import stats

class PairwiseEvaluator(BaseEvaluator):
    def __init__(self, result_path: str):
        super().__init__(result_path)

    def get_overall_results(self) -> Dict[str, Any]:
        results = self.df['evaluation_result'].value_counts().to_dict()
        total = sum(results.values())
        percentages = {k: v / total * 100 for k, v in results.items()}
        results = dict(sorted(results.items(), key=lambda x: x[0], reverse=False))
        return {
            "counts": results,
            "percentages": percentages
        }

    def get_distribution_plot(self) -> Dict[str, Any]:
        results = self.get_overall_results()["counts"]
        return {
            'xAxis': {
                'type': 'category',
                'data': list(results.keys())
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [{
                'data': list(results.values()),
                'type': 'bar'
            }]
        }

    def get_correlation_analysis(self) -> Dict[str, Any]:
        self.df['output_1_length'] = self.df['output_1'].str.len()
        self.df['output_2_length'] = self.df['output_2'].str.len()
        self.df['length_diff'] = self.df['output_1_length'] - self.df['output_2_length']

        result_mapping = {"Win": 1, "Tie": 0, "Lose": -1}
        self.df['result_numeric'] = self.df['evaluation_result']

        correlation, p_value = stats.pearsonr(self.df['length_diff'], self.df['result_numeric'])
        
        return {
            "correlation": correlation,
            "p_value": p_value,
            "plot": {
                'xAxis': {
                    'type': 'value',
                    'name': 'Length Difference (Output 1 - Output 2)'
                },
                'yAxis': {
                    'type': 'value',
                    'name': 'Evaluation Result (1: Win, 0: Tie, -1: Lose)'
                },
                'series': [{
                    'data': self.df[['length_diff', 'evaluation_result']].values.tolist(),
                    'type': 'scatter'
                }]
            },
            "interpretation": "Positive correlation indicates longer outputs tend to win, "
                              "negative correlation indicates shorter outputs tend to win."
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        return {
            "total_comparisons": len(self.df),
            "unique_contexts": self.df['context'].nunique(),
            "avg_output_1_length": self.df['output_1'].str.len().mean(),
            "avg_output_2_length": self.df['output_2'].str.len().mean(),
        }