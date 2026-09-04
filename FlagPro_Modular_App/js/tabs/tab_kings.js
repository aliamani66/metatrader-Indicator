function switchKingsSubView(viewMode, el) {
            document.querySelectorAll('.kings-sub-btn').forEach(b => {
                b.style.background = '#0f172a';
                b.style.borderColor = '#334155';
                b.style.color = '#94a3b8';
                b.style.boxShadow = 'none';
            });
            el.style.background = '#0284c7';
            el.style.borderColor = '#38bdf8';
            el.style.color = '#fff';
            el.style.boxShadow = '0 0 12px rgba(56,189,248,0.3)';

            let vMulti = document.getElementById('kingsViewMulti');
            let vAll = document.getElementById('kingsViewAllTime');
            let vComp = document.getElementById('kingsViewCompare');
            if(vMulti) vMulti.style.display = (viewMode === 'multi') ? 'block' : 'none';
            if(vAll) vAll.style.display = (viewMode === 'alltime') ? 'block' : 'none';
            if(vComp) vComp.style.display = (viewMode === 'compare') ? 'block' : 'none';
        }

        let currentHorizon = 'INTERSECTION';
        let currentHorizonTF = 'ALL';

        function showHorizonView(hKey, el) {
            currentHorizon = hKey;
            document.querySelectorAll('.horizon-pill-btn').forEach(b => {
                b.style.background = '#0f172a';
                b.style.borderColor = '#334155';
                b.style.color = '#94a3b8';
                b.style.boxShadow = 'none';
            });
            el.style.background = '#0284c7';
            el.style.borderColor = '#38bdf8';
            el.style.color = '#fff';
            el.style.boxShadow = '0 0 10px rgba(56,189,248,0.3)';

            document.querySelectorAll('.horizon-view-panel').forEach(p => p.style.display = 'none');
            let targetPanel = document.getElementById('panel-horizon-' + hKey);
            if(targetPanel) targetPanel.style.display = 'block';

            applyHorizonFilters();
        }

        function filterHorizonTF(tf, el) {
            currentHorizonTF = tf;
            document.querySelectorAll('.tf-filter-btn').forEach(b => {
                b.style.background = '#1e293b';
                b.style.color = '#94a3b8';
                b.style.fontWeight = 'normal';
            });
            el.style.background = '#0284c7';
            el.style.color = '#fff';
            el.style.fontWeight = 'bold';

            applyHorizonFilters();
        }

        function applyHorizonFilters() {
            let activePanel = document.getElementById('panel-horizon-' + currentHorizon);
            if(!activePanel) return;
            let rows = activePanel.querySelectorAll('.mp-row');
            rows.forEach(r => {
                let rTF = r.getAttribute('data-tf');
                if(currentHorizonTF === 'ALL' || rTF === currentHorizonTF) {
                    r.style.display = '';
                } else {
                    r.style.display = 'none';
                }
            });
        }

        