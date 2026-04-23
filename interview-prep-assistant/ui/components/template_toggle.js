function attachTemplateToggle(textAreaId, templateBtnId, fetchUrl) {
    const btn = document.getElementById(templateBtnId);
    const textarea = document.getElementById(textAreaId);
    
    if (!btn || !textarea) return;
    
    btn.addEventListener('click', async (e) => {
        e.preventDefault();
        btn.textContent = "Loading template...";
        btn.disabled = true;
        
        try {
            const res = await fetch(fetchUrl, { method: 'POST' });
            const data = await res.json();
            
            textarea.value = data.template;
            textarea.style.opacity = '0.5';
            
            // Revert opacity when user types
            textarea.addEventListener('input', function onInput() {
                textarea.style.opacity = '1';
                textarea.removeEventListener('input', onInput);
            });
            
            btn.textContent = "Template loaded";
        } catch (err) {
            console.error("Failed to load template", err);
            btn.textContent = "Error loading template";
            btn.disabled = false;
        }
    });
}
