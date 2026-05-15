/**
 * Live Edit — Édition en place sur le site public.
 */
(function() {
    var bar = document.getElementById('edit-bar');
    if (!bar) return;

    var editables = document.querySelectorAll('[data-edit-field]');
    var settingEditables = document.querySelectorAll('[data-edit-setting]');
    var imageEditables = document.querySelectorAll('[data-edit-image]');
    if (!editables.length && !settingEditables.length && !imageEditables.length && !document.querySelector('.gallery-delete-btn')) return;

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

        imageEditables.forEach(function(el) {
            // Si l'image cible est cachée (pas de photo encore) on rend le placeholder cliquable à sa place
            var target = el;
            if (el.hidden && el.parentElement) {
                var placeholder = el.parentElement.querySelector('[data-edit-image-placeholder]');
                if (placeholder) {
                    target = placeholder;
                    // L'upload s'enverra sur les data-attrs de l'img originale
                    target._editImageRef = el;
                }
            }

            // Sauvegarde pour restaurer ensuite
            target.dataset.editPrevOutline = target.style.outline || '';
            target.dataset.editPrevOpacity = target.style.opacity || '';
            target.dataset.editPrevMixBlend = target.style.mixBlendMode || '';
            target.dataset.editPrevZIndex = target.style.zIndex || '';
            target.dataset.editPrevPosition = target.style.position || '';
            target.dataset.editPrevFilter = target.style.filter || '';

            target.style.outline = '3px dashed rgba(245, 184, 32, 0.95)';
            target.style.outlineOffset = '-3px';
            target.style.cursor = 'pointer';
            if (!target.style.position) target.style.position = 'relative';
            target.style.zIndex = '60';
            target.style.mixBlendMode = 'normal';
            target.style.opacity = '1';
            target.style.filter = 'none';
            target.title = 'Cliquer pour ajouter une photo';
            target.addEventListener('click', onImageClick);
            // Sauvegarde le target pour le retrait en deactivate()
            el._editClickTarget = target;
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

        imageEditables.forEach(function(el) {
            var target = el._editClickTarget || el;
            target.style.outline = target.dataset.editPrevOutline || '';
            target.style.outlineOffset = '';
            target.style.cursor = '';
            target.style.zIndex = target.dataset.editPrevZIndex || '';
            target.style.position = target.dataset.editPrevPosition || '';
            target.style.opacity = target.dataset.editPrevOpacity || '';
            target.style.mixBlendMode = target.dataset.editPrevMixBlend || '';
            target.style.filter = target.dataset.editPrevFilter || '';
            delete target.dataset.editPrevOutline;
            delete target.dataset.editPrevOpacity;
            delete target.dataset.editPrevMixBlend;
            delete target.dataset.editPrevZIndex;
            delete target.dataset.editPrevPosition;
            delete target.dataset.editPrevFilter;
            target.removeAttribute('title');
            target.removeEventListener('click', onImageClick);
            delete target._editImageRef;
            delete el._editClickTarget;
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

    function getCsrf() {
        var token = '';
        document.cookie.split(';').forEach(function(c) {
            c = c.trim();
            if (c.startsWith('csrftoken=')) token = c.substring(10);
        });
        return token;
    }

    function onImageClick(e) {
        e.preventDefault();
        e.stopPropagation();
        var clicked = e.currentTarget;
        // Si on a cliqué sur un placeholder, les data-attrs sont sur l'img frère
        var img = clicked._editImageRef || clicked;
        var fieldName = img.dataset.editImage;
        var pageId = img.dataset.editPage;
        var modelKey = img.dataset.editModel;
        var objectId = img.dataset.editObject;

        var picker = document.createElement('input');
        picker.type = 'file';
        picker.accept = 'image/jpeg,image/png,image/webp';
        picker.style.display = 'none';
        document.body.appendChild(picker);
        picker.addEventListener('change', function() {
            var file = picker.files && picker.files[0];
            document.body.removeChild(picker);
            if (!file) return;
            if (file.size > 8 * 1024 * 1024) {
                alert('Image trop volumineuse (max 8 Mo).');
                return;
            }

            var prevOutline = img.style.outline;
            img.style.opacity = '0.5';

            var formData = new FormData();
            formData.append('field', fieldName);
            formData.append('image', file);
            if (modelKey && objectId) {
                formData.append('model', modelKey);
                formData.append('object', objectId);
            } else if (pageId) {
                formData.append('page', pageId);
            }

            fetch('/gestion/live-edit-image/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() },
                body: formData,
            })
            .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
            .then(function(res) {
                img.style.opacity = '';
                if (res.ok && res.data.ok) {
                    img.removeAttribute('hidden');
                    // Cache-bust pour forcer le rechargement de l'image
                    img.src = res.data.url + '?t=' + Date.now();
                    // Masque un éventuel placeholder frère ("Aucune image")
                    var placeholder = img.parentElement && img.parentElement.querySelector('[data-edit-image-placeholder]');
                    if (placeholder) placeholder.style.display = 'none';
                    // Si on avait cliqué sur le placeholder, transfère le mode édition vers l'img maintenant visible
                    if (clicked !== img) {
                        img.style.outline = '3px dashed rgba(245, 184, 32, 0.95)';
                        img.style.outlineOffset = '-3px';
                        img.style.cursor = 'pointer';
                        if (!img.style.position) img.style.position = 'relative';
                        img.style.zIndex = '60';
                        img.title = 'Cliquer pour changer l\'image';
                        img.addEventListener('click', onImageClick);
                        img._editClickTarget = img;
                    }
                } else {
                    alert('Erreur : ' + (res.data.error || 'upload impossible'));
                }
            })
            .catch(function() {
                img.style.opacity = '';
                alert('Erreur réseau lors de l\'upload.');
            });
        });
        picker.click();
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
