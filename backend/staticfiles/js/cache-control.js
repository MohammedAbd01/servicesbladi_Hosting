/**
 * cache-control.js - Une solution 100% efficace pour les problèmes de cache
 * 
 * Ce script doit être inclus en premier dans toutes les pages pour s'assurer
 * que les utilisateurs voient toujours la dernière version.
 */

(function() {
    // Fonction pour obtenir un paramètre de l'URL
    function getUrlParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    }

    // Fonction pour forcer le rechargement
    function forceRefresh() {
        const timestamp = new Date().getTime();
        if (!window.location.href.includes('t=') && !window.location.href.includes('no_refresh')) {
            window.location.href = window.location.href + 
                (window.location.href.includes('?') ? '&' : '?') + 
                't=' + timestamp;
            return true;
        }
        return false;
    }
    
    // Vérification si l'URL contient déjà un paramètre de temps
    const timeParam = getUrlParam('t');
    const forceParam = getUrlParam('force');
    
    // Si force=1 est dans l'URL, forcer un rechargement complet
    if (forceParam === '1') {
        window.location.reload(true);
    }
    
    // Si aucun paramètre de temps n'est présent, ou s'il est ancien (plus de 5 minutes)
    if (!timeParam || ((new Date().getTime() - parseInt(timeParam)) > 300000)) {
        // Forcer l'actualisation avec un nouveau paramètre de temps
        if (!forceRefresh()) {
            // Si pas de redirection, vérifier le cache
            if (window.performance && window.performance.navigation) {
                // Si chargé depuis le cache (type 1 = rechargement, type 2 = retour/avant)
                if (window.performance.navigation.type === 0) {
                    // Vérifier le temps de chargement
                    window.addEventListener('load', function() {
                        const loadTime = window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart;
                        // Si le chargement a été trop rapide (probablement depuis le cache)
                        if (loadTime < 100) {
                            window.location.reload(true);
                        }
                    });
                }
            }
        }
    }
    
    // Ajouter un gestionnaire d'événements pour recharger en cas d'erreurs WebSocket
    document.addEventListener('DOMContentLoaded', function() {
        // Observer d'erreurs WebSocket
        var wsErrors = 0;
        // Intercepter les erreurs websocket
        window.addEventListener('error', function(e) {
            if (e && e.message && (
                e.message.includes('WebSocket') || 
                e.message.includes('ws://') || 
                e.message.includes('wss://')
            )) {
                wsErrors++;
                // Si plusieurs erreurs WebSocket, recharger la page
                if (wsErrors > 2) {
                    console.error('Erreurs WebSocket détectées. Rechargement...');
                    localStorage.setItem('wsErrors', Date.now().toString());
                    window.location.reload(true);
                }
            }
        });
        
        // Vérifier si nous avons eu des erreurs WebSocket récemment
        const lastWsError = localStorage.getItem('wsErrors');
        if (lastWsError && (Date.now() - parseInt(lastWsError)) < 60000) {
            // Erreurs récentes, forcer un rechargement de la page
            localStorage.removeItem('wsErrors'); // Supprimez pour éviter une boucle
            window.location.href = window.location.href + 
                (window.location.href.includes('?') ? '&' : '?') + 
                'force=1&t=' + Date.now();
        }
    });
})(); 