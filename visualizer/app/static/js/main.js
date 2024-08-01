document.addEventListener('DOMContentLoaded', (event) => {
    const searchForm = document.getElementById('search-form');
    const navbarSearchForm = document.getElementById('navbar-search-form');
    const filterDropdown = document.getElementById('filterDropdown');
    const filterOptions = document.getElementById('filterOptions');

    // Handle search form submission (for both main and navbar forms)
    const handleSearchFormSubmission = function (e) {
        e.preventDefault();
        const searchTerm = e.target.querySelector('input[type="text"]').value;
        window.location.href = `/browse-cases?search=${encodeURIComponent(searchTerm)}`;
    };

    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchFormSubmission);
    }

    if (navbarSearchForm) {
        navbarSearchForm.addEventListener('submit', handleSearchFormSubmission);
    }

    // Fetch and populate filter options
    if (filterOptions) {
        fetch('/get-filter-options')
            .then(response => response.json())
            .then(data => {
                if (data.type === 'numeric') {
                    const min = data.min;
                    const max = data.max;
                    filterOptions.innerHTML = `
                        <label for="lower-bound" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Lower Bound</label>
                        <input type="number" id="lower-bound" name="lower-bound" min="${min}" max="${max}" value="${min}" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">
                        <label for="upper-bound" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Upper Bound</label>
                        <input type="number" id="upper-bound" name="upper-bound" min="${min}" max="${max}" value="${max}" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">
                        <button id="apply-range-filter" class="mt-2 w-full text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800 rounded-lg p-2.5">Apply</button>
                    `;
                    document.getElementById('apply-range-filter').addEventListener('click', function () {
                        const lowerBound = document.getElementById('lower-bound').value;
                        const upperBound = document.getElementById('upper-bound').value;
                        window.location.href = `/browse-cases?lower_bound=${lowerBound}&upper_bound=${upperBound}`;
                    });
                } else if (data.type === 'categorical') {
                    data.options.forEach(option => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <div class="flex items-center">
                                <input id="filter-${option}" type="checkbox" value="${option}" class="w-4 h-4 bg-gray-100 border-gray-300 rounded text-primary-600 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-700 focus:ring-2 dark:bg-gray-600 dark:border-gray-500">
                                <label for="filter-${option}" class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-100">${option}</label>
                            </div>
                        `;
                        filterOptions.appendChild(li);
                    });
                    filterOptions.addEventListener('change', function (e) {
                        if (e.target.type === 'checkbox') {
                            const checkedOptions = Array.from(filterOptions.querySelectorAll('input:checked')).map(input => input.value);
                            window.location.href = `/browse-cases?filter=${encodeURIComponent(checkedOptions.join(','))}`;
                        }
                    });
                }
            })
            .catch(error => console.error('Error fetching filter options:', error));
    }

    // Human Evaluation Session Creation
    const sessionNameForm = document.querySelector('#session-name-form');
    const settingsForm = document.querySelector('#settings-form');
    const createLoadButtonContainer = document.querySelector('#create-load-button-container');

    if (sessionNameForm) {
        sessionNameForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const sessionName = document.querySelector('#session_name').value;
            
            fetch('/check-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_name: sessionName }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    window.location.href = `/annotation-session/${sessionName}`;
                } else {
                    // Hide the "Create or Load Session" button
                    createLoadButtonContainer.classList.add('hidden');

                    // Show settings form
                    settingsForm.innerHTML = `
                            <form id="human-evaluation-form" method="POST" action="/human-evaluation" class="space-y-8">
                                <input type="hidden" name="session_name" value="${sessionName}">
                                <div>
                                    <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-gray-300">Evaluation Type</label>
                                    <div class="flex items-center mb-4">
                                        <input type="radio" id="pairwise" name="evaluation_type" value="pairwise" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600" required>
                                        <label for="pairwise" class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Pairwise Comparison</label>
                                    </div>
                                    <div class="flex items-center">
                                        <input type="radio" id="scoring" name="evaluation_type" value="scoring" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600" required>
                                        <label for="scoring" class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Scoring</label>
                                    </div>
                                </div>
                                <div id="pairwise_options" class="hidden space-y-4">
                                    <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-gray-300">Allowed Choices</label>
                                    <div class="space-y-2">
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Response 1 is better" class="sr-only peer" checked>
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Response 1 is better</span>
                                        </label>
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Response 2 is better" class="sr-only peer" checked>
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Response 2 is better</span>
                                        </label>
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Tie" class="sr-only peer">
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Tie</span>
                                        </label>
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Both Good" class="sr-only peer">
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Both Good</span>
                                        </label>
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Both Bad" class="sr-only peer">
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Both Bad</span>
                                        </label>
                                        <label class="inline-flex items-center cursor-pointer">
                                            <input type="checkbox" name="pairwise_options" value="Not Sure" class="sr-only peer">
                                            <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                            <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Not Sure</span>
                                        </label>
                                    </div>
                                    <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-gray-300">Debias</label>
                                    <label class="inline-flex items-center cursor-pointer">
                                        <input type="checkbox" name="random_swap" class="sr-only peer">
                                        <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                        <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Randomly swap order of responses</span>
                                    </label>
                                </div>
                                <div id="scoring_options" class="hidden space-y-4">
                                    <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-gray-300">Scoring Type</label>
                                    <div class="flex items-center mb-4">
                                        <input type="radio" id="discrete" name="scoring_type" value="discrete" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                                    <label for="discrete" class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Discrete Scores</label>
                                </div>
                                <div class="flex items-center">
                                    <input type="radio" id="continuous" name="scoring_type" value="continuous" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                                    <label for="continuous" class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Continuous Range</label>
                                </div>
                                <div id="discrete_scores" class="hidden">
                                    <div class="relative z-0 w-full mb-5 group">
                                        <input type="text" name="allowed_scores" id="allowed_scores" class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder=" " />
                                        <label for="allowed_scores" class="peer-focus:font-medium absolute text-sm text-gray-500 dark:text-gray-400 duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">Allowed Scores (comma-separated, e.g.: 1,2,3)</label>
                                    </div>
                                </div>
                                <div id="continuous_range" class="hidden space-y-4">
                                    <div class="relative z-0 w-full mb-5 group">
                                        <input type="number" name="min_score" id="min_score" class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder=" " />
                                        <label for="min_score" class="peer-focus:font-medium absolute text-sm text-gray-500 dark:text-gray-400 duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">Minimum Score</label>
                                    </div>
                                    <div class="relative z-0 w-full mb-5 group">
                                        <input type="number" name="max_score" id="max_score" class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder=" " />
                                        <label for="max_score" class="peer-focus:font-medium absolute text-sm text-gray-500 dark:text-gray-400 duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">Maximum Score</label>
                                    </div>
                                </div>
                            </div>
                            <label class="inline-flex items-center cursor-pointer">
                                <input type="checkbox" name="hide_scores" class="sr-only peer" checked>
                                <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:w-5 after:h-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">Hide evaluation results</span>
                            </label>
                            <div class="flex justify-center">
                                <button type="submit" class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium rounded-full text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Create Annotation Session</button>
                            </div>
                        </form>
                    `;
                        settingsForm.classList.remove('hidden');

                        // Add event listener for the new form
                        const humanEvaluationForm = document.querySelector('#human-evaluation-form');
                        if (humanEvaluationForm) {
                            humanEvaluationForm.addEventListener('submit', function (e) {
                                e.preventDefault();
                                const formData = new FormData(this);
                                fetch('/human-evaluation', {
                                    method: 'POST',
                                    body: formData
                                })
                                .then(response => {
                                    if (response.redirected) {
                                        window.location.href = response.url;
                                    }
                                })
                                .catch(error => {
                                    console.error('Error:', error);
                                });
                            });
                        }

                        // Trigger the event listeners setup in the HTML
                        const event = new Event('DOMContentLoaded');
                        document.dispatchEvent(event);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    }

    // Annotation Saving
    const annotationControls = document.getElementById('annotation-controls');
    if (annotationControls) {
        const sessionName = annotationControls.dataset.sessionName;
        const uuid = annotationControls.dataset.caseUuid;
        const isSwapped = annotationControls.dataset.isSwapped === 'True';

        const saveAnnotation = (annotation, button) => {
            // If responses were swapped and the annotation is about which response is better, reverse it
            if (isSwapped) {
                if (annotation === 'Response 1 is better') {
                    annotation = 'Response 2 is better';
                } else if (annotation === 'Response 2 is better') {
                    annotation = 'Response 1 is better';
                }
            }

            fetch(`/save-annotation/${sessionName}/${uuid}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ annotation: annotation }),
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Change button color to green
                        button.classList.remove('bg-blue-700', 'hover:bg-blue-800', 'dark:bg-blue-600', 'dark:hover:bg-blue-700');
                        button.classList.add('bg-green-500', 'hover:bg-green-600', 'dark:bg-green-600', 'dark:hover:bg-green-700');

                        // Reset other buttons
                        const allButtons = annotationControls.querySelectorAll('.annotation-option, #submit-score');
                        allButtons.forEach(btn => {
                            if (btn !== button) {
                                btn.classList.remove('bg-green-500', 'hover:bg-green-600', 'dark:bg-green-600', 'dark:hover:bg-green-700');
                                btn.classList.add('bg-blue-700', 'hover:bg-blue-800', 'dark:bg-blue-600', 'dark:hover:bg-blue-700');
                            }
                        });
                    } else {
                        console.error('Error saving annotation');
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        };

        const annotationOptions = annotationControls.querySelectorAll('.annotation-option');
        annotationOptions.forEach(option => {
            option.addEventListener('click', function () {
                saveAnnotation(this.dataset.option || this.textContent, this);
            });
        });

        const submitScore = document.getElementById('submit-score');
        if (submitScore) {
            submitScore.addEventListener('click', function () {
                const scoreInput = document.getElementById('score-input');
                if (scoreInput) {
                    saveAnnotation(scoreInput.value, this);
                }
            });
        }
    }
});