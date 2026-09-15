/* Use the actual installed renderers; this is a browser fixture, not Typora UI. */
window.quietypeReady = new Promise(resolve => window.addEventListener('load', async () => {
    const errors = [...window.quietypeLoadErrors];
    const editors = [];
    await document.fonts.ready;
    const css = getComputedStyle(document.body);
    try {
        mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'strict',
            theme: css.getPropertyValue('--mermaid-theme').trim(),
            fontFamily: 'sans-serif',
            flowchart: {htmlLabels: true, useMaxWidth: true,
                curve: css.getPropertyValue('--mermaid-flowchart-curve').trim()},
            sequence: {useMaxWidth: false, diagramMarginX: 8, diagramMarginY: 8, boxMargin: 8}
        });
        for (const pre of document.querySelectorAll('pre[lang="mermaid"]')) {
            const source = pre.textContent;
            pre.textContent = '';
            pre.className = 'md-fences md-fences-advanced';
            const panel = document.createElement('div');
            panel.className = 'md-diagram-panel md-diagram-panel-preview';
            pre.append(panel);
            const {svg} = await mermaid.render(`quietype-diagram-${pre.dataset.diagramId}`, source);
            panel.innerHTML = svg;
        }
    } catch (error) { errors.push(`Mermaid: ${error.message}`); }

    try {
        await MathJax.startup.promise;
        await MathJax.typesetPromise();
    } catch (error) { errors.push(`MathJax: ${error.message}`); }

    try {
        const aliases = {js: 'javascript', json: {name: 'javascript', json: true},
            text: null, '': null, bash: 'shell', sh: 'shell', html: 'htmlmixed'};
        for (const pre of document.querySelectorAll('pre.md-fences:not([lang="mermaid"])')) {
            const original = pre.textContent;
            const language = pre.getAttribute('lang') || '';
            pre.textContent = '';
            pre.classList.remove('mock-cm', 'cm-s-inner');
            const cm = CodeMirror(pre, {value: original,
                mode: Object.hasOwn(aliases, language) ? aliases[language] : language,
                theme: 'inner', lineWrapping: true, viewportMargin: Infinity,
                cursorBlinkRate: 0}, window.File.editor);
            cm.setSize(null, 'auto');
            // Insertion and undo must preserve the full source, including blank lines.
            cm.replaceRange('    preview_probe\n', {line: 0, ch: 0}, null, '+input');
            cm.undo();
            editors.push({language, preserved: cm.getValue() === original, lines: cm.lineCount()});
            cm.clearHistory();
            cm.refresh();
        }
    } catch (error) { errors.push(`CodeMirror: ${error.message}`); }
    await document.fonts.ready;
    window.scrollTo(0, 0);
    resolve({errors, editors, codeMirrorVersion: window.CodeMirror?.version});
}));
