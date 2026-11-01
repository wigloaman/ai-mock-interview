$(document).ready(function () {

    // Check if device is IOS
    function isIOS() {
        var ua = navigator.userAgent;
        // Checks for iPhone and iPod
        var isIOSDevice = /iPad|iPhone|iPod/.test(ua);
        // Special case for iPads with iPadOS 13 and later that use a desktop user agent
        if (!isIOSDevice && navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) {
            isIOSDevice = true;
        }
        return isIOSDevice;
    }

    function isMobile() {
        // Regular expression to detect common mobile device user agents
        var mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
        return mobileRegex.test(navigator.userAgent);
    }

    // Function to add a message to the chat box
    function addMessage(message, incoming) {
        const messageClass = incoming ? "incoming" : "outgoing";
        const messageDiv = `<div class="message ${messageClass}">${message}</div>`;
        $("#chat-box").append(messageDiv);
    }

    // Declaring variables
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const menuBtn = document.getElementById('menuBtn');
    const sendBtnsmall = document.getElementById('sendBtnsmall');
    const voiceInputIcon = document.getElementById('voice-input-icon');
    const chatBox = document.getElementById('chat-box');

    // To send message when enter is clicked
    messageInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevents the default behavior of the Enter key (e.g., new line in a textarea)
            sendButton.click(); // Trigger a click event on the send button
        }
    });

    // Function to get the next question from Django
    function getNextQuestion() {
        $.ajax({
            url: "/get_question/",
            type: "GET",
            dataType: "json",
            success: function (data) {
                if (data.question) {
                    addMessage(data.question, true);
                    chatBox.scrollTop = chatBox.scrollHeight;
                    speakText(data.question);
                    sendButton.disabled = false;
                    if (data.auto_answer) {
                        getAutoAnswer();
                    }
                } else {
                    addMessage("No more questions.", true);
                    addMessage("You will be redirected to the result page.", true);
                    window.location.href = data.redirect;
                }
            },
            error: function (error) {
                console.error(error);
            },
        });
    }

    //Function to auto answer the question from gpt
    function getAutoAnswer() {
        $.ajax({
            url: "/get-answer-automatically/",
            type: "GET",
            dataType: "json",
            success: function (data) {
                if (data.success) {
                    const userAnswerValue = data.answer
                    $("#message-input").val(userAnswerValue);
                    $("#send-button").trigger("click");
                } else {
                    console.error("Failed to get answer automatically.");
                }
            },
            error: function (error) {
                console.error(error);
            },
        });
    }

    // Initialize the chat with the first question
    getNextQuestion();

    // Handle user input and submission
    $("#send-button").click(function () {
        var userAnswer = $("#message-input").val();
        userAnswer = userAnswer.replace(/{|}|"|'/g, '');
        if (userAnswer.trim() !== "") {
            $("#message-input").val("");
            sendButton.disabled = true;
            addMessage(userAnswer, false);
            chatBox.scrollTop = chatBox.scrollHeight;
            if (window.matchMedia("(max-width: 768px)").matches) {
                voiceInputIcon.style.display = 'inline-block';
                menuBtn.style.display = 'inline-block';
                sendBtnsmall.style.display = 'inline-block';
            }
            // Send the user's answer to Django for processing and update the database
            $.ajax({
                url: "/save-answer/",
                type: "POST",
                dataType: "json",
                data: {
                    answer: userAnswer,
                },
                headers: {
                    "X-CSRFToken": csrfToken,
                },
                success: function (data) {
                    if (data.success) {
                        getNextQuestion();
                    } else {
                        sendButton.disabled = false;
                        alert("Failed to save answer.");
                    }
                },
                error: function (error) {
                    sendButton.disabled = false;
                    console.error(error);
                },
            });
        }
    });

    //Add video element and it's functionalities
    function setupVideo() {

        const personBox = document.getElementById('candidate-box');
        const personName = document.getElementById('candidate-name');
        const videoContainer = document.getElementById('videoContainer');
        const videoElement = document.getElementById('videoElement');

        personBox.addEventListener('mouseenter', () => {
            disableVideoButton.style.display = 'block';
            enableVideoButton.style.display = 'block';
        });

        personBox.addEventListener('mouseleave', () => {
            disableVideoButton.style.display = 'none';
            enableVideoButton.style.display = 'none';
        });

        disableVideoButton.addEventListener('click', async () => {
            const videoElement = document.getElementById('videoElement');

            if (videoElement.srcObject) {
                const tracks = videoElement.srcObject.getTracks();

                // Suspend the video element to try to stop the camera feed
                videoElement.pause();

                // Stop each track and wait for the promises to resolve
                await Promise.all(tracks.map(track => track.stop()));

                // Set srcObject to null after stopping the tracks
                videoElement.srcObject = null;
                videoContainer.style.display = 'none'; // Hide the video container
                personName.style.display = 'flex'; // Show the person's name
            }
        });

        enableVideoButton.addEventListener('click', () => {
            handleVideoPermission();
        });

        function handleVideoPermission() {
            navigator.mediaDevices.getUserMedia({ video: true }).then(() => {
                // If permission is granted, display the video
                personName.style.display = 'none';
                videoContainer.style.display = 'block';
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then((stream) => {
                        videoElement.srcObject = stream;
                        videoElement.style.transform = 'scaleX(-1)';
                    })
                    .catch((error) => {
                        alert("Camera permission is not granted. Please grant it to enable video.");
                    });
            })
                .catch(() => {
                    // If permission is not granted, display the person's name
                    alert("Camera permission is not granted. Please grant it to enable video.");
                    personName.style.display = 'flex';
                    videoContainer.style.display = 'none';
                });
        }

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            handleVideoPermission();
        } else {
            alert('Sorry, camera access is not supported in this browser.');
        }
    }

    // Only ask for camera permission when video box is visible
    if (window.innerWidth >= 992) {
        setupVideo();
    }


    //Display menu in interview
    document.getElementById('menuBtn').addEventListener('click', function () {
        var menu = document.querySelector('.interview-menu-expand');
        menu.classList.toggle('show');
    });

    document.addEventListener('click', function (event) {
        var menu = document.querySelector('.interview-menu-expand');
        if (menu.classList.contains('show') && event.target.closest('.interview-menu') === null) {
            menu.classList.remove('show');
        }
    });

    //Add voice input in interface

    let recognition;

    // Function to start voice recognition
    function startRecognition() {
        recognition = new webkitSpeechRecognition(); // Create a new instance
        recognition.lang = 'en-US'; // Set the language
        recognition.onerror = function (event) {
            if (isIOS()) {
                alert("Microphone may not be fully supported on iOS devices. Please use your keyboard microphone instead.");
            }
            else {
                if (isMobile()) {
                    alert("Microphone may not be fully supported on your device. Please use your keyboard microphone instead.");
                }
                else {
                    alert("Microphone may not be fully supported on your device.");
                }
            }
        };
        recognition.onresult = function (event) {

            const transcript = event.results[0][0].transcript;
            messageInput.value += transcript + ' '; // Append recognized text
        };

        recognition.onend = function () {
            recognition.stop();
            startRecognition(); // Restart recognition on end (continuous listening)
        };

        recognition.start(); // Start listening
    }

    // Toggle voice recognition on icon click
    var micMessage = document.getElementById('mic-message');
    voiceInputIcon.addEventListener('click', function () {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then((stream) => {
                if (!recognition) {
                    voiceInputIcon.classList.remove('fa-microphone-slash');
                    voiceInputIcon.classList.add('fa-microphone');
                    micMessage.textContent = 'Mic Enabled. Start speaking';
                    micMessage.style.display = 'block';
                    startRecognition();
                } else {
                    voiceInputIcon.classList.remove('fa-microphone');
                    voiceInputIcon.classList.add('fa-microphone-slash');
                    micMessage.textContent = 'Mic Disabled';
                    micMessage.style.display = 'block';
                    recognition.stop();
                    recognition = undefined;
                }
                setTimeout(function () {
                    micMessage.style.display = 'none';
                }, 2000);
            })
            .catch((error) => {
                alert("Microphone permission is not granted. Please grant it to start speaking.");
            });
    });

    let currentlyPlayingAudio = null;
    // AWS text to speech
    function speakText(text) {
        if (currentlyPlayingAudio) {
            currentlyPlayingAudio.pause();
            currentlyPlayingAudio.currentTime = 0; // Reset the playback to the beginning
            currentlyPlayingAudio = null;
        }
        fetch('/speak_text/?text=' + encodeURIComponent(text))
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                } else {
                    const audioUrl = 'data:audio/mpeg;base64,' + data.audio_data;
                    const audio = new Audio(audioUrl);
                    audio.play();
                    currentlyPlayingAudio = audio;

                    const personBox = document.querySelector('.person-name');
                    audio.addEventListener('play', () => {
                        personBox.classList.add('speaking');
                    });

                    audio.addEventListener('ended', () => {
                        personBox.classList.remove('speaking');
                    });
                }
            });
    }

    // Expand textarea on smaller screens
    if (window.matchMedia("(max-width: 768px)").matches) {
        messageInput.addEventListener('input', function () {
            if (this.value.trim().length > 0) {
                if (!recognition) {
                    voiceInputIcon.style.display = 'none';
                }
                menuBtn.style.display = 'none';
                sendBtnsmall.style.display = 'none'
            } else {
                if (!recognition) {
                    voiceInputIcon.style.display = 'inline-block';
                }
                menuBtn.style.display = 'inline-block';
                sendBtnsmall.style.display = 'inline-block';
            }
        });
    }
});