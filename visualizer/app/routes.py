from flask import Blueprint, render_template, request, current_app, jsonify, url_for, redirect, send_file
import json
import os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

@main.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_file(os.path.join(root_dir, 'static', filename), 
                     max_age=2592000)  # Cache for 30 days


def iterative_reformatting(data):
    if not data:
        return {}
    for item in data:
        if isinstance(data[item], str):
            data[item] = data[item].replace('\n', '<br>')
        else:
            if isinstance(data[item], dict):
                data[item] = json.dumps(data[item], indent=2, ensure_ascii=False)
            else:
                try:
                    data[item] = str(data[item])
                except:
                    data[item] = 'Error: Could not convert to string'
            data[item] = data[item].replace('\n', '<br>')
    return data

@main.route('/')
def dashboard():
    evaluator = current_app.config['EVALUATOR']
    overall_results = evaluator.get_overall_results()
    metadata = iterative_reformatting(evaluator.metadata)
    overview = iterative_reformatting(evaluator.overview)

    print(overall_results)

    chart_data = {
        'xAxis': {
            'type': 'category',
            'data': list(overall_results['counts'].keys())
        },
        'yAxis': {
            'type': 'value'
        },
        'series': [{
            'data': list(overall_results['counts'].values()),
            'type': 'bar'
        }]
    }
    
    return render_template('dashboard.html', chart_data=chart_data, metadata=metadata, overview=overview)

@main.route('/case-study')
def case_study():
    evaluator = current_app.config['EVALUATOR']
    uuid = request.args.get('uuid')
    
    if uuid:
        try:
            case_data = evaluator.get_case_study(uuid)
            case_data = {k: v.replace('\n', '<br>') if isinstance(v, str) else v for k, v in case_data.items()}
            return render_template('case_study.html', case_data=case_data)
        except ValueError as e:
            return str(e), 404
    else:
        return "Please provide a UUID", 400

@main.route('/get-cases')
def get_cases():
    evaluator = current_app.config['EVALUATOR']
    if 'context' in evaluator.df.columns:
        cases = evaluator.df[['uuid', 'context']].to_dict('records')
    elif 'input' in evaluator.df.columns:
        cases = evaluator.df[['uuid', 'input']].to_dict('records')
    else:
        cases = evaluator.df[['uuid']].to_dict('records')
    return jsonify(cases)

@main.route('/analysis')
def analysis():
    evaluator = current_app.config['EVALUATOR']
    charts = evaluator.prepare_figure_data()
    return render_template('analysis.html', charts=charts)

@main.route('/browse-cases')
def browse_cases():
    evaluator = current_app.config['EVALUATOR']
    page = int(request.args.get('page', 1))
    per_page = 10
    search_term = request.args.get('search', '')
    filter_option = request.args.get('filter', '')
    lower_bound = request.args.get('lower_bound', None, type=float)
    upper_bound = request.args.get('upper_bound', None, type=float)

    cases = evaluator.get_all_cases()
    
    if search_term:
        fields = [f for f in['context', 'input', 'output', 'uuid'] if f in cases[0]]
        if fields:
            cases = [case for case in cases if any(search_term.lower() in str(case.get(f, '')).lower() for f in fields)]

    if filter_option:
        filter_options = filter_option.split(',')
        cases = [case for case in cases if str(case['evaluation_result']) in filter_options]
    elif lower_bound is not None and upper_bound is not None:
        cases = [case for case in cases if lower_bound <= case['evaluation_result'] <= upper_bound]

    total_cases = len(cases)
    paginated_cases = cases[(page - 1) * per_page: page * per_page]
    
    next_url = url_for('main.browse_cases', page=page + 1, search=search_term, filter=filter_option, lower_bound=lower_bound, upper_bound=upper_bound) if page * per_page < total_cases else None
    prev_url = url_for('main.browse_cases', page=page - 1, search=search_term, filter=filter_option, lower_bound=lower_bound, upper_bound=upper_bound) if page > 1 else None
    
    start_index = (page - 1) * per_page + 1
    end_index = min(page * per_page, total_cases)

    return render_template('browse_cases.html', 
                           cases=paginated_cases, 
                           total_cases=total_cases, 
                           next_url=next_url, 
                           prev_url=prev_url, 
                           page=page, 
                           per_page=per_page,
                           start_index=start_index,
                           end_index=end_index,
                           search_term=search_term,
                           filter_option=filter_option,
                           lower_bound=lower_bound,
                           upper_bound=upper_bound)

