import click
from flask import Flask
from app import create_app

@click.command()
@click.option('--mode', type=click.Choice(['pairwise-comparison', 'direct-scoring', 'matching']), required=True, help='Evaluation mode')
@click.option('--result-path', type=click.Path(exists=True), required=True, help='Path to the results JSON file')
@click.option('--port', default=5000, help='Port to run the server on')
@click.option('--addr', default='127.0.0.1', help='Address to run the server on')
def run_app(mode, result_path, port, addr):
    app = create_app(mode, result_path)
    app.run(host=addr, port=port, debug=True)

if __name__ == '__main__':
    run_app()