document.addEventListener('DOMContentLoaded', async function() {
    const isLoggedIn = await checkSession();

    if (!isLoggedIn) {
        alert('Пожалуйста, войдите в систему!');
        window.location.href = 'index.html';
        return;
    }

    const main = document.querySelector('main');

    if (main) {
        main.classList.add('section-visible');
    }

    await updateFileList();

    const searchInput = document.getElementById('fileSearchInput');
    function debounce(fn, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim().toLowerCase();
            await updateFileList(query);
        }, 300));
    }
});

async function uploadFile() {
    const file = document.getElementById('fileInput').files[0];
    if (!file) return alert("Выберите файл!");

    const fileName = document.getElementById('fileNameInput').value || file.name;
    const fileDesc = document.getElementById('fileDescInput').value || "";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", fileName);
    formData.append("description", fileDesc);

    try {
        const res = await fetch('/api/data/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error(`Ошибка ${res.status}`);
        const data = await res.json();
        alert(`Файл загружен: ${JSON.stringify(data)}`);

        await updateFileList();
    } catch (err) {
        console.error(err);
        alert('Ошибка при загрузке файла');
    }
}

async function getCsvPreview(filename) {
    try {
        const response = await fetch(`/api/processing/analyze/${filename}`);
        if (!response.ok) throw new Error(`Ошибка ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Ошибка при получении preview CSV:', error);
        return { 
            preview: 'Не удалось загрузить preview', 
            columns_total: 0, 
            analysis: [] 
        };
    }
}

async function performCsvAnalysis(filename, columns, resultsDiv) {
    try {
        resultsDiv.classList.add('analysis-results-visible');
        resultsDiv.innerHTML = '<div class="loading">Загрузка анализа...</div>';
        
        const url = columns ? 
            `/api/processing/analyze/${filename}?columns=${encodeURIComponent(columns)}` : 
            `/api/processing/analyze/${filename}`;
            
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Ошибка ${response.status}`);
        
        const data = await response.json();
        
        resultsDiv.innerHTML = `
            <div class="analysis-summary">
                <h4>Результаты анализа</h4>
                <p><strong>Файл:</strong> ${data.filename}</p>
                <p><strong>Всего столбцов:</strong> ${data.columns_total}</p>
                <p><strong>Выбранные столбцы:</strong> ${data.columns_selected}</p>
            </div>
            
            <div class="analysis-details">
                <h4>Статистика по столбцам:</h4>
                <div class="analysis-table">
                    ${data.analysis.map(col => `
                        <div class="analysis-row">
                            <div class="column-name"><strong>${col.column}</strong></div>
                            <div class="column-stats">
                                <span>Сумма: ${col.sum}</span>
                                <span>Среднее: ${col.average}</span>
                                <span>Наибольшее значение: ${col.max}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Ошибка при анализе CSV:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h4>Ошибка анализа</h4>
                <p>Не удалось проанализировать файл: ${error.message}</p>
            </div>
        `;
    }
}

async function updateFileList(searchQuery = '') {
    try {
        const response = await fetch('/api/data/files');
        const files = await response.json();
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        const filteredFiles = files.filter(f => 
            f.title.toLowerCase().includes(searchQuery) || 
            f.filename.toLowerCase().includes(searchQuery)
        );

        for (const file of filteredFiles) {
            const div = document.createElement('div');
            div.classList.add('file-item', 'file-item-card');
            div.setAttribute('data-filename', file.filename);

            const div_info =document.createElement('div');
            div_info.classList.add('card-info');
            const info = document.createElement('p');
            const info1 = document.createElement('p');
            const info2 = document.createElement('p');
            const descrptnShow = file.description?.trim() || "Нет";
            info.textContent = `Имя: ${file.title}`;
            info1.textContent = `Тип: ${file.filetype}`;
            info2.textContent = `Описание: ${descrptnShow}`;
            div_info.append(info, info1, info2);
            div.appendChild(div_info);

            if (file.filetype === 'csv') {
                const previewContainer = document.createElement('div');
                previewContainer.classList.add('csv_preview', 'csv-preview-wrapper');

                const previewContent = document.createElement('pre');
                previewContent.classList.add('csv-preview-content');

                previewContainer.appendChild(previewContent);

                const statsContainer = document.createElement('div');
                previewContainer.appendChild(statsContainer);
                
                div.appendChild(previewContainer);

                try {
                    const data = await getCsvPreview(file.filename);
                    previewContent.textContent = data.preview;
                } catch (error) {
                    previewContent.textContent = 'Ошибка загрузки preview';
                }
            }

            if (file.filetype === 'photo') {
                const div_img= document.createElement('div');
                div_img.classList.add('div_img', 'image-container');
                const img = document.createElement('img');
                img.src = `/api/data/download/${file.filename}`;
                img.alt = file.filename;
                div_img.appendChild(img);
                div.appendChild(div_img);
            }

            const downloadBtn = document.createElement('button');
            downloadBtn.classList.add('card_btn');
            downloadBtn.textContent = 'Скачать';
            downloadBtn.onclick = () => {
                const link = document.createElement('a');
                link.href = `/api/data/download/${file.filename}`;
                link.download = file.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };
            

            const deleteBtn = document.createElement('button');
            deleteBtn.classList.add('card_btn');
            deleteBtn.textContent = 'Удалить';
            deleteBtn.onclick = async () => {
                const confirmDelete = confirm(`Вы уверены, что хотите удалить ${file.filename}?`);
                if (!confirmDelete) return;

                const res = await fetch(`/api/data/files/${file.filename}`, { method: 'DELETE' });
                if (res.ok) {
                    alert(`${file.filename} удалён`);
                    await updateFileList(searchQuery);
                } else {
                    const errorData = await res.json();
                    alert(`Ошибка: ${errorData.detail}`);
                }
            }

            const buttonsContainer = document.createElement('div');
            buttonsContainer.classList.add('buttons-container');

            buttonsContainer.appendChild(downloadBtn);
            buttonsContainer.appendChild(deleteBtn);

            div.appendChild(buttonsContainer);

            fileList.appendChild(div);
        }

        if (filteredFiles.length === 0) {
            fileList.textContent = 'Файлы не найдены';
        }

    } catch (err) {
        console.error(err);
        document.getElementById('fileList').textContent = 'Ошибка при загрузке файлов';
    }
}


function showSection(section) {
    const uploadSection = document.getElementById('upload_section');
    const searchSection = document.getElementById('search_section');

    if (section === 'upload') {
        uploadSection.classList.remove('section-hidden');
        uploadSection.classList.add('section-visible');
        searchSection.classList.remove('section-visible');
        searchSection.classList.add('section-hidden');
    } else if (section === 'search') {
        uploadSection.classList.remove('section-visible');
        uploadSection.classList.add('section-hidden');
        searchSection.classList.remove('section-hidden');
        searchSection.classList.add('section-visible');
    }
}

document.addEventListener('click', async function (e) {

    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        return;
    }

    const card = e.target.closest('.file-item');
    if (!card) return;

    const overlay = document.createElement('div');
    overlay.classList.add('overlay');

    const modal = document.createElement('div');
    modal.classList.add('modal-card');
    
    const fileInfo = card.querySelector('.card-info');
    const fileName = fileInfo.querySelector('p:first-child').textContent.replace('Имя: ', '');
    const fileType = fileInfo.querySelector('p:nth-child(2)').textContent.replace('Тип: ', '');
    const fileDescription = fileInfo.querySelector('p:nth-child(3)').textContent.replace('Описание: ', '');
    const actualFilename = card.getAttribute('data-filename');
    
    modal.innerHTML = `
        <div class="card-info">
            <p>Имя: ${fileName}</p>
            <p>Тип: ${fileType}</p>
            <p>Описание: ${fileDescription}</p>
        </div>
        
    `;

    if (fileType === 'photo' && actualFilename) {
        const imgContainer = document.createElement('div');
        imgContainer.classList.add('modal-image-container');
        imgContainer.innerHTML = `
            <img src="/api/data/download/${actualFilename}" alt="${fileName}" style="max-width: 100%; height: auto; display: block; margin: 15px auto;">
        `;
        modal.appendChild(imgContainer);
    }

    if (fileType === 'csv' && actualFilename) {
        const previewContainer = document.createElement('div');
        previewContainer.classList.add('csv-preview-container');
        previewContainer.innerHTML = `
            <div class="preview-section">
                <h4>Предварительный просмотр:</h4>
                <pre class="csv-preview" id="csvPreviewContent">Загрузка...</pre>
            </div>
        `;
        modal.appendChild(previewContainer);
        
        try {
            const data = await getCsvPreview(actualFilename);
            const previewElement = modal.querySelector('#csvPreviewContent');
            if (previewElement) {
                previewElement.textContent = data.preview;
            }
        } catch (error) {
            const previewElement = modal.querySelector('#csvPreviewContent');
            if (previewElement) {
                previewElement.textContent = 'Ошибка загрузки preview';
            }
        }

        const csvAnalysisContainer = document.createElement('div');
        csvAnalysisContainer.classList.add('csv-analysis-container');
        csvAnalysisContainer.innerHTML = `
            <div class="analysis-controls">
                <h3>Анализ CSV файла</h3>
                <div class="column-selection">
                    <label for="columnInput">Выберите столбцы для анализа (номера через запятую, начиная с 1):</label>
                    <input type="text" id="columnInput" placeholder="Например: 1,3,5 или оставьте пустым для всех столбцов">
                    <button id="analyzeBtn" class="analyze-btn">Анализировать</button>
                </div>
                <div id="analysisResults" class="analysis-results section-hidden"></div>
            </div>
        `;
        modal.appendChild(csvAnalysisContainer);
        
        const analyzeBtn = modal.querySelector('#analyzeBtn');
        const columnInput = modal.querySelector('#columnInput');
        const resultsDiv = modal.querySelector('#analysisResults');
        
        analyzeBtn.addEventListener('click', async () => {
            resultsDiv.classList.remove('section-hidden');
            resultsDiv.classList.add('analysis-results-visible');
            const columns = columnInput.value.trim();
            await performCsvAnalysis(actualFilename, columns, resultsDiv);
        });
    }

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.classList.add('close-btn');
    closeBtn.classList.add('modal-close-btn');
    closeBtn.addEventListener('click', () => overlay.remove());
    modal.appendChild(closeBtn);

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
});
