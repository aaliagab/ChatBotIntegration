var wavesurfer;
var recorder;

function speakText(text, lang = 'es-ES') {
    if (!wavesurfer) {
        wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: 'violet',
            progressColor: 'purple',
            height: 100,
            barWidth: 2,
            cursorWidth: 1,
            cursorColor: '#333',
            backend: 'MediaElement'
        });
    }

    var synth = window.speechSynthesis;
    var utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;

    // Setup recorder
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        recorder = new RecordRTC(stream, {
            type: 'audio',
            mimeType: 'audio/wav',
            recorderType: RecordRTC.StereoAudioRecorder,
            desiredSampRate: 16000
        });

        utterance.onstart = function() {
            recorder.startRecording();
        };

        utterance.onend = function() {
            recorder.stopRecording(() => {
                var blob = recorder.getBlob();
                var audioURL = URL.createObjectURL(blob);
                wavesurfer.load(audioURL);
                document.getElementById('voice-player').style.display = 'block';
            });
        };

        synth.speak(utterance);
    }).catch(error => console.error('Error accessing media devices.', error));
}

function toggleVoiceMode() {
    var voiceCheckbox = document.getElementById('voice-checkbox');
    var recordButton = document.getElementById('record-button');
    var messageInput = document.getElementById('message-input');
    if (voiceCheckbox.checked) {
        recordButton.style.display = 'block';
        messageInput.style.display = 'none';
    } else {
        recordButton.style.display = 'none';
        messageInput.style.display = 'block';
    }
}

function recordVoiceMessage() {
    var recordButton = document.getElementById('record-button');
    recordButton.textContent = 'Grabando voz...';
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        recorder = new RecordRTC(stream, {
            type: 'audio',
            mimeType: 'audio/wav',
            recorderType: RecordRTC.StereoAudioRecorder,
            desiredSampRate: 16000
        });

        recorder.startRecording();

        setTimeout(() => {
            recorder.stopRecording(() => {
                var blob = recorder.getBlob();
                var formData = new FormData();
                formData.append('audio', blob, 'voice_message.wav');

                fetch('/transcribe_audio', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Network response was not ok " + response.statusText);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.transcription) {
                        document.getElementById('message-input').value = data.transcription;
                        sendMessage();
                    } else {
                        displayMessage('Bot', 'Ocurrió un error al transcribir el audio. Por favor, intenta de nuevo.');
                    }
                })
                .catch(error => console.error('Error:', error))
                .finally(() => {
                    recordButton.textContent = 'Grabar Mensaje';
                });
            });
        }, 5000);  // Grabar durante 5 segundos
    }).catch(error => {
        console.error('Error accessing media devices.', error);
        recordButton.textContent = 'Grabar Mensaje';
    });
}


function toggleVoicePlayer() {
    var voiceCheckbox = document.getElementById('voice-checkbox');
    var voicePlayer = document.getElementById('voice-player');
    if (voiceCheckbox.checked) {
        voicePlayer.style.display = 'block';
    } else {
        voicePlayer.style.display = 'none';
        if (wavesurfer) {
            wavesurfer.stop();
        }
    }
}

function togglePlay() {
    if (wavesurfer) {
        wavesurfer.playPause();
    }
}

function openWebcamModal() {
    var modal = document.getElementById('webcam-modal');
    modal.style.display = 'block';
    startWebcam();
}

function closeWebcamModal() {
    var modal = document.getElementById('webcam-modal');
    modal.style.display = 'none';
    stopWebcam();
}

function startWebcam() {
    var video = document.getElementById('webcam');
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
            video.srcObject = stream;
        })
        .catch(function (err) {
            console.log("Error: " + err);
        });

    startCountdown(5);
}

function stopWebcam() {
    var video = document.getElementById('webcam');
    var stream = video.srcObject;
    if (stream) {
        var tracks = stream.getTracks();
        tracks.forEach(function (track) {
            track.stop();
        });
        video.srcObject = null;
    }
}

function startCountdown(seconds) {
    var countdownElement = document.getElementById('countdown');
    countdownElement.style.display = 'block';
    var count = seconds;

    var countdownInterval = setInterval(function() {
        countdownElement.textContent = count;
        count--;

        if (count < 0) {
            clearInterval(countdownInterval);
            countdownElement.style.display = 'none';
            captureImage();
        }
    }, 1000);
}

