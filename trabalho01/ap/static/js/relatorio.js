const categorias = JSON.parse(document.getElementById('categorias').textContent);
const quantidades = JSON.parse(document.getElementById('quantidades').textContent);
const statusValores = JSON.parse(document.getElementById('status-valores').textContent);

if (document.getElementById('graficoCategorias')) {
    new Chart(document.getElementById('graficoCategorias'), {
        type: 'bar',
        data: {
            labels: categorias,
            datasets: [{
                label: 'Livros por Categoria',
                data: quantidades,
                backgroundColor: '#5C1F2E',
                borderColor: '#431420',
                borderWidth: 1,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    labels: { font: { family: "'Segoe UI', sans-serif", weight: 'bold' } }
                }
            }
        }
    });
}

if (document.getElementById('graficoStatus')) {
    new Chart(document.getElementById('graficoStatus'), {
        type: 'doughnut',
        data: {
            labels: ['Disponíveis (Ativos)', 'Indisponíveis (Inativos)'],
            datasets: [{
                label: 'Disponibilidade de Livros',
                data: statusValores,
                backgroundColor: [
                    '#5C1F2E', 
                    '#1B2A3D'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { family: "'Segoe UI', sans-serif" } }
                }
            }
        }
    });
}
