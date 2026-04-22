window.loadAllObdCharts = loadAll;
console.log("[obd_charts] Script cargado.");

async function fetchSeries(url) {
    // const res = await fetch(url);
    // return await res.json();
    const res = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
    });
    

    // para ver si el backend devuelve 403/404/500
    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} al pedir ${url}. ${text}`);
    }

    const data = await res.json();

    // Validación mínima del formato esperado
    if (
        !data ||
        !Array.isArray(data.labels) ||
        !Array.isArray(data.values)
    ) {
        throw new Error(
        `Respuesta inválida en ${url}. Se esperaba {labels:[], values:[]}. Recibido: ${JSON.stringify(data)}`,
        );
    }
      
    console.log("URL solicitada:", url);
    console.log("Datos recibidos:", data);
    // console.log("Datos RPM:", rpm); 

    return data;

     
}

function buildUrl(base, vehiculoId, fi, ff) {
    const params = new URLSearchParams();
    if (vehiculoId) params.append('vehiculo_id', vehiculoId);
    if (fi) params.append('fecha_inicio', fi);
    if (ff) params.append('fecha_fin', ff);
    // return `${base}?${params.toString()}`;

    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
}

let charts = {};

function renderLineChart(canvasId, labels, values, labelName) {
    // const ctx = document.getElementById(canvasId);
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(
        `[obd_charts] No existe el canvas #${canvasId} en el DOM.`,
        );
        return;
    }
        if (typeof Chart === 'undefined') {
        console.error('[obd_charts] Chart.js no está cargado. Verifica que incluyas chart.js antes de este script.');
        return;
    }
    const ctx = canvas.getContext('2d');

    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
                // label: labelName, data: values}]
            // label: labelName,
            // data: values,
                // No fijamos colores para no pelear con AdminLTE; Chart.js usará defaults.
            // borderWidth: 2,
            // pointRadius: 0,
            // tension: 0.25,
            label: labelName,
            data: values,
            borderWidth: 2,
            fill: false,
            pointRadius: labels.length <= 1 ? 5 : 2,
            pointHoverRadius: labels.length <= 1 ? 6 : 4,
            spanGaps: true,
            showLine: values.length > 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true },
        },
        scales: {
          x: {
            ticks: { maxRotation: 0, autoSkip: true },
            grid: { display: false },
          },
          y: {
            beginAtZero: false,
          },
        },
      },
    });
    console.log(`Renderizando gráfica ${canvasId} con datos:`, values);
    
}

function getApiBase() {
    // poner en el template: <div id="obdChartsRoot" data-api-base="/api/obd"></div>
    const root = document.getElementById('obdChartsRoot');
    const base = root?.dataset?.apiBase;
    return base || '/api/obd';
}


