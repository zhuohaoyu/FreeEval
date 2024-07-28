from .base_evaluator import BaseEvaluator
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
from scipy import stats

class MatchingEvaluator(BaseEvaluator):
    def __init__(self, result_path: str):
        super().__init__(result_path)
        self.is_binary = self.df['match'].dtype == bool

    def get_overall_results(self) -> Dict[str, Any]:
        if self.is_binary:
            results = self.df['match'].value_counts().to_dict()
            total = sum(results.values())
            return {
                "match_rate": results.get(True, 0) / total,
                "total_evaluations": total
            }
        else:
            return {
                "mean_score": self.df['match'].mean(),
                "median_score": self.df['match'].median(),
                "min_score": self.df['match'].min(),
                "max_score": self.df['match'].max()
            }

    def get_distribution_plot(self) -> go.Figure:
        if self.is_binary:
            results = self.df['match'].value_counts().to_dict()
            fig = go.Figure(data=[go.Bar(x=list(results.keys()), y=list(results.values()))])
            fig.update_layout(title="Distribution of Match Results",
                              xaxis_title="Match",
                              yaxis_title="Count")
        else:
            fig = go.Figure(data=[go.Histogram(x=self.df['match'])])
            fig.update_layout(title="Distribution of Match Scores",
                              xaxis_title="Score",
                              yaxis_title="Frequency")
        return fig

    def get_correlation_analysis(self) -> Dict[str, Any]:
        self.df['output_length'] = self.df['output'].str.len()
        self.df['reference_length'] = self.df['reference'].str.len()
        
        if self.is_binary:
            correlation, p_value = stats.pointbiserialr(self.df['match'], self.df['output_length'])
            fig = px.box(self.df, x='match', y='output_length', 
                         title='Relationship between Output Length and Match Result')
            fig.update_layout(xaxis_title="Match Result",
                              yaxis_title="Output Length")
        else:
            correlation, p_value = stats.pearsonr(self.df['match'], self.df['output_length'])
            fig = px.scatter(self.df, x='output_length', y='match', 
                             title='Correlation between Output Length and Match Score')
            fig.update_layout(xaxis_title="Output Length",
                              yaxis_title="Match Score")
        
        return {
            "correlation": correlation,
            "p_value": p_value,
            "plot": fig,
            "interpretation": "For binary matching: Positive correlation indicates longer outputs tend to match more often. "
                              "For continuous matching: Positive correlation indicates longer outputs tend to have higher match scores."
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        return {
            "total_evaluations": len(self.df),
            "unique_references": self.df['reference'].nunique(),
            "avg_output_length": self.df['output'].str.len().mean(),
            "avg_reference_length": self.df['reference'].str.len().mean(),
            "match_type": "Binary" if self.is_binary else "Continuous"
        }

    def get_all_plots(self) -> List[go.Figure]:
        return [
            self.get_distribution_plot(),
            self.get_correlation_analysis()['plot']
        ]