function captureImage() {
    var video = document.getElementById('webcam');
    var canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(function (blob) {
        var formData = new FormData();
        formData.append('image', blob, 'webcam_image.png');

        // Añadir el mensaje de texto del campo de entrada al formulario
        var messageInput = document.getElementById('message-input'); // Asegúrate de que este elemento esté definido
        var messageText = messageInput.value;
        formData.append('message', messageText);

        // Mostrar la miniatura de la imagen capturada en el chat
        var imageUrl = URL.createObjectURL(blob);
        displayImage('You', imageUrl);
        displayMessage('You', messageText);  // Mostrar el mensaje de texto en el chat

        fetch('/chat', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok " + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("Received response:", data);
            if (data.response) {
                displayMessage('Bot', data.response);
                if (data.recommended_image_url) {
                    console.log("Recommended image URL:", data.recommended_image_url);
                    displayImage('Bot', data.recommended_image_url); // Muestra la miniatura de la imagen recomendada
                }
                // Si el checkbox de voz está marcado, reproducir la voz del bot
                var voiceCheckbox = document.getElementById('voice-checkbox');
                if (voiceCheckbox.checked) {
                    speakText(data.response, 'es-ES');
                }
            } else {
                displayMessage('Bot', 'Ocurrió un error. Por favor, intenta de nuevo.');
            }
        })
        .catch(error => console.error('Error:', error));
    }, 'image/png');

    // Detener la transmisión de video
    stopWebcam();

    // Ocultar el modal de la webcam
    closeWebcamModal();

    // Limpiar el campo de entrada de mensaje después de enviar el mensaje
    document.getElementById('message-input').value = '';
}

function sendMessage() {
    var messageInput = document.getElementById('message-input');
    var imageUpload = document.getElementById('image-upload');

    var formData = new FormData();
    formData.append('message', messageInput.value);
    if (imageUpload.files[0]) {
        formData.append('image', imageUpload.files[0]);
    }

    displayMessage('You', messageInput.value); // Muestra el mensaje del usuario inmediatamente
    if (imageUpload.files[0]) {
        displayImage('You', URL.createObjectURL(imageUpload.files[0])); // Muestra la miniatura de la imagen subida por el usuario
    }

    fetch('/chat', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok " + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log("Received response:", data);
        if (data.response) {
            displayMessage('Bot', data.response);
            if (data.recommended_image_url) {
                console.log("Recommended image URL:", data.recommended_image_url);
                displayImage('Bot', data.recommended_image_url); // Muestra la miniatura de la imagen recomendada
            }
            // Si el checkbox de voz está marcado, reproducir la voz del bot
            var voiceCheckbox = document.getElementById('voice-checkbox');
            if (voiceCheckbox.checked) {
                speakText(data.response, 'es-ES');
            }
        } else {
            displayMessage('Bot', 'Ocurrió un error. Por favor, intenta de nuevo.');
        }

        // Limpiar los campos de entrada después de enviar el mensaje
        messageInput.value = '';
        imageUpload.value = '';

    })
    .catch(error => console.error('Error:', error));
}

function sendImageUrl() {
    var imageUrlInput = document.getElementById('image-url');
    var messageInput = document.getElementById('message-input');

    displayMessage('You', messageInput.value); // Muestra el mensaje del usuario inmediatamente
    displayImage('You', imageUrlInput.value); // Muestra la imagen de la URL en el chat

    // Descargar la imagen desde la URL y enviarla como un blob
    fetch(imageUrlInput.value)
        .then(response => response.blob())
        .then(blob => {
            var formData = new FormData();
            formData.append('image', blob, 'image_from_url.png');
            formData.append('message', messageInput.value);

            return fetch('/chat', {
                method: 'POST',
                body: formData
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok " + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("Received response:", data);
            if (data.response) {
                displayMessage('Bot', data.response);
                if (data.recommended_image_url) {
                    console.log("Recommended image URL:", data.recommended_image_url);
                    displayImage('Bot', data.recommended_image_url); // Muestra la miniatura de la imagen recomendada
                }
                // Si el checkbox de voz está marcado, reproducir la voz del bot
                var voiceCheckbox = document.getElementById('voice-checkbox');
                if (voiceCheckbox.checked) {
                    speakText(data.response, 'es-ES');
                }
            } else {
                displayMessage('Bot', 'Ocurrió un error. Por favor, intenta de nuevo.');
            }

            // Limpiar los campos de entrada después de enviar el mensaje
            imageUrlInput.value = '';
            messageInput.value = '';
        })
        .catch(error => console.error('Error:', error));
}

function displayMessage(sender, message) {
    var chatHistory = document.getElementById('chat-history');
    var messageElement = document.createElement('div');
    messageElement.classList.add('message');
    
    var senderElement = document.createElement('strong');
    senderElement.textContent = sender + ': ';
    messageElement.appendChild(senderElement);
    
    var textElement = document.createElement('span');
    textElement.textContent = message;
    messageElement.appendChild(textElement);
    
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function displayImage(sender, imageUrl) {
    var chatHistory = document.getElementById('chat-history');
    var messageElement = document.createElement('div');
    messageElement.classList.add('message');
    
    var senderElement = document.createElement('strong');
    senderElement.textContent = sender + ': ';
    messageElement.appendChild(senderElement);
    
    var imageElement = document.createElement('img');
    imageElement.src = imageUrl;
    imageElement.style.width = '80px';  // Ajusta el tamaño de la miniatura
    imageElement.style.height = '80px'; // Ajusta el tamaño de la miniatura
    messageElement.appendChild(imageElement);
    
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
