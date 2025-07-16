async function fetchTemperatureData() {
    try {
        const response = await fetch("/api/temperature-history");
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching temperature data:", error);
        return [];
    }
}

function renderChart(data) {
    const ctx = document.getElementById("temperature-chart").getContext("2d");
    const chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString()),
            datasets: [{
                label: "Water Temperature (°C)",
                data: data.map(d => d.temperature),
                borderColor: "rgba(75, 192, 192, 1)",
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderWidth: 2,
                fill: true,
                pointRadius: 0
            }]
        },
        options: {
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: false,
                    suggestedMin: 50,
                    suggestedMax: 70
                }
            },
            animation: false,
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    const data = await fetchTemperatureData();
    renderChart(data);
});