
(() => {
  const search = document.querySelector('#search');
  const statusFilter = document.querySelector('#status-filter');
  const categoryFilter = document.querySelector('#category-filter');
  const cards = Array.from(document.querySelectorAll('[data-name]'));
  const visibleCount = document.querySelector('[data-visible-count]');

  const normalize = (text) => text.toLowerCase();

  function matches(card) {
    const keyword = normalize(search.value.trim());
    const statusValue = statusFilter.value;
    const categoryValue = categoryFilter.value;
    const haystack = [
      card.dataset.name,
      card.dataset.address,
      card.dataset.category,
      card.dataset.features,
    ].join(' ').toLowerCase();

    const keywordMatch = !keyword || haystack.includes(keyword);
    const statusMatch = !statusValue || card.dataset.status === statusValue;
    const categoryMatch = !categoryValue || card.dataset.category === categoryValue;

    return keywordMatch && statusMatch && categoryMatch;
  }

  function applyFilters() {
    let count = 0;
    cards.forEach((card) => {
      if (matches(card)) {
        card.style.display = '';
        count += 1;
      } else {
        card.style.display = 'none';
      }
    });

    if (visibleCount) {
      visibleCount.textContent = count;
    }
  }

  if (search) search.addEventListener('input', applyFilters);
  if (statusFilter) statusFilter.addEventListener('change', applyFilters);
  if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);

  applyFilters();
})();
