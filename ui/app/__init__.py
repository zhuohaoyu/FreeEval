from flask import Flask
from .evaluators import PairwiseEvaluator, DirectScoringEvaluator, MatchingEvaluator

def create_app(mode, result_path):
    app = Flask(__name__)
    
    if mode == 'pairwise-comparison':
        evaluator = PairwiseEvaluator(result_path)
    elif mode == 'direct-scoring':
        evaluator = DirectScoringEvaluator(result_path)
    elif mode == 'matching':
        evaluator = MatchingEvaluator(result_path)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    app.config['EVALUATOR'] = evaluator
    
    from .routes import main
    app.register_blueprint(main)
    
    return app