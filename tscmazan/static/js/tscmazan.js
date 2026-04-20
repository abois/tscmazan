(function () {
    // Easter egg — titre de l'onglet qui change quand on quitte la page
    var originalTitle = document.title;
    var awayMessages = [
        "Reviens sur le court !",
        "Tu abandonnes au tie-break ?",
        "Le set n'est pas fini…",
        "Balle de match — reviens !",
        "On t'attend au filet.",
    ];
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            var msg = awayMessages[Math.floor(Math.random() * awayMessages.length)];
            document.title = msg;
        } else {
            document.title = originalTitle;
        }
    });
})();
