function gaugeColorByStatus(status) {
  if (status === "critical") return "#dc3545";
  if (status === "warning") return "#ffc107";
  if (status === "ok") return "#58D9F9";
  return "#6c757d";
}

function buildGaugeOption(gaugeData) {
  const mainColor = gaugeColorByStatus(gaugeData.status);
  const unitText = gaugeData.unit || "";

  return {
    series: [
      {
        type: "gauge",
        startAngle: 180,
        endAngle: 0,
        min: gaugeData.min,
        max: gaugeData.max,
        splitNumber: 10,
        itemStyle: {
          color: mainColor,
          shadowColor: "rgba(0,138,255,0.25)",
          shadowBlur: 10,
          shadowOffsetX: 2,
          shadowOffsetY: 2
        },
        progress: {
          show: true,
          roundCap: true,
          width: 16
        },
        pointer: {
          icon: "path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.194028 2092.44859,617.312956 L2096.90698,728.755929 C2097.05155,732.369577 2094.2393,735.416212 2090.62566,735.56078 C2090.53845,735.564269 2090.45117,735.566014 2090.36389,735.566014 L2090.36389,735.566014 C2086.74736,735.566014 2083.81557,732.63423 2083.81557,729.017692 C2083.81557,728.930412 2083.81732,728.84314 2083.82081,728.755929 L2088.2792,617.312956 C2088.32396,616.194028 2089.24407,615.30999 2090.36389,615.30999 Z",
          length: "75%",
          width: 12,
          offsetCenter: [0, "5%"]
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 18
          }
        },
        axisTick: {
          splitNumber: 2,
          lineStyle: {
            width: 2,
            color: "#999"
          }
        },
        splitLine: {
          length: 12,
          lineStyle: {
            width: 3,
            color: "#999"
          }
        },
        axisLabel: {
          distance: 20,
          color: "#999",
          fontSize: 12
        },
        title: {
          show: true,
          offsetCenter: [0, "85%"],
          fontSize: 16,
          color: "#444"
        },
        detail: {
          backgroundColor: "#fff",
          borderColor: "#999",
          borderWidth: 2,
          width: "70%",
          lineHeight: 30,
          height: 38,
          borderRadius: 8,
          offsetCenter: [0, "40%"],
          valueAnimation: true,
          formatter: function (value) {
            return "{value|" + Number(value).toFixed(0) + "}{unit| " + unitText + "}";
          },
          rich: {
            value: {
              fontSize: 24,
              fontWeight: "bold",
              color: "#555"
            },
            unit: {
              fontSize: 13,
              color: "#888",
              padding: [0, 0, -4, 6]
            }
          }
        },
        data: [
          {
            value: gaugeData.value,
            name: gaugeData.title
          }
        ]
      }
    ]
  };
}

function renderVehicleGauge(containerId, gaugeData) {
  const el = document.getElementById(containerId);
  if (!el) return;

  const chart = echarts.init(el);
  chart.setOption(buildGaugeOption(gaugeData));

  window.addEventListener("resize", function () {
    chart.resize();
  });

  return chart;
}

async function loadVehicleGauges(apiUrl) {
  try {
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (!data.ok) {
      const errorBox = document.getElementById("gauges-error");
      if (errorBox) {
        errorBox.innerText = data.message || "No se pudieron cargar los indicadores";
        errorBox.classList.remove("d-none");
      }
      return;
    }

    renderVehicleGauge("gauge-rpm", data.gauges.rpm);
    renderVehicleGauge("gauge-temperature", data.gauges.temperature);
    renderVehicleGauge("gauge-battery", data.gauges.battery);
    renderVehicleGauge("gauge-fuel", data.gauges.fuel);
    renderVehicleGauge("gauge-oil", data.gauges.oil_pressure);

    const ts = document.getElementById("gauges-timestamp");
    if (ts) {
      ts.innerText = "Última lectura: " + data.timestamp;
    }
  } catch (error) {
    const errorBox = document.getElementById("gauges-error");
    if (errorBox) {
      errorBox.innerText = "Error al cargar los gauges";
      errorBox.classList.remove("d-none");
    }
    console.error(error);
  }
}

async function loadGauges(vehiculoId) {
  const apiUrl = `/api/obd/gauges/?vehiculo_id=${vehiculoId}`;
  return loadVehicleGauges(apiUrl);
}