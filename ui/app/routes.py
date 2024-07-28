from flask import Blueprint, render_template, request, current_app, jsonify, url_for
import json

main = Blueprint('main', __name__)

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
            cases = [case for case in cases if any(search_term.lower() in case[f].lower() for f in fields)]

    if filter_option:
        filter_options = filter_option.split(',')
        cases = [case for case in cases if case['evaluation_result'] in filter_options]
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