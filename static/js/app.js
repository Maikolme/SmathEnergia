document.addEventListener('DOMContentLoaded', function() {
    M.AutoInit();

    document.querySelectorAll('.sidenav').forEach(el => {
        M.Sidenav.init(el, { edge: 'left', draggable: true });
    });

    document.querySelectorAll('select').forEach(el => {
        M.FormSelect.init(el);
    });

    document.querySelectorAll('.tooltip').forEach(el => {
        M.Tooltip.init(el);
    });

    initLocalStorage();
});

function initLocalStorage() {
    if (!localStorage.getItem('energiaSmart_data')) {
        const defaultData = {
            settings: {
                monthlyGoal: 200,
                tariffRate: 0.15,
                currency: 'USD',
                notifications: true
            },
            readings: [],
            lastSync: null
        };
        localStorage.setItem('energiaSmart_data', JSON.stringify(defaultData));
    }
}

function getLocalData() {
    try {
        return JSON.parse(localStorage.getItem('energiaSmart_data')) || {};
    } catch {
        return {};
    }
}

function saveLocalData(data) {
    localStorage.setItem('energiaSmart_data', JSON.stringify(data));
}

function addLocalReading(reading) {
    const data = getLocalData();
    if (!data.readings) data.readings = [];
    data.readings.push({
        id: Date.now(),
        meter_reading: reading.meter_reading,
        reading_date: reading.reading_date,
        notes: reading.notes || '',
        timestamp: new Date().toISOString()
    });
    saveLocalData(data);
}

function getLocalReadings() {
    const data = getLocalData();
    return data.readings || [];
}

function clearLocalReadings() {
    const data = getLocalData();
    data.readings = [];
    saveLocalData(data);
}

function showToast(message, type = 'success') {
    M.toast({
        html: `<i class="material-icons left">${type === 'success' ? 'check_circle' : 'error'}</i>${message}`,
        classes: type === 'success' ? 'green' : 'red',
        displayLength: 3000
    });
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function calculateConsumption(readings) {
    if (readings.length < 2) return [];
    const sorted = [...readings].sort((a, b) => new Date(a.reading_date) - new Date(b.reading_date));
    const result = [];
    for (let i = 1; i < sorted.length; i++) {
        const diff = sorted[i].meter_reading - sorted[i - 1].meter_reading;
        const days = (new Date(sorted[i].reading_date) - new Date(sorted[i - 1].reading_date)) / (1000 * 60 * 60 * 24);
        if (days > 0 && diff >= 0) {
            result.push({
                date: sorted[i].reading_date,
                kwh: parseFloat(diff.toFixed(2)),
                days: Math.round(days),
                daily_avg: parseFloat((diff / days).toFixed(2))
            });
        }
    }
    return result;
}