@main.route('/get-filter-options')
def get_filter_options():
    evaluator = current_app.config['EVALUATOR']
    result_type = evaluator.get_evaluation_result_type()
    
    if result_type == 'numeric':
        min_value, max_value = evaluator.get_evaluation_result_range()
        return jsonify({'type': 'numeric', 'min': float(min_value), 'max': float(max_value)})
    elif result_type == 'categorical':
        options = evaluator.get_evaluation_result_options()
        return jsonify({'type': 'categorical', 'options': options})

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/check-session', methods=['POST'])
def check_session():
    session_name = request.json['session_name']
    session_folder = os.path.join(current_app.root_path, 'human_evaluation_sessions', session_name)
    settings_file = os.path.join(session_folder, 'annotation_settings.json')
    
    if os.path.exists(settings_file):
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@main.route('/human-evaluation', methods=['GET', 'POST'])
def human_evaluation():
    if request.method == 'POST':
        session_name = secure_filename(request.form['session_name'])
        os.makedirs(os.path.join(current_app.root_path, 'human_evaluation_sessions'), exist_ok=True)

        session_folder = os.path.join(current_app.root_path, 'human_evaluation_sessions', session_name)
        settings_file = os.path.join(session_folder, 'annotation_settings.json')
        
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)
        
        if not os.path.exists(settings_file):
            settings = {
                'evaluation_type': request.form['evaluation_type'],
                'hide_scores': 'hide_scores' in request.form
            }
            
            if settings['evaluation_type'] == 'pairwise':
                settings['options'] = request.form.getlist('pairwise_options')
                settings['random_swap'] = 'random_swap' in request.form
            elif settings['evaluation_type'] == 'scoring':
                settings['scoring_type'] = request.form['scoring_type']
                if settings['scoring_type'] == 'discrete':
                    settings['allowed_scores'] = request.form['allowed_scores'].split(',')
                else:
                    settings['min_score'] = int(request.form['min_score'])
                    settings['max_score'] = int(request.form['max_score'])
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
        
        return redirect(url_for('main.annotation_session', session_name=session_name))
    
    return render_template('human_evaluation.html')

@main.route('/annotation-session/<session_name>')
def annotation_session(session_name):
    session_folder = os.path.join(current_app.root_path, 'human_evaluation_sessions', session_name)
    settings_file = os.path.join(session_folder, 'annotation_settings.json')
    
    if not os.path.exists(settings_file):
        return "Session not found", 404

    with open(settings_file, 'r') as f:
        settings = json.load(f)
    
    evaluator = current_app.config['EVALUATOR']
    cases = evaluator.get_all_cases()
    
    # Get the list of annotated UUIDs
    annotated_uuids = set()
    for filename in os.listdir(session_folder):
        if filename.endswith('.json') and filename != 'annotation_settings.json':
            annotated_uuids.add(filename[:-5])  # Remove '.json' from the filename
    
    return render_template('annotation_session.html', 
                           session_name=session_name, 
                           settings=settings, 
                           cases=cases, 
                           annotated_uuids=annotated_uuids)

import random

@main.route('/case-annotation/<session_name>/<uuid>')
def case_annotation(session_name, uuid):
    session_folder = os.path.join(current_app.root_path, 'human_evaluation_sessions', session_name)
    with open(os.path.join(session_folder, 'annotation_settings.json'), 'r') as f:
        settings = json.load(f)
    
    evaluator = current_app.config['EVALUATOR']
    all_cases = evaluator.get_all_cases()
    
    # Find the current case and the next case
    current_case_index = next((i for i, case in enumerate(all_cases) if case['uuid'] == uuid), None)
    if current_case_index is None:
        return "Case not found", 404
    
    next_case_index = (current_case_index + 1) % len(all_cases)
    next_uuid = all_cases[next_case_index]['uuid']
    
    case_data = evaluator.get_case_study(uuid)
    
    if settings.get('hide_scores'):
        case_data.pop('evaluation_result', None)
        case_data.pop('evaluator_output', None)
    
    # Handle swapping for pairwise comparison
    is_swapped = False
    if settings['evaluation_type'] == 'pairwise' and settings.get('random_swap'):
        is_swapped = random.choice([True, False])
        if is_swapped:
            case_data['output_1'], case_data['output_2'] = case_data['output_2'], case_data['output_1']
    
    annotation_file = os.path.join(session_folder, f'{uuid}.json')
    if os.path.exists(annotation_file):
        with open(annotation_file, 'r') as f:
            annotation = json.load(f)
    else:
        annotation = None
    
    return render_template('case_annotation.html', 
                           session_name=session_name, 
                           settings=settings, 
                           case_data=case_data, 
                           annotation=annotation,
                           next_uuid=next_uuid,
                           is_swapped=is_swapped)


@main.route('/save-annotation/<session_name>/<uuid>', methods=['POST'])
def save_annotation(session_name, uuid):
    session_folder = os.path.join(current_app.root_path, 'human_evaluation_sessions', session_name)
    annotation_file = os.path.join(session_folder, f'{uuid}.json')
    
    annotation = request.json
    
    with open(annotation_file, 'w') as f:
        json.dump(annotation, f)
    
    return jsonify(success=True)