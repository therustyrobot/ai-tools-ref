// search.js — AI Stars Gallery v1.1 Search & Filter
// Phase 6: Live text search

(function () {
  'use strict';

  var searchInput = document.getElementById('search-input');
  if (!searchInput) return; // guard: no-op if page lacks search input

  var cards = document.querySelectorAll('[data-name]');
  var sections = document.querySelectorAll('section[data-category]');

  // No-results message element — injected once, shown/hidden as needed
  var noResultsMsg = document.createElement('p');
  noResultsMsg.id = 'search-no-results';
  noResultsMsg.textContent = 'No matches \u2014 showing all repos';
  noResultsMsg.style.cssText = [
    'display:none',
    'padding:8px 12px',
    'font-size:10px',
    'font-weight:700',
    'text-transform:uppercase',
    'opacity:0.6',
    'letter-spacing:0.05em'
  ].join(';');
  searchInput.parentNode.insertBefore(noResultsMsg, searchInput.nextSibling);

  function applyTextFilter(activeFilter) {
    var query = searchInput.value.trim().toLowerCase();

    if (!query && !activeFilter) {
      // No query, no category filter — show everything
      cards.forEach(function (card) { card.style.display = ''; });
      sections.forEach(function (section) { section.style.display = ''; });
      noResultsMsg.style.display = 'none';
      return;
    }

    // Filter cards: match name, desc, or category (case-insensitive substring)
    var matchedCategories = {};
    cards.forEach(function (card) {
      var nameMatch  = !query || card.dataset.name.toLowerCase().indexOf(query) > -1;
      var descMatch  = !query || card.dataset.desc.toLowerCase().indexOf(query) > -1;
      var catMatch   = !query || card.dataset.category.toLowerCase().indexOf(query) > -1;
      var textMatch  = nameMatch || descMatch || catMatch;
      var catFilter  = !activeFilter || card.dataset.category === activeFilter;
      var visible    = textMatch && catFilter;
      card.style.display = visible ? '' : 'none';
      if (visible) {
        matchedCategories[card.dataset.category] = true;
      }
    });

    var anyMatch = Object.keys(matchedCategories).length > 0;

    if (!anyMatch && query) {
      // Zero text matches: show everything + message (never empty page)
      cards.forEach(function (card) { card.style.display = ''; });
      sections.forEach(function (section) { section.style.display = ''; });
      noResultsMsg.style.display = '';
      return;
    }

    noResultsMsg.style.display = 'none';

    // Show/hide sections based on whether they have visible cards
    sections.forEach(function (section) {
      var cat = section.dataset.category;
      var inCatFilter = !activeFilter || cat === activeFilter;
      var hasMatch    = !query || matchedCategories[cat] === true;
      section.style.display = (inCatFilter && hasMatch) ? '' : 'none';
    });
  }

  // Expose applyTextFilter so Phase 7 category filter can call it with activeFilter state
  window._starsApplyFilters = applyTextFilter;

  searchInput.addEventListener('input', function () {
    // Pass current category filter state if Phase 7 has set it
    applyTextFilter(window._starsCategoryFilter || null);
    // Show/hide × clear button (UX-03)
    var clearBtn = document.getElementById('search-clear');
    if (clearBtn) {
      clearBtn.style.display = searchInput.value ? '' : 'none';
    }
  });

  // UX-04: '/' key focuses search input (unless already in a text field)
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/') return;
    var tag = document.activeElement && document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    e.preventDefault();
    searchInput.focus();
  });

  // Initial call with no filter
  applyTextFilter(null);
})();

// Phase 7: Category Filter
(function () {
  'use strict';

  var filterBtns = document.querySelectorAll('[data-filter]');
  if (!filterBtns.length) return;

  // Shared state: read by Phase 6 applyTextFilter via window._starsCategoryFilter
  window._starsCategoryFilter = null;

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var slug = btn.dataset.filter;

      if (window._starsCategoryFilter === slug) {
        // Toggle off — restore all categories
        window._starsCategoryFilter = null;
        filterBtns.forEach(function (b) { b.classList.remove('is-active'); });
        if (typeof window._starsOnFilterClear === 'function') {
          window._starsOnFilterClear();
        }
      } else {
        // Activate this category
        filterBtns.forEach(function (b) { b.classList.remove('is-active'); });
        window._starsCategoryFilter = slug;
        btn.classList.add('is-active');
      }

      // Re-run filters with updated category state
      // window._starsApplyFilters is exposed by Phase 6 IIFE
      if (typeof window._starsApplyFilters === 'function') {
        window._starsApplyFilters(window._starsCategoryFilter);
      }
      // Do NOT call e.preventDefault() — browser anchor scroll still executes (UX-05)
    });
  });
})();

// Phase 8: Scroll-aware active section tracking via IntersectionObserver
(function () {
  'use strict';

  if (!('IntersectionObserver' in window)) return; // graceful degradation

  var filterBtns = document.querySelectorAll('[data-filter]');
  var sections = document.querySelectorAll('section[data-category]');
  if (!filterBtns.length || !sections.length) return;

  var currentSlug = null;

  function setScrollActive(slug) {
    if (currentSlug === slug) return;
    currentSlug = slug;
    filterBtns.forEach(function (btn) {
      btn.classList.toggle('is-active', btn.dataset.filter === slug);
    });
  }

  var observer = new IntersectionObserver(function (entries) {
    if (window._starsCategoryFilter) return; // click-filter takes precedence
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        setScrollActive(entry.target.dataset.category);
      }
    });
  }, {
    rootMargin: '-10% 0px -80% 0px',
    threshold: 0
  });

  sections.forEach(function (section) { observer.observe(section); });

  // Called by Phase 7 when click-filter is toggled off, to re-sync with scroll position
  window._starsOnFilterClear = function () {
    currentSlug = null;
    var topSection = null;
    sections.forEach(function (section) {
      if (topSection || section.style.display === 'none') return;
      if (section.getBoundingClientRect().bottom > 100) { topSection = section; }
    });
    if (topSection) { setScrollActive(topSection.dataset.category); }
  };
})();