async function loadAll() {
    console.log("[obd_charts] Cargando todas las gráficas...");
    // const vehiculoId = document.getElementById('vehiculoId').value;
    // const fi = document.getElementById('fechaInicio').value;
    // const ff = document.getElementById('fechaFin').value;

    const vehiculoIdEl = document.getElementById("vehiculoId");
    const fiEl = document.getElementById("fechaInicio");
    const ffEl = document.getElementById("fechaFin");

    // const rpm = await fetchSeries(buildUrl('/api/obd/rpm/', vehiculoId, fi, ff));
    // renderLineChart('chartRpm', rpm.labels, rpm.values, 'RPM promedio');
    if (!vehiculoIdEl) {
      console.error("[obd_charts] Falta el input #vehiculoId en el template.");
      return;
    }

    // const temp = await fetchSeries(buildUrl('/api/obd/temp/', vehiculoId, fi, ff));
    // renderLineChart('chartTemp', temp.labels, temp.values, 'Temperatura motor promedio (°C)');
    const vehiculoId = vehiculoIdEl.value;
    const fi = fiEl ? fiEl.value : null;
    const ff = ffEl ? ffEl.value : null;

    // const vehspeed = await fetchSeries(buildUrl('/api/obd/vehspeed/', vehiculoId, fi, ff));
    // renderLineChart('chartVehSpeed', vehspeed.labels, vehspeed.values, 'Velocidad vehículo promedio (km/h)');
    const apiBase = getApiBase();
    // const apiBase = "api/obd";
    console.info("[obd_charts] apiBase:", apiBase);
    // console.log("[obd_charts] apiBase corregido:", apiBase);

    // const coolant = await fetchSeries(buildUrl('/api/obd/coolant/', vehiculoId, fi, ff));
    // renderLineChart('chartCoolant', coolant.labels, coolant.values, 'Temperatura refrigerante promedio (°C)');
    try {
        const rpm = await fetchSeries(
        buildUrl(`${apiBase}/rpm/`, vehiculoId, fi, ff),
        );
        renderLineChart("chartRpm", rpm.labels, rpm.values, "RPM promedio");

        // const oilpressure = await fetchSeries(buildUrl('/api/obd/oilpressure/', vehiculoId, fi, ff));
        // renderLineChart('chartOilPressure', oilpressure.labels, oilpressure.values, 'Presión de aceite promedio (psi)');
        const temp = await fetchSeries(
        buildUrl(`${apiBase}/temp/`, vehiculoId, fi, ff),
        );
        renderLineChart(
        "chartTemp",
        temp.labels,
        temp.values,
        "Temperatura motor promedio (°C)",
        );

        // const alerts = await fetchSeries(buildUrl('/api/obd/alerts/', vehiculoId, fi, ff));
        // renderLineChart('chartAlerts', alerts.labels, alerts.values, 'Alertas activas');
        const vehspeed = await fetchSeries(
        buildUrl(`${apiBase}/vehspeed/`, vehiculoId, fi, ff),
        );
        renderLineChart(
        "chartVehSpeed",
        vehspeed.labels,
        vehspeed.values,
        "Velocidad vehículo promedio (km/h)",
        );

        const coolant = await fetchSeries(
        buildUrl(`${apiBase}/coolant/`, vehiculoId, fi, ff),
        );
        renderLineChart(
        "chartCoolant",
        coolant.labels,
        coolant.values,
        "Temperatura refrigerante promedio (°C)",
        );

        const oilpressure = await fetchSeries(
        buildUrl(`${apiBase}/oilpressure/`, vehiculoId, fi, ff),
        );
        renderLineChart(
        "chartOilPressure",
        oilpressure.labels,
        oilpressure.values,
        "Presión de aceite promedio (psi)",
        );

        const alerts = await fetchSeries(
        buildUrl(`${apiBase}/alerts/`, vehiculoId, fi, ff),
        );
        renderLineChart(
        "chartAlerts",
        alerts.labels,
        alerts.values,
        "Alertas activas",
        );
    } catch (err) {
        console.error("[obd_charts] Error cargando series:", err);
        // Si quieres, aquí puedes mostrar un toast de AdminLTE o un alert en el template.
    }
}

// IMPORTANTE: Antes este archivo definía loadAll() pero NO lo ejecutaba.
// Esto hace que las gráficas nunca se pinten.
document.addEventListener('DOMContentLoaded', () => {
    // Prefija un rango reciente para que el usuario vea datos útiles al abrir la pantalla.
    const fiInput = document.getElementById('fechaInicio');
    const ffInput = document.getElementById('fechaFin');

    const formatDateLocal = (date) => {
        const tzAdjusted = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
        return tzAdjusted.toISOString().split('T')[0];
    };

    if (ffInput && !ffInput.value) {
        const today = new Date();
        ffInput.value = formatDateLocal(today);
    }

    if (fiInput && !fiInput.value) {
        const start = new Date();
        start.setDate(start.getDate() - 7); // última semana por defecto
        fiInput.value = formatDateLocal(start);
    }

    // 1) Si hay botón aplicar filtros, lo amarramos.
    const btn = document.getElementById('btnAplicar');
    if (btn) {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            loadAll();
        });
    }

    // 2) Carga inicial (si ya hay vehiculoId seteado)
    const vehiculoIdEl = document.getElementById('vehiculoId');
    if (vehiculoIdEl && vehiculoIdEl.value) {
        loadAll();
    }
});

// Si necesitas llamar manualmente desde el template (onclick), exponemos:
window.loadAllObdCharts = loadAll;
