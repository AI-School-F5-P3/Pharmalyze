// static/js/product-search.js
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const filterButton = document.querySelector('button[title="Filtrar por categoría"]');
    const productsTable = document.getElementById('productsTable');
    const productCards = document.querySelector('.product-cards');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            
            // For stock.html table
            if (productsTable) {
                const rows = productsTable.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
            
            // For product_list.html cards
            if (productCards) {
                const cards = productCards.querySelectorAll('.product-card');
                cards.forEach(card => {
                    const title = card.querySelector('.product-title').textContent.toLowerCase();
                    const category = card.querySelector('.product-category').textContent.toLowerCase();
                    const shouldShow = title.includes(searchTerm) || category.includes(searchTerm);
                    card.style.display = shouldShow ? '' : 'none';
                });
            }
        });
    }

    // Category filter functionality
    if (filterButton) {
        filterButton.addEventListener('click', function() {
            const categories = [...new Set(Array.from(document.querySelectorAll('td:nth-child(9)')).map(td => td.textContent))];
            
            const filterMenu = document.createElement('div');
            filterMenu.className = 'category-filter-menu';
            filterMenu.innerHTML = `
                <div class="filter-popup">
                    <h4>Filter by Category</h4>
                    ${categories.map(category => `
                        <label>
                            <input type="checkbox" value="${category}"> ${category}
                        </label>
                    `).join('')}
                    <button class="btn btn-primary btn-sm mt-2">Apply</button>
                </div>
            `;
            
            document.body.appendChild(filterMenu);
            
            filterMenu.querySelector('button').addEventListener('click', function() {
                const selectedCategories = Array.from(filterMenu.querySelectorAll('input:checked')).map(inp => inp.value);
                const rows = productsTable.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const rowCategory = row.querySelector('td:nth-child(9)').textContent;
                    row.style.display = selectedCategories.length === 0 || selectedCategories.includes(rowCategory) ? '' : 'none';
                });
                
                filterMenu.remove();
            });
        });
    }
});