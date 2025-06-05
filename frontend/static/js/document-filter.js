// Fonctionnalité de filtrage des documents
function setupDocumentFiltering() {
  const typeFilter = document.getElementById('type-filter');
  const searchInput = document.getElementById('search-input');
  const filterBtn = document.getElementById('filter-btn');
  const resetBtn = document.querySelector('a[href="?"]');
  const documentItems = document.querySelectorAll('.document-item');
  
  // Fonction pour mettre à jour l'URL avec les paramètres de filtre
  function updateUrl() {
    const params = new URLSearchParams();
    
    if (typeFilter && typeFilter.value) params.set('type', typeFilter.value);
    if (searchInput && searchInput.value) params.set('search', searchInput.value);
    
    // Mettre à jour l'URL sans recharger la page
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);
  }
  
  // Appliquer les filtres
  function applyFilters() {
    const type = typeFilter ? typeFilter.value.toLowerCase() : '';
    const search = searchInput ? searchInput.value.toLowerCase() : '';
    let hasVisibleItems = false;
    
    documentItems.forEach(function(item) {
      const itemType = item.dataset.type || '';
      const itemContent = item.textContent.toLowerCase();
      
      const typeMatch = !type || itemType === type;
      const searchMatch = !search || itemContent.includes(search);
      
      if (typeMatch && searchMatch) {
        item.style.display = 'block';
        hasVisibleItems = true;
      } else {
        item.style.display = 'none';
      }
    });
    
    // Afficher un message si aucun résultat
    const noResultsMessage = `
      <div class="alert alert-info no-results">
        <div class="d-flex align-items-center">
          <i class="bi bi-info-circle-fill me-2 fs-4"></i>
          <div>
            <h5 class="mb-1">Aucun document trouvé</h5>
            <p class="mb-0">Aucun document ne correspond à vos critères de recherche.</p>
          </div>
        </div>
      </div>
    `;
    
    const container = document.getElementById('documents-container');
    if (!container) return;
    
    const existingMessage = container.querySelector('.alert.alert-info.no-results');
    
    if (!hasVisibleItems) {
      if (!existingMessage) {
        const temp = document.createElement('div');
        temp.innerHTML = noResultsMessage;
        container.appendChild(temp.firstElementChild);
      }
    } else if (existingMessage) {
      existingMessage.remove();
    }
    
    // Mettre à jour l'URL
    updateUrl();
  }
  
  // Réinitialiser les filtres
  function resetFilters() {
    if (typeFilter) typeFilter.value = '';
    if (searchInput) searchInput.value = '';
    
    documentItems.forEach(function(item) {
      item.style.display = 'block';
    });
    
    // Supprimer le message d'absence de résultats
    const noResultsMessage = document.querySelector('.alert.alert-info.no-results');
    if (noResultsMessage) {
      noResultsMessage.remove();
    }
    
    updateUrl();
  }
  
  // Écouter les clics sur le bouton de filtre
  if (filterBtn) {
    filterBtn.addEventListener('click', applyFilters);
  }
  
  // Écouter la touche Entrée dans le champ de recherche
  if (searchInput) {
    searchInput.addEventListener('keyup', function(e) {
      if (e.key === 'Enter') {
        applyFilters();
      }
    });
  }
  
  // Écouter le clic sur le bouton de réinitialisation
  if (resetBtn) {
    resetBtn.addEventListener('click', function(e) {
      e.preventDefault();
      resetFilters();
    });
  }
  
  // Appliquer les filtres au chargement de la page si des paramètres sont présents
  if (window.location.search) {
    const params = new URLSearchParams(window.location.search);
    
    if (typeFilter && params.has('type')) {
      typeFilter.value = params.get('type');
    }
    
    if (searchInput && params.has('search')) {
      searchInput.value = params.get('search');
    }
    
    if (params.has('type') || params.has('search')) {
      applyFilters();
    }
  }
  
  // Initialiser les tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// Gérer la suppression des documents
function setupDocumentDeletion() {
  document.addEventListener('click', function(e) {
    // Vérifier si le clic est sur un bouton de suppression
    const deleteBtn = e.target.closest('.delete-document');
    if (deleteBtn) {
      e.preventDefault();
      
      // Demander confirmation avant de supprimer
      if (confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
        const url = deleteBtn.dataset.url;
        if (url) {
          window.location.href = url;
        }
      }
    }
  });
}

// Attendre que le DOM soit complètement chargé
document.addEventListener('DOMContentLoaded', function() {
  setupDocumentFiltering();
  setupDocumentDeletion();
});
