const REFRESH_INTERVAL = 30000;  // 30 Sekunden in ms

// Speichert die letzten Werte für Vergleich
let lastValues = {};

function updateElement(id, value, prefix = "") {
    const element = document.getElementById(id);
    const oldValue = element.innerHTML;
    const newValue = `${prefix}${value}`;
    
    if (oldValue !== newValue) {
        element.innerHTML = newValue;
        element.classList.add('updated');
        setTimeout(() => {
            element.classList.remove('updated');
        }, 1000);
    }
}

async function fetchData() {
    try {
        console.log("Starte Datenabruf...");
        
        // Teste zuerst die API-Verbindung
        const testResp = await fetch("/test");
        const testData = await testResp.json();
        console.log("API Test Ergebnisse:", testData);
        
        // Hole die eigentlichen Daten
        const resp = await fetch("/data");
        console.log("Daten Response Status:", resp.status);
        console.log("Daten Response Headers:", resp.headers);
        
        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status}`);
        }
        
        const text = await resp.text();
        console.log("Rohe Antwort:", text);
        
        const data = JSON.parse(text);
        console.log("Raw response text:", text);
        console.log("Parsed data:", data);
        console.log("Premier rating:", data.premier_rating);
        console.log("KD ratio:", data.kd_ratio);

        // Update alle Statistiken
        updateElement("current_map", data.current_map);
        updateElement("premier_rating", String(data.premier_rating));
        // Always show K/D ratio as is, it will be properly formatted from the backend
        updateElement("kd_ratio", data.kd_ratio);
        // Elo gained today (may contain colored HTML)
        if (data.elo !== undefined) {
            updateElement("elo", data.elo);
        }
        updateElement("last_updated", data.last_updated, "");

        // Speichern der aktuellen Werte
        lastValues = { ...data };
        
        console.log("Daten erfolgreich aktualisiert");
    } catch (err) {
        console.error("Fehler beim Laden der Daten:", err);
        console.error("Stack trace:", err.stack);
    }
}

// Initiale Daten laden
fetchData();

// Regelmäßiges Update
setInterval(fetchData, REFRESH_INTERVAL);
