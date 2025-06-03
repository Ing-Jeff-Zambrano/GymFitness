const cameraStream = document.getElementById('camera-stream');
  const cameraCanvas = document.getElementById('camera-canvas');
  const startCameraButton = document.getElementById('start-camera');
  const capturePhotoButton = document.getElementById('capture-photo');
  const detectBodyTypeButton = document.getElementById('detect-body-type');
  const uploadFile = document.getElementById('upload-file');
  const context = cameraCanvas.getContext('2d');
  let stream;
  let capturedImagesForBodyType = [];
  const numberOfCaptures = 10;
  let captureCounter = 0;

  startCameraButton.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      cameraStream.srcObject = stream;
      cameraStream.style.display = 'block';
      capturePhotoButton.style.display = 'inline-block';
      startCameraButton.style.display = 'none';
      detectBodyTypeButton.style.display = 'none'; // Ocultar detección al usar captura de foto de perfil
    } catch (err) {
      console.error("Error accessing camera: ", err);
      alert("No se pudo acceder a la cámara.");
    }
  });

  capturePhotoButton.addEventListener('click', () => {
    context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);
    const imageDataURL = cameraCanvas.toDataURL('image/png');

    const cameraPhotoInput = document.createElement('input');
    cameraPhotoInput.setAttribute('type', 'hidden');
    cameraPhotoInput.setAttribute('name', 'camera_photo_data');
    cameraPhotoInput.setAttribute('value', imageDataURL);

    const profileForm = document.querySelector('form');
    profileForm.appendChild(cameraPhotoInput);

    cameraStream.style.display = 'none';
    capturePhotoButton.style.display = 'none';
    startCameraButton.style.display = 'block';
    detectBodyTypeButton.style.display = 'block'; // Mostrar detección de nuevo
    alert('Foto de perfil capturada. Ahora puedes guardar tu perfil.');
  });

  detectBodyTypeButton.addEventListener('click', async () => {
    capturedImagesForBodyType = [];
    captureCounter = 0;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      cameraStream.srcObject = stream;
      cameraStream.style.display = 'block';
      startCameraButton.style.display = 'none';
      capturePhotoButton.style.display = 'none';
      detectBodyTypeButton.style.display = 'none';
      alert(`Iniciando captura de ${numberOfCaptures} fotos para detección de tipo de cuerpo...`);

      const captureInterval = setInterval(() => {
        context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);
        const imageDataURL = cameraCanvas.toDataURL('image/png');
        capturedImagesForBodyType.push(imageDataURL);
        captureCounter++;
        console.log(`Foto ${captureCounter} para tipo de cuerpo capturada.`);

        if (captureCounter >= numberOfCaptures) {
          clearInterval(captureInterval);
          cameraStream.style.display = 'none';
          alert(`${numberOfCaptures} fotos capturadas para análisis de tipo de cuerpo. Ahora puedes guardar tu perfil.`);
          startCameraButton.style.display = 'block';
          detectBodyTypeButton.style.display = 'block';

          // Añadir campos ocultos al formulario con las imageDataURL
          const profileForm = document.querySelector('form');
          capturedImagesForBodyType.forEach((imageData, index) => {
            const input = document.createElement('input');
            input.setAttribute('type', 'hidden');
            input.setAttribute('name', `body_photo_${index + 1}`);
            input.setAttribute('value', imageData);
            profileForm.appendChild(input);
          });
          capturedImagesForBodyType = []; // Limpiar el array después de añadir al formulario
        }
      }, 1000); // Captura cada 1 segundo

    } catch (err) {
      console.error("Error accessing camera: ", err);
      alert("No se pudo acceder a la cámara para la detección de tipo de cuerpo.");
      startCameraButton.style.display = 'block';
      detectBodyTypeButton.style.display = 'block';
    }
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  uploadFile.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
      console.log("Archivo seleccionado:", file);
    }
  });