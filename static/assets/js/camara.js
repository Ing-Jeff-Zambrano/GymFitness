document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM completamente cargado. Inicializando script de cámara.');

    // Obtener referencias a los elementos HTML por su ID
    const startCameraButton = document.getElementById('start-camera');
    const capturePhotoButton = document.getElementById('capture-photo');
    const recapturePhotoButton = document.getElementById('recapture-photo'); // Botón "Volver a Capturar"
    const savePhotoButton = document.getElementById('save-photo');         // Botón "Guardar Foto"
    const cancelPhotoButton = document.getElementById('cancel-photo');     // Botón "Cancelar"
    const cameraStream = document.getElementById('camera-stream');         // Elemento <video> para la transmisión de la cámara
    const cameraCanvas = document.getElementById('camera-canvas');         // Elemento <canvas> para la captura de la foto
    const cameraPhotoDataInput = document.getElementById('camera-photo-data'); // Campo oculto para almacenar la imagen en base64
    const context = cameraCanvas.getContext('2d'); // Contexto 2D del canvas para dibujar la imagen

    // Verificar si todos los elementos se encontraron correctamente en el DOM
    // Si alguno de estos es 'null', significa que el ID en el HTML no coincide o el elemento no existe.
    console.log('Elementos HTML encontrados:');
    console.log('startCameraButton:', startCameraButton);
    console.log('capturePhotoButton:', capturePhotoButton);
    console.log('recapturePhotoButton:', recapturePhotoButton);
    console.log('savePhotoButton:', savePhotoButton);
    console.log('cancelPhotoButton:', cancelPhotoButton);
    console.log('cameraStream:', cameraStream);
    console.log('cameraCanvas:', cameraCanvas);
    console.log('cameraPhotoDataInput:', cameraPhotoDataInput);


    let stream; // Variable para almacenar el MediaStream de la cámara

    // Función auxiliar para controlar la visibilidad de los elementos
    function setVisibility(element, isVisible) {
        if (element) { // Asegurarse de que el elemento exista antes de intentar modificar su estilo
            element.style.display = isVisible ? 'block' : 'none';
            console.log(`Visibilidad de ${element.id} establecida a: ${isVisible ? 'visible' : 'oculto'}`);
        } else {
            console.warn(`Intento de establecer visibilidad en un elemento nulo (ID no encontrado).`);
        }
    }

    // --- Configuración inicial de la visibilidad de los botones al cargar la página ---
    setVisibility(recapturePhotoButton, false); // Ocultar "Volver a Capturar"
    setVisibility(savePhotoButton, false);     // Ocultar "Guardar Foto"
    setVisibility(cancelPhotoButton, false);    // Ocultar "Cancelar"
    setVisibility(capturePhotoButton, false);   // Ocultar "Capturar Foto" (solo se muestra al iniciar cámara)

    // --- Event Listener para el botón "Iniciar Cámara" ---
    startCameraButton.addEventListener('click', async function() {
        console.log('Botón "Iniciar Cámara" clickeado.');
        try {
            // Solicitar acceso a la cámara de video del usuario
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            cameraStream.srcObject = stream; // Asignar el stream al elemento <video>

            // Actualizar la visibilidad de los elementos
            setVisibility(cameraStream, true);      // Mostrar la transmisión de la cámara
            setVisibility(cameraCanvas, false);     // Asegurarse de que el canvas esté oculto
            setVisibility(startCameraButton, false); // Ocultar "Iniciar Cámara"
            setVisibility(capturePhotoButton, true); // Mostrar "Capturar Foto"
            setVisibility(recapturePhotoButton, false); // Asegurarse de que esté oculto
            setVisibility(savePhotoButton, false);      // Asegurarse de que esté oculto
            setVisibility(cancelPhotoButton, true);     // Mostrar "Cancelar"
            console.log('Cámara iniciada exitosamente.');
        } catch (err) {
            console.error("Error al acceder a la cámara: ", err);
            alert("No se pudo acceder a la cámara. Asegúrate de que esté disponible y de que hayas dado permiso.");
        }
    });

    // --- Event Listener para el botón "Capturar Foto" ---
    capturePhotoButton.addEventListener('click', function() {
        console.log('Botón "Capturar Foto" clickeado.');
        // Configurar el tamaño del canvas para que coincida con la resolución del video
        cameraCanvas.width = cameraStream.videoWidth;
        cameraCanvas.height = cameraStream.videoHeight;

        // Dibujar el frame actual del video en el canvas
        context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);
        // Obtener la imagen del canvas en formato Data URL (Base64)
        const imageDataURL = cameraCanvas.toDataURL('image/png');
        cameraPhotoDataInput.value = imageDataURL; // Guardar la imagen en el campo oculto del formulario
        console.log('Imagen capturada y guardada en campo oculto.');

        // Detener el stream de la cámara para liberar los recursos
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            console.log('Stream de cámara detenido.');
        }

        // Actualizar la visibilidad de los elementos
        setVisibility(cameraStream, false);      // Ocultar la transmisión de la cámara
        setVisibility(cameraCanvas, true);       // Mostrar la imagen capturada en el canvas
        setVisibility(capturePhotoButton, false); // Ocultar "Capturar Foto"
        setVisibility(recapturePhotoButton, true); // Mostrar "Volver a Capturar"
        setVisibility(savePhotoButton, true);     // Mostrar "Guardar Foto"
        setVisibility(cancelPhotoButton, true);    // Mostrar "Cancelar"
        console.log('Visibilidad de botones actualizada después de capturar.');
    });

    // --- Event Listener para el botón "Volver a Capturar" ---
    recapturePhotoButton.addEventListener('click', async function() {
        console.log('Botón "Volver a Capturar" clickeado.');
        // Limpiar el canvas y el campo oculto
        context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
        cameraPhotoDataInput.value = '';

        // Reiniciar el stream de la cámara
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            cameraStream.srcObject = stream;
            setVisibility(cameraStream, true);      // Mostrar la transmisión de la cámara
            setVisibility(cameraCanvas, false);     // Ocultar el canvas
            setVisibility(recapturePhotoButton, false); // Ocultar "Volver a Capturar"
            setVisibility(savePhotoButton, false);      // Ocultar "Guardar Foto"
            setVisibility(capturePhotoButton, true);    // Mostrar "Capturar Foto"
            setVisibility(cancelPhotoButton, true);     // Mostrar "Cancelar"
            console.log('Cámara reiniciada.');
        } catch (err) {
            console.error("Error al reiniciar la cámara: ", err);
            alert("No se pudo reiniciar la cámara.");
        }
    });

    // --- Event Listener para el botón "Guardar Foto" ---
    savePhotoButton.addEventListener('click', function() {
        console.log('Botón "Guardar Foto" clickeado.');
        // Este botón solo confirma que la foto está lista en el campo oculto.
        // El guardado real en el servidor ocurre cuando el formulario principal se envía.
        alert("Foto lista para guardar. Envía el formulario principal (botón 'Guardar Perfil') para aplicar los cambios.");
    });

    // --- Event Listener para el botón "Cancelar" ---
    cancelPhotoButton.addEventListener('click', function() {
        console.log('Botón "Cancelar" clickeado.');
        // Detener el stream de la cámara si está activo
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        // Limpiar el canvas y el campo oculto
        context.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
        cameraPhotoDataInput.value = '';

        // Ocultar todos los elementos de la cámara y mostrar solo el botón "Iniciar Cámara"
        setVisibility(cameraStream, false);
        setVisibility(cameraCanvas, false);
        setVisibility(startCameraButton, true);
        setVisibility(capturePhotoButton, false);
        setVisibility(recapturePhotoButton, false);
        setVisibility(savePhotoButton, false);
        setVisibility(cancelPhotoButton, false);
        console.log('Proceso de cámara cancelado.');
    });
});

