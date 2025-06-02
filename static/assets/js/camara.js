const cameraStream = document.getElementById('camera-stream');
  const cameraCanvas = document.getElementById('camera-canvas');
  const startCameraButton = document.getElementById('start-camera');
  const capturePhotoButton = document.getElementById('capture-photo');
  const uploadFile = document.getElementById('upload-file'); // Lo mantenemos por si acaso
  const context = cameraCanvas.getContext('2d');
  let stream;

  startCameraButton.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      cameraStream.srcObject = stream;
      cameraStream.style.display = 'block';
      capturePhotoButton.style.display = 'inline-block';
      startCameraButton.style.display = 'none';
    } catch (err) {
      console.error("Error accessing camera: ", err);
      alert("No se pudo acceder a la cámara.");
    }
  });

  capturePhotoButton.addEventListener('click', () => {
    context.drawImage(cameraStream, 0, 0, cameraCanvas.width, cameraCanvas.height);
    const imageDataURL = cameraCanvas.toDataURL('image/png');

    // Crear un campo oculto en el formulario principal para enviar la imageDataURL
    const cameraPhotoInput = document.createElement('input');
    cameraPhotoInput.setAttribute('type', 'hidden');
    cameraPhotoInput.setAttribute('name', 'camera_photo_data');
    cameraPhotoInput.setAttribute('value', imageDataURL);

    const profileForm = document.querySelector('form'); // Selecciona el formulario principal
    profileForm.appendChild(cameraPhotoInput);

    // Ocultar la vista de la cámara
    cameraStream.style.display = 'none';
    capturePhotoButton.style.display = 'none';
    startCameraButton.style.display = 'block';
    alert('Foto capturada. Ahora puedes guardar tu perfil.'); // Informar al usuario
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