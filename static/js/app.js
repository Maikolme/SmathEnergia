function useSidenav() {
    onMounted(() => {
        M.Sidenav.init(document.querySelectorAll('.sidenav'));
    });
}

function useSelects() {
    onMounted(() => {
        nextTick(() => {
            M.FormSelect.init(document.querySelectorAll('select'));
        });
    });
}

function useLocalStorage(key, defaultValue) {
    const data = ref(defaultValue);

    const load = () => {
        try {
            const stored = localStorage.getItem(key);
            if (stored) data.value = JSON.parse(stored);
        } catch {}
    };

    const save = (value) => {
        data.value = value;
        localStorage.setItem(key, JSON.stringify(value));
    };

    load();
    return { data, save, load };
}

function useFlashMessages() {
    onMounted(() => {
        document.querySelectorAll('.swal-flash').forEach(el => {
            const type = el.dataset.type;
            const title = el.dataset.title;
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: type,
                    title: title,
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#00897b',
                    customClass: { popup: 'swal2-popup-custom' },
                    timer: type === 'success' ? 2500 : undefined,
                    timerProgressBar: type === 'success'
                });
            }
        });
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function calculateConsumption(readings) {
    if (!readings || readings.length < 2) return [];
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
