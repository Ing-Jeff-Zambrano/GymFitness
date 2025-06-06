// ATENCIÓN: La variable 'dataPeso' se espera que sea inyectada desde el template de Django
// por ejemplo: const dataPeso = JSON.parse('{{ fechas_pesos_json|safe }}');
// Por lo tanto, NO SE DEFINE AQUÍ con datos de ejemplo.

// Referencia al elemento donde se mostrará el peso seleccionado en el HTML.
const selectedWeightDisplay = document.getElementById('selected-weight-display');

// Variable para mantener el rastro del punto seleccionado previamente.
let previousSelectedDot = null;

// Configuración de márgenes para el gráfico.
const margin = { top: 20, right: 30, bottom: 40, left: 50 };

// Selecciona el contenedor del gráfico.
const container = d3.select("#weight-chart-container");

// Crea el elemento SVG principal y un grupo (g) para el contenido del gráfico.
// Aseguramos que se cree solo un SVG
let svgElement = container.select("svg");
if (svgElement.empty()) {
    svgElement = container.append("svg");
    svgElement.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
}
const svg = svgElement.select("g"); // Selecciona el grupo interno para el resto de operaciones


// Analizador de fechas para convertir cadenas de texto a objetos Date.
const parseDate = d3.timeParse("%Y-%m-%d");

// Función para inicializar o redibujar el gráfico.
// Se llama al cargar la página y al redimensionar la ventana.
function initChart() {
    // Si dataPeso no está definida (ej. en caso de error de Django), se puede salir temprano
    if (typeof dataPeso === 'undefined' || dataPeso.length === 0) {
        selectedWeightDisplay.textContent = "No hay datos de peso disponibles para mostrar.";
        // Limpia el SVG si no hay datos
        svgElement.html('');
        return;
    }

    // Prepara los datos: convierte fechas a objetos Date y pesos a números.
    dataPeso.forEach(d => {
        d.fecha = parseDate(d.fecha);
        d.peso = +d.peso; // El signo + convierte la cadena a número.
    });

    // Recalcula las dimensiones del gráfico basándose en el tamaño actual del contenedor.
    // Usamos el tamaño del contenedor directo del SVG para el cálculo.
    const containerRect = container.node().getBoundingClientRect();
    const width = containerRect.width - margin.left - margin.right;
    const height = containerRect.height - margin.top - margin.bottom;


    // Actualiza los atributos 'width' y 'height' del elemento SVG principal.
    svgElement.attr("width", width + margin.left + margin.right);
    svgElement.attr("height", height + margin.top + margin.bottom);

    // Actualiza la transformación del grupo principal
    svg.attr("transform", `translate(${margin.left},${margin.top})`);


    // Configura la escala para el eje X (tiempo).
    const xScale = d3.scaleTime()
        .domain(d3.extent(dataPeso, d => d.fecha)) // Rango de fechas de los datos.
        .range([0, width]); // Mapea el rango de fechas al ancho del gráfico.

    // Configura la escala para el eje Y (peso).
    const yScale = d3.scaleLinear()
        .domain([d3.min(dataPeso, d => d.peso) - 1, d3.max(dataPeso, d => d.peso) + 1]) // Rango de peso con un pequeño margen.
        .range([height, 0]); // Mapea el rango de peso a la altura del gráfico (invertido para Y).

    // Define el generador de línea D3.
    const lineGenerator = d3.line()
        .x(d => xScale(d.fecha)) // Posición X de cada punto basada en la fecha.
        .y(d => yScale(d.peso)) // Posición Y de cada punto basada en el peso.
        .curve(d3.curveMonotoneX); // Suaviza la línea entre los puntos.

    // Selecciona la ruta de la línea y la actualiza o la crea si no existe.
    const path = svg.selectAll(".line").data([dataPeso]);
    path.enter().append("path")
        .attr("class", "line") // Asigna la clase CSS 'line'.
        .merge(path) // Fusiona los elementos existentes con los nuevos.
        .attr("d", lineGenerator); // Genera la ruta SVG para la línea.

    // Selecciona los círculos (puntos de datos) y los actualiza o los crea.
    const dots = svg.selectAll(".dot").data(dataPeso);
    dots.enter().append("circle")
        .attr("class", "dot") // Asigna la clase CSS 'dot'.
        .merge(dots) // Fusiona los elementos existentes con los nuevos.
        .attr("cx", d => xScale(d.fecha)) // Posición X del círculo.
        .attr("cy", d => yScale(d.peso)) // Posición Y del círculo.
        .attr("r", 4) // Radio por defecto del círculo.
        .on("click", function(event, d) { // Añade un evento de clic a cada punto.
            // Si hay un punto previamente seleccionado, le quita el estilo de resaltado.
            if (previousSelectedDot) {
                d3.select(previousSelectedDot)
                    .attr("class", "dot"); // Vuelve a la clase CSS 'dot' por defecto.
            }

            // Resalta el punto clickeado añadiéndole la clase 'selected'.
            d3.select(this)
                .attr("class", "dot selected");

            // Almacena la referencia del punto clickeado como el 'previousSelectedDot'.
            previousSelectedDot = this;

            // Muestra el peso y la fecha del punto seleccionado en el elemento HTML.
            selectedWeightDisplay.textContent = `Peso: ${d.peso} kg (${d3.timeFormat("%d/%m/%Y")(d.fecha)})`;
        });
    dots.exit().remove(); // Elimina cualquier punto que ya no esté en los datos.

    // Dibuja el eje X.
    const xAxis = svg.selectAll(".x.axis").data([null]); // Solo un eje X.
    xAxis.enter().append("g")
        .attr("class", "x axis") // Asigna la clase CSS 'x axis'.
        .merge(xAxis) // Fusiona y actualiza el eje existente.
        .attr("transform", `translate(0,${height})`) // Coloca el eje en la parte inferior del gráfico.
        .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%b %Y"))); // Formato de fecha para las etiquetas del eje X.

    // Dibuja el eje Y.
    const yAxis = svg.selectAll(".y.axis").data([null]); // Solo un eje Y.
    yAxis.enter().append("g")
        .attr("class", "y axis") // Asigna la clase CSS 'y axis'.
        .merge(yAxis) // Fusiona y actualiza el eje existente.
        .call(d3.axisLeft(yScale)); // Dibuja el eje Y con la escala correspondiente.
}

// Llama a la función initChart cuando la ventana ha cargado completamente.
window.onload = initChart;

// Añade un listener para redibujar el gráfico cada vez que la ventana se redimensiona.
window.addEventListener('resize', initChart);

// Mensaje inicial en el display de peso
selectedWeightDisplay.textContent = "Haz clic en un punto para ver el peso.";