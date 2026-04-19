/**
 * Live Edit — Édition en place sur le site public.
 */
(function() {
    var bar = document.getElementById('edit-bar');
    if (!bar) return;

    var editables = document.querySelectorAll('[data-edit-field]');
    var settingEditables = document.querySelectorAll('[data-edit-setting]');
    if (!editables.length && !settingEditables.length && !document.querySelector('.gallery-delete-btn')) return;

    var isOn = false;
    var originals = {};
    var modified = {};

    // Boutons
    var toggleBtn = document.createElement('a');
    toggleBtn.href = '#';
    var saveBtn = document.createElement('a');
    saveBtn.href = '#';
    saveBtn.innerHTML = '✓ Enregistrer';
    saveBtn.style.cssText = 'background:white; color:#2057b2; padding:0.3rem 0.8rem; border-radius:0.3rem; font-weight:700; display:none;';
    var cancelBtn = document.createElement('a');
    cancelBtn.href = '#';
    cancelBtn.innerHTML = '✕ Annuler';
    cancelBtn.style.cssText = 'display:none;';

    var first = bar.firstElementChild;
    bar.insertBefore(cancelBtn, first);
    bar.insertBefore(saveBtn, first);
    bar.insertBefore(toggleBtn, first);

    function activate() {
        isOn = true;
        localStorage.setItem('live-edit-mode', '1');
        toggleBtn.innerHTML = '● Mode édition ON';
        toggleBtn.style.cssText = 'background:rgba(255,255,255,0.2); padding:0.3rem 0.8rem; border-radius:0.3rem; font-weight:600;';
        cancelBtn.style.display = '';

        editables.forEach(function(el) {
            originals[el.dataset.editField] = el.innerHTML;
            el.contentEditable = true;
            el.style.outline = '2px dashed rgba(32,87,178,0.6)';
            el.style.outlineOffset = '4px';
            el.style.borderRadius = '4px';
            el.style.cursor = 'text';
            el.addEventListener('input', onInput);
        });

        settingEditables.forEach(function(el) {
            originals['setting_' + el.dataset.editSetting] = el.textContent;
            el.contentEditable = true;
            el.style.outline = '2px dashed rgba(32,87,178,0.6)';
            el.style.outlineOffset = '4px';
            el.style.borderRadius = '4px';
            el.style.cursor = 'text';
            el.addEventListener('input', onSettingInput);
        });

        // Galerie + autres modules
        if (window._liveEditToggleCallback) window._liveEditToggleCallback(true);
        window._galleryEditToggle && window._galleryEditToggle(true);
    }

    function deactivate() {
        isOn = false;
        localStorage.setItem('live-edit-mode', '0');
        toggleBtn.innerHTML = '✎ Éditer cette page';
        toggleBtn.style.cssText = 'font-weight:600;';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';

        editables.forEach(function(el) {
            el.contentEditable = false;
            el.style.outline = '';
            el.style.outlineOffset = '';
            el.style.borderRadius = '';
            el.style.cursor = '';
            el.removeEventListener('input', onInput);
        });

        settingEditables.forEach(function(el) {
            el.contentEditable = false;
            el.style.outline = '';
            el.style.outlineOffset = '';
            el.style.borderRadius = '';
            el.style.cursor = '';
            el.removeEventListener('input', onSettingInput);
        });

        modified = {};
        if (window._liveEditToggleCallback) window._liveEditToggleCallback(false);
        window._galleryEditToggle && window._galleryEditToggle(false);
    }

    var modifiedSettings = {};

    function onInput(e) {
        modified[e.target.dataset.editField] = {
            value: e.target.innerHTML,
            page: e.target.dataset.editPage,
        };
        saveBtn.style.display = '';
    }

    function onSettingInput(e) {
        modifiedSettings[e.target.dataset.editSetting] = e.target.textContent.trim();
        saveBtn.style.display = '';
    }

    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (isOn) { deactivate(); } else { activate(); }
    });

    cancelBtn.addEventListener('click', function(e) {
        e.preventDefault();
        editables.forEach(function(el) {
            if (originals[el.dataset.editField]) {
                el.innerHTML = originals[el.dataset.editField];
            }
        });
        settingEditables.forEach(function(el) {
            var key = 'setting_' + el.dataset.editSetting;
            if (originals[key]) { el.textContent = originals[key]; }
        });
        deactivate();
    });

    saveBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (!Object.keys(modified).length && !Object.keys(modifiedSettings).length) return;

        saveBtn.innerHTML = '⏳ ...';
        var csrfToken = '';
        document.cookie.split(';').forEach(function(c) {
            c = c.trim();
            if (c.startsWith('csrftoken=')) csrfToken = c.substring(10);
        });

        fetch('/gestion/live-edit/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ fields: modified, settings: modifiedSettings }),
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) {
                saveBtn.innerHTML = '✓ OK !';
                setTimeout(function() { saveBtn.style.display = 'none'; saveBtn.innerHTML = '✓ Enregistrer'; }, 1200);
                modified = {};
                modifiedSettings = {};
                editables.forEach(function(el) { originals[el.dataset.editField] = el.innerHTML; });
                settingEditables.forEach(function(el) { originals['setting_' + el.dataset.editSetting] = el.textContent; });
            } else {
                saveBtn.innerHTML = '✕ Erreur';
                setTimeout(function() { saveBtn.innerHTML = '✓ Enregistrer'; }, 2000);
            }
        })
        .catch(function() {
            saveBtn.innerHTML = '✕ Erreur';
            setTimeout(function() { saveBtn.innerHTML = '✓ Enregistrer'; }, 2000);
        });
    });

    // Restaurer le mode si actif
    if (localStorage.getItem('live-edit-mode') === '1') {
        activate();
    } else {
        toggleBtn.innerHTML = '✎ Éditer cette page';
        toggleBtn.style.cssText = 'font-weight:600;';
    }
})();
