from .base_evaluator import BaseEvaluator
from typing import Dict, Any
from scipy import stats

class DirectScoringEvaluator(BaseEvaluator):
    def __init__(self, result_path: str):
        super().__init__(result_path)

    def get_overall_results(self) -> Dict[str, Any]:
        counts = self.df['evaluation_result'].value_counts().to_dict()
        counts = dict(sorted(counts.items(), key=lambda x: x[0], reverse=False))
        return {
            "mean_score": self.df['evaluation_result'].mean(),
            "median_score": self.df['evaluation_result'].median(),
            "min_score": self.df['evaluation_result'].min(),
            "max_score": self.df['evaluation_result'].max(),
            "counts": counts
        }

    def get_distribution_plot(self) -> Dict[str, Any]:
        counts = self.df['evaluation_result'].value_counts().to_dict()
        return {
            'xAxis': {
                'type': 'category',
                'data': list(counts.keys())
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [{
                'data': list(counts.values()),
                'type': 'bar'
            }]
        }

    def get_correlation_analysis(self) -> Dict[str, Any]:
        self.df['output_length'] = self.df['output'].str.len()
        correlation, p_value = stats.pearsonr(self.df['output_length'], self.df['evaluation_result'])
        
        return {
            "correlation": correlation,
            "p_value": p_value,
            "plot": {
                'xAxis': {
                    'type': 'value',
                    'name': 'Output Length'
                },
                'yAxis': {
                    'type': 'value',
                    'name': 'Evaluation Score'
                },
                'series': [{
                    'data': self.df[['output_length', 'evaluation_result']].values.tolist(),
                    'type': 'scatter'
                }]
            },
            "interpretation": "Positive correlation indicates longer outputs tend to score higher, "
                              "negative correlation indicates shorter outputs tend to score lower."
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        return {
            "total_evaluations": len(self.df),
            "unique_contexts": self.df['context'].nunique(),
            "avg_output_length": self.df['output'].str.len().mean(),
            "score_std_dev": self.df['evaluation_result'].std()
        }