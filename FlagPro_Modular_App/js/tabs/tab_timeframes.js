window.sortDirections = window.sortDirections || { 'data-score': true };

function sortTableByAttr(tableId, attrName, isNumeric, defaultDesc, btnElem) {
            let table = document.getElementById(tableId);
            if (!table) return;
            let tbody = table.querySelector('tbody');
            if (!tbody) return;
            let rows = Array.from(tbody.querySelectorAll('tr.tf-row, tr.tf-role-row'));

            let sortDirs = window.sortDirections || {};
            let isCurrentDesc = sortDirs[attrName];
            let newDesc = (isCurrentDesc === undefined) ? defaultDesc : !isCurrentDesc;
            sortDirs[attrName] = newDesc;
            window.sortDirections = sortDirs;

            let headers = table.querySelectorAll('th');
            headers.forEach(h => {
                let icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = ' ⬍';
                h.style.background = '';
            });

            let activeTh = table.querySelector(`th[data-sort="${attrName}"]`);
            if (activeTh) {
                let icon = activeTh.querySelector('.sort-icon');
                if (icon) icon.textContent = newDesc ? ' ▼' : ' ▲';
                activeTh.style.background = '#1e293b';
            }

            if (btnElem) {
                let p = btnElem.parentElement;
                if (p) {
                    p.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    btnElem.classList.add('active');
                }
            }

            rows.sort((a, b) => {
                let valA = a.getAttribute(attrName) || '';
                let valB = b.getAttribute(attrName) || '';

                if (isNumeric) {
                    let numA = parseFloat(valA) || 0.0;
                    let numB = parseFloat(valB) || 0.0;
                    if (numA !== numB) {
                        return newDesc ? (numB - numA) : (numA - numB);
                    }
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                } else {
                    let res = valA.localeCompare(valB);
                    if (res !== 0) return newDesc ? -res : res;
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                }
            });

            rows.forEach((r, i) => {
                let firstTd = r.querySelector('td:first-child');
                if (firstTd && firstTd.textContent.trim().startsWith('#')) {
                    firstTd.textContent = '#' + (i + 1);
                }
                tbody.appendChild(r);
            });
        }

        function filterTF(tf, btnElem) {
            let btns = document.querySelectorAll('.tf-btn');
            btns.forEach(b => b.classList.remove('active'));
            if (btnElem) {
                btnElem.classList.add('active');
            } else if (typeof event !== 'undefined' && event && (event.currentTarget || event.target)) {
                (event.currentTarget || event.target).classList.add('active');
            }

            let rows = document.querySelectorAll('.tf-row, .tf-role-row');
            rows.forEach(r => {
                if(tf === 'ALL' || r.getAttribute('data-tf') === tf) {
                    r.style.display = '';
                } else {
                    r.style.display = 'none';
                }
            });
        }