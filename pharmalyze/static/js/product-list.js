// static/js/product-list.js

document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    const productCards = document.querySelectorAll('.product-card');
    const categorySections = document.querySelectorAll('.category-section');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();

            categorySections.forEach(section => {
                let hasVisibleProducts = false;
                const productsInSection = section.querySelectorAll('.product-card');

                productsInSection.forEach(card => {
                    const title = card.querySelector('.product-title').textContent.toLowerCase();
                    const category = card.querySelector('.product-category').textContent.toLowerCase();
                    const isMatch = title.includes(searchTerm) || category.includes(searchTerm);
                    
                    card.style.display = isMatch ? '' : 'none';
                    if (isMatch) hasVisibleProducts = true;
                });

                // Show/hide the entire category section
                section.style.display = hasVisibleProducts ? '' : 'none';
            });

            // Handle "No results found" message
            let allHidden = true;
            categorySections.forEach(section => {
                if (section.style.display !== 'none') allHidden = false;
            });

            let noResultsMsg = document.getElementById('no-results-message');
            if (allHidden) {
                if (!noResultsMsg) {
                    noResultsMsg = document.createElement('div');
                    noResultsMsg.id = 'no-results-message';
                    noResultsMsg.className = 'text-center py-8 text-gray-500';
                    noResultsMsg.textContent = 'No se encontraron productos que coincidan con la búsqueda.';
                    document.querySelector('.products-grid').appendChild(noResultsMsg);
                }
                noResultsMsg.style.display = '';
            } else if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
        });
    }

    // Lazy loading functionality
    const initLazyLoading = () => {
        const lazyImages = document.querySelectorAll("img.lazy-image");
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.onload = () => {
                            img.classList.add('loaded');
                        };
                        observer.unobserve(img);
                    }
                });
            }, {
                root: null,
                rootMargin: '0px',
                threshold: 0.1
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for browsers that don't support IntersectionObserver
            lazyImages.forEach(img => {
                img.src = img.dataset.src;
            });
        }
    };

    initLazyLoading();
});