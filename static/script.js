// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    console.log('script.js: DOMContentLoaded');

    fetch('/api/loans')
        .then(response => {
            console.log('script.js: fetch response', response);
            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(loans => {
            console.log('script.js: loans data', loans);
            renderTable(loans);
        })
        .catch(err => {
            console.error('script.js error:', err);
            showError(err.message);
        });
});

/**
 * Populate the #loans-table tbody with loan rows,
 * or a single “no data” message if the array is empty.
 */
function renderTable(loans) {
    const tbody = document.querySelector('#loans-table tbody');
    tbody.innerHTML = '';  // clear existing rows

    if (!Array.isArray(loans) || loans.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 7;  // number of columns in your table
        cell.textContent = 'No loans found for this client.';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
    }

    const columnOrder = [
        "lender",
        "borrower",
        "original_date",
        "currency",
        "principal",
        "interest_rate",
        "maturity_date"
    ];

    loans.forEach(loan => {
        const row = document.createElement('tr');
        columnOrder.forEach(col => {
            const cell = document.createElement('td');
            cell.textContent = loan[col] || "";  // fallback if key is missing
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
}

/** Show an error message in the table if something breaks */
function showError(message) {
    const tbody = document.querySelector('#loans-table tbody');
    tbody.innerHTML = '';
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 7;
    cell.textContent = `Error loading loans: ${message}`;
    row.appendChild(cell);
    tbody.appendChild(row);
}
