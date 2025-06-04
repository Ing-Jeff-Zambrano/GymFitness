document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM completamente cargado. Inicializando scripts de cámara (revisión final).');

    // --- Elementos Comunes de la Cámara ---
    const cameraStream = document.getElementById('camera-stream');
    const cameraCanvas = document.getElementById('camera-canvas');
    const context = cameraCanvas.getContext('2d');
    const cameraMessage = document.getElementById('camera-message'); // Mensaje de progreso

    // --- Lógica y Elementos para Foto de Perfil ---
    const startCameraButton = document.getElementById('start-camera');
    const capturePhotoButton = document.getElementById('capture-photo');
    const recapturePhotoButton = document.getElementById('recapture-photo');
    const savePhotoButton = document.getElementById('save-photo');
    const cancelPhotoButton = document.getElementById('cancel-photo');
    const cameraPhotoDataInput = document.getElementById('camera-photo-data');

    // --- Lógica y Elementos para Detección de Cuerpo ---
    const detectBodyTypeButton = document.getElementById('detect-body-type');
    const startBodyCaptureButton = document.getElementById('start-body-capture'); // Botón de iniciar captura
    const measurementPhotoDataInput = document.getElementById('measurement-photo-data'); // Input para array de base64

    // Variables de control para ambos modos
    let currentStream = null;
    let animationFrameId = null;
    let isBodyDetectionModeActive = false; // Flag para controlar el modo de detección de cuerpo
    let captureIntervalId = null; // Para controlar el intervalo de captura de fotos

    // --- MediaPipe Initialization (Solo si está disponible y para detección de cuerpo) ---
    let pose = null;
    let mp_drawing = null;
    let PoseLandmark = null;

    // Verificar si MediaPipe está disponible globalmente
    if (typeof Pose !== 'undefined' && typeof DrawingUtils !== 'undefined') {
        try {
            pose = new Pose({locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/${file}`;
            }});
            pose.setOptions({
                modelComplexity: 1,
                smoothLandmarks: true,
                enableSegmentation: false,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            pose.onResults(onResultsBodyDetection); // MediaPipe solo llama a esta función
            mp_drawing = DrawingUtils;
            // Definir los landmarks que necesitamos para dibujar las líneas
            PoseLandmark = {
                LEFT_SHOULDER: 11,
                RIGHT_SHOULDER: 12,
                LEFT_HIP: 23,
                RIGHT_HIP: 24,
            };
            console.log("MediaPipe Pose y DrawingUtils inicializados correctamente.");
        } catch (e) {
            console.error("ERROR: Fallo al inicializar MediaPipe Pose. La detección de pose visual no estará disponible.", e);
            pose = null; // Asegurarse de que pose sea null si falla la inicialización
        }
    } else {
        console.warn("ADVERTENCIA: MediaPipe Pose o DrawingUtils no están definidos globalmente. La funcionalidad de detección de pose visual no estará disponible.");
    }

    // --- Funciones de Utilidad Comunes ---
    function setVisibility(element, isVisible) {
        if (element) {
            element.style.display = isVisible ? 'block' : 'none';
        }
    }

    function stopCameraStream() {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        if (captureIntervalId) { // Detener cualquier intervalo de captura activo
            clearInterval(captureIntervalId);
            captureIntervalId = null;
        }
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
        }
        // NO LIMPIAR EL CANVAS AQUÍ. El canvas se limpiará al iniciar una nueva sesión.
    }

    function hideAllCameraUI() {
        setVisibility(cameraStream, false);
        setVisibility(cameraCanvas, false);
        setVisibility(cameraMessage, false);

        // Ocultar todos los botones de control
        setVisibility(capturePhotoButton, false);
        setVisibility(recapturePhotoButton, false);
        setVisibility(savePhotoButton, false);
        setVisibility(cancelPhotoButton, false);
        setVisibility(startBodyCaptureButton, false); // Ocultar el nuevo botón de captura
    }

    function showInitialButtons() {
        setVisibility(startCameraButton, true);
        setVisibility(detectBodyTypeButton, true);
    }

    // --- Lógica de Foto de Perfil ---

    // Configuración inicial de visibilidad para Foto de Perfil
    hideAllCameraUI(); // Ocultar todo al inicio
    showInitialButtons(); // Mostrar solo los botones de inicio

    // Event Listener para "Iniciar Cámara" (Foto de Perfil)
    if (startCameraButton) {
        startCameraButton.addEventListener('click', async function() {
            console.log('Botón "Iniciar Cámara" (Foto de Perfil) clickeado.');
            isBodyDetectionModeActive = false; // Desactivar modo detección de cuerpo
            stopCameraStream(); // Asegurarse de que no haya otro stream activo
            hideAllCameraUI(); // Ocultar todo antes de empezar

            // LIMPIAR EL CANVAS AL INICIAR UNA NUEVA SESIÓN DE CÁMARA
            if (cameraCanvas && context) {
                context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
            }

            try {
                currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraStream.srcObject = currentStream;

                await new Promise((resolve) => {
                    cameraStream.onloadedmetadata = () => {
                        cameraCanvas.width = cameraStream.videoWidth;
                        cameraCanvas.height = cameraStream.videoHeight;
                        resolve();
                    };
                });

                setVisibility(cameraStream, true);
                setVisibility(cameraCanvas, false); // Canvas oculto para foto de perfil (solo se muestra al capturar)
                setVisibility(startCameraButton, false);
                setVisibility(detectBodyTypeButton, false); // Ocultar el otro botón de inicio

                setVisibility(capturePhotoButton, true);
                setVisibility(cancelPhotoButton, true);

                cameraStream.play();
                console.log('Cámara iniciada para foto de perfil.');
            } catch (err) {
                console.error("ERROR al acceder a la cámara para foto de perfil:", err);
                alert("No se pudo acceder a la cámara. Asegúrate de que esté disponible y de que hayas dado permiso. Error: " + err.name);
                stopCameraStream();
                hideAllCameraUI();
                showInitialButtons();
            }
        });
    }

    // Event Listener para "Capturar Foto" (Foto de Perfil)
    if (capturePhotoButton) {
        capturePhotoButton.addEventListener('click', function() {
            console.log('Botón "Capturar Foto" clickeado (Modo Foto de Perfil).');
            // Asegurarse de que el canvas tenga el tamaño correcto antes de dibujar
            cameraCanvas.width = cameraStream.videoWidth;
            cameraCanvas.height = cameraStream.videoHeight;

            // Dibujar el frame actual del video en el canvas para la imagen estática
            context.save();
            context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height); // Limpiar antes de dibujar
            context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);
            context.restore();

            const imageDataURL = cameraCanvas.toDataURL('image/png');
            cameraPhotoDataInput.value = imageDataURL;
            console.log('Imagen de perfil capturada y guardada en campo oculto.');

            stopCameraStream(); // Detener el stream DESPUÉS de dibujar en el canvas

            setVisibility(cameraStream, false);
            setVisibility(cameraCanvas, true); // Mostrar el canvas con la imagen capturada

            setVisibility(capturePhotoButton, false);
            setVisibility(recapturePhotoButton, true);
            setVisibility(savePhotoButton, true);
            setVisibility(cancelPhotoButton, true);
        });
    }

    // Event Listener para "Volver a Capturar" (Foto de Perfil)
    if (recapturePhotoButton) {
        recapturePhotoButton.addEventListener('click', function() {
            console.log('Botón "Volver a Capturar" clickeado (Modo Foto de Perfil).');
            stopCameraStream();
            hideAllCameraUI();
            if (startCameraButton) startCameraButton.click(); // Simular clic en "Iniciar Cámara"
        });
    }

    // Event Listener para "Guardar Foto" (Foto de Perfil)
    if (savePhotoButton) {
        savePhotoButton.addEventListener('click', function() {
            console.log('Botón "Guardar Foto" clickeado (Modo Foto de Perfil).');
            alert("Foto de perfil lista para guardar. Envía el formulario principal para aplicar los cambios.");
        });
    }

    // Event Listener para "Cancelar" (Foto de Perfil)
    if (cancelPhotoButton) {
        cancelPhotoButton.addEventListener('click', function() {
            console.log('Botón "Cancelar" clickeado (Modo Foto de Perfil).');
            stopCameraStream();
            hideAllCameraUI();
            showInitialButtons();
        });
    }

    // --- Lógica de Detección de Cuerpo (CON BOTÓN DE CAPTURA) ---

    // Función de callback para MediaPipe (solo para detección de cuerpo)
    function onResultsBodyDetection(results) {
        if (isBodyDetectionModeActive && cameraStream.style.display === 'block' && cameraCanvas && context) {
            cameraCanvas.width = cameraStream.videoWidth;
            cameraCanvas.height = cameraStream.videoHeight;

            context.save();
            context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
            context.drawImage(results.image, 0, 0, cameraCanvas.width, cameraCanvas.height);

            // Solo dibujar si MediaPipe está inicializado y tiene resultados
            if (pose && mp_drawing && PoseLandmark && results.pose_landmarks) {
                const connections = [
                    [PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER],
                    [PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP]
                ];
                mp_drawing.drawConnectors(context, results.pose_landmarks, connections, {color: '#00FF00', lineWidth: 4});

                const relevantLandmarks = [
                    results.pose_landmarks[PoseLandmark.LEFT_SHOULDER],
                    results.pose_landmarks[PoseLandmark.RIGHT_SHOULDER],
                    results.pose_landmarks[PoseLandmark.LEFT_HIP],
                    results.pose_landmarks[PoseLandmark.RIGHT_HIP]
                ];
                mp_drawing.drawLandmarks(context, relevantLandmarks, {color: '#FF0000', lineWidth: 2});
            } else {
                console.warn("ADVERTENCIA: MediaPipe no está dibujando las líneas de pose. Asegúrate de que las bibliotecas estén cargadas y la inicialización fue exitosa.");
            }
            context.restore();
        }
    }

    // Bucle de animación para detección de cuerpo
    async function processBodyDetectionFrames() {
        if (!cameraStream.paused && !cameraStream.ended && isBodyDetectionModeActive && pose) {
            await pose.send({image: cameraStream});
        }
        animationFrameId = requestAnimationFrame(processBodyDetectionFrames);
    }

    // Event Listener para "Iniciar Detección de Tipo de Cuerpo" (solo inicia la cámara y visualización)
    if (detectBodyTypeButton) {
        detectBodyTypeButton.addEventListener('click', async function() {
            console.log('Botón "Iniciar Detección de Tipo de Cuerpo" clickeado (solo previsualización).');
            isBodyDetectionModeActive = true; // Activar modo detección de cuerpo
            stopCameraStream(); // Asegurarse de que no haya otro stream activo
            hideAllCameraUI(); // Ocultar todo antes de empezar

            // LIMPIAR EL CANVAS AL INICIAR UNA NUEVA SESIÓN DE CÁMARA
            if (cameraCanvas && context) {
                context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
            }

            try {
                currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraStream.srcObject = currentStream;

                await new Promise((resolve) => {
                    cameraStream.onloadedmetadata = () => {
                        cameraCanvas.width = cameraStream.videoWidth;
                        cameraCanvas.height = cameraStream.videoHeight;
                        resolve();
                    };
                });

                setVisibility(cameraStream, true);
                setVisibility(cameraCanvas, true); // Canvas visible para dibujar pose
                cameraMessage.textContent = 'Posiciónate para la medición. Haz clic en "Iniciar Captura" cuando estés listo.';
                setVisibility(cameraMessage, true); // Mostrar mensaje

                setVisibility(detectBodyTypeButton, false); // Ocultar este botón
                setVisibility(startCameraButton, false); // Ocultar el otro botón de inicio
                setVisibility(startBodyCaptureButton, true); // Mostrar el botón de iniciar captura
                setVisibility(cancelPhotoButton, true); // Mostrar el botón de cancelar

                cameraStream.play();
                // Solo iniciar el bucle de MediaPipe si pose está inicializado
                if (pose) {
                    processBodyDetectionFrames();
                } else {
                    console.warn("ADVERTENCIA: MediaPipe Pose no está inicializado. El video se mostrará, pero sin detección de pose visual.");
                }

            } catch (err) {
                console.error("ERROR al acceder a la cámara para detección de cuerpo:", err);
                alert("No se pudo acceder a la cámara. Asegúrate de que esté disponible y de que hayas dado permiso. Error: " + err.name);
                stopCameraStream();
                hideAllCameraUI();
                showInitialButtons();
            }
        });
    }

    // Event Listener para "Iniciar Captura de Medición" (inicia la secuencia de fotos)
    if (startBodyCaptureButton) {
        startBodyCaptureButton.addEventListener('click', function() {
            console.log('Botón "Iniciar Captura de Medición" clickeado.');
            setVisibility(startBodyCaptureButton, false); // Ocultar el botón de iniciar captura
            setVisibility(cancelPhotoButton, false); // Ocultar el botón de cancelar durante la captura
            captureTenBodyPhotos(); // Iniciar la secuencia de 10 fotos
        });
    }

    // Array para almacenar las fotos de medición capturadas
    let capturedMeasurementPhotos = [];
    const NUM_PHOTOS_TO_CAPTURE = 10;
    const CAPTURE_INTERVAL_MS = 1000; // 1 segundo entre fotos

    async function captureTenBodyPhotos() {
        capturedMeasurementPhotos = []; // Limpiar fotos anteriores
        let photoCount = 0;

        captureIntervalId = setInterval(() => { // Usar captureIntervalId
            if (photoCount < NUM_PHOTOS_TO_CAPTURE) {
                photoCount++;
                cameraMessage.textContent = `Tomando foto ${photoCount} de ${NUM_PHOTOS_TO_CAPTURE}...`;

                // Asegurarse de que el canvas tenga el tamaño correcto antes de dibujar
                cameraCanvas.width = cameraStream.videoWidth;
                cameraCanvas.height = cameraStream.videoHeight;

                // Dibujar el frame actual del video en el canvas
                context.save();
                context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height); // Limpiar antes de dibujar
                context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);

                // Si MediaPipe tiene resultados, dibujarlos encima
                // Es crucial usar pose.lastResults para asegurar que dibujamos los últimos resultados conocidos.
                if (pose && mp_drawing && PoseLandmark && pose.lastResults && pose.lastResults.pose_landmarks) {
                    const connections = [
                        [PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER],
                        [PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP]
                    ];
                    mp_drawing.drawConnectors(context, pose.lastResults.pose_landmarks, connections, {color: '#00FF00', lineWidth: 4});
                    const relevantLandmarks = [
                        pose.lastResults.pose_landmarks[PoseLandmark.LEFT_SHOULDER],
                        pose.lastResults.pose_landmarks[PoseLandmark.RIGHT_SHOULDER],
                        pose.lastResults.pose_landmarks[PoseLandmark.LEFT_HIP],
                        pose.lastResults.pose_landmarks[PoseLandmark.RIGHT_HIP]
                    ];
                    mp_drawing.drawLandmarks(context, relevantLandmarks, {color: '#FF0000', lineWidth: 2});
                } else {
                    console.warn(`ADVERTENCIA: MediaPipe no pudo dibujar en la foto ${photoCount}. Capturando la imagen sin líneas.`);
                }
                context.restore();

                const imageDataURL = cameraCanvas.toDataURL('image/png');
                capturedMeasurementPhotos.push(imageDataURL);
                console.log(`Foto de medición ${photoCount} capturada.`);

            } else {
                clearInterval(captureIntervalId); // Detener el intervalo
                captureIntervalId = null; // Resetear el ID
                console.log('Captura de 10 fotos de medición completada.');
                cameraMessage.textContent = 'Captura completada. Guardando datos...';

                // Almacenar todas las fotos capturadas como una cadena JSON en el input oculto
                measurementPhotoDataInput.value = JSON.stringify(capturedMeasurementPhotos);
                console.log('Todas las fotos de medición guardadas en el campo oculto.');

                // Detener cámara y resetear UI
                stopCameraStream();
                hideAllCameraUI();
                showInitialButtons(); // Mostrar los botones de inicio de nuevo
                alert("Se han tomado 10 fotos para la medición del cuerpo. Puedes guardar tu perfil ahora.");
            }
        }, CAPTURE_INTERVAL_MS);
    }

    // --- Configuración inicial al cargar la página ---
    hideAllCameraUI(); // Asegurarse de que todo esté oculto al principio
    showInitialButtons(); // Mostrar solo los botones de inicio
});
