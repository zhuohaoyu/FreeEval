document.addEventListener('DOMContentLoaded', (event) => {
    const searchForm = document.getElementById('search-form');
    const navbarSearchForm = document.getElementById('navbar-search-form');
    const filterDropdown = document.getElementById('filterDropdown');
    const filterOptions = document.getElementById('filterOptions');

    // Handle search form submission (for both main and navbar forms)
    const handleSearchFormSubmission = function(e) {
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
                document.getElementById('apply-range-filter').addEventListener('click', function() {
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
                filterOptions.addEventListener('change', function(e) {
                    if (e.target.type === 'checkbox') {
                        const checkedOptions = Array.from(filterOptions.querySelectorAll('input:checked')).map(input => input.value);
                        window.location.href = `/browse-cases?filter=${encodeURIComponent(checkedOptions.join(','))}`;
                    }
                });
            }
        });
});