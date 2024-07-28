from abc import ABC, abstractmethod
import json
from typing import Dict, List, Any
import pandas as pd

class BaseEvaluator(ABC):
    def __init__(self, result_path: str):
        self.result_path = result_path
        self.overview, self.metadata, self.results = self.load_results()
        self.df = pd.DataFrame(self.results)
        
        if 'uuid' in self.df.columns:
            self.df['uuid'] = self.df['uuid'].astype(str)

    def load_results(self) -> List[Dict[str, Any]]:
        with open(self.result_path, 'r') as f:
            j = json.load(f)
        if isinstance(j, list):
            return None, None, j
        else:
            return j.get('overview', {}), j.get('metadata', {}), j.get('results', [])

    @abstractmethod
    def get_overall_results(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_distribution_plot(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_correlation_analysis(self) -> Dict[str, Any]:
        pass

    def get_case_study(self, uuid: str) -> Dict[str, Any]:
        return self.df[self.df['uuid'] == uuid].to_dict('records')[0]

    @abstractmethod
    def get_summary_stats(self) -> Dict[str, Any]:
        pass

    def prepare_figure_data(self):
        charts = []
        
        # Distribution plot
        distribution_data = self.get_distribution_plot()
        charts.append({
            'id': 'distribution_chart',
            'title': 'Distribution of Evaluation Results',
            'options': distribution_data
        })
        
        # Correlation analysis
        correlation_data = self.get_correlation_analysis()
        charts.append({
            'id': 'correlation_chart',
            'title': 'Correlation Analysis',
            'options': correlation_data['plot']
        })
        
        return charts
    
    def get_all_cases(self):
        return self.df[['uuid', 'context', 'evaluation_result']].to_dict('records')

    def get_evaluation_result_type(self):
        if pd.api.types.is_numeric_dtype(self.df['evaluation_result']):
            return 'numeric'
        elif pd.api.types.is_string_dtype(self.df['evaluation_result']):
            return 'categorical'
        else:
            raise ValueError("Unsupported evaluation result type")

    def get_evaluation_result_range(self):
        if self.get_evaluation_result_type() == 'numeric':
            return self.df['evaluation_result'].min(), self.df['evaluation_result'].max()
        else:
            raise ValueError("Evaluation result is not numeric")

    def get_evaluation_result_options(self):
        if self.get_evaluation_result_type() == 'categorical':
            return self.df['evaluation_result'].unique().tolist()
        else:
            raise ValueError("Evaluation result is not categorical")