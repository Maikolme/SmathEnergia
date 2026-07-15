const API = {
    async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Error ${res.status}`);
        return res.json();
    },

    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async put(url, data) {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async delete(url) {
        const res = await fetch(url, { method: 'DELETE' });
        return res.json();
    }
};

const { createApp, ref, reactive, computed, onMounted, watch, nextTick } = Vue;
