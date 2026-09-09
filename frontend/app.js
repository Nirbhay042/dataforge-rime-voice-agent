// ===============================
// DATAFORGE - VOICE AGENT
// Streaming + Full Duplex + Interruption
// ===============================

const API_BASE = "http://127.0.0.1:8000";

// ===============================
// DOM ELEMENTS
// ===============================

const voiceOrb = document.getElementById("voiceOrb");
const orbStatus = document.getElementById("orbStatus");
const orbSubtitle = document.getElementById("orbSubtitle");

const micButton = document.getElementById("micButton");
const stopButton = document.getElementById("stopButton");

const userText = document.getElementById("userText");
const agentText = document.getElementById("agentText");
const sessionTime = document.getElementById("sessionTime");

// ===============================
// STATE
// ===============================

let recognition = null;

let isListening = false;
let isProcessing = false;
let isSpeaking = false;

let manuallyStopped = false;

let currentAudio = null;

// IMPORTANT:
// Resolves the currently playing Rime
// promise when interrupted
let currentAudioFinish = null;

let interruptionActive = false;

let finalTranscript = "";
let interimTranscript = "";

let lastSentText = "";

let requestVersion = 0;

let conversationId =
    "dataforge-" +
    Date.now() +
    "-" +
    Math.random().toString(36).substring(2, 8);

// ===============================
// STREAMING / AUDIO STATE
// ===============================

let currentAgentResponse = "";

let ttsBuffer = "";

let audioQueue = [];

let isPlayingQueue = false;

let currentlySpeakingText = "";

// ===============================
// SESSION TIMER
// ===============================

let sessionSeconds = 0;

setInterval(() => {
    sessionSeconds++;

    const minutes =
        Math.floor(sessionSeconds / 60);

    const seconds =
        sessionSeconds % 60;

    if (sessionTime) {
        sessionTime.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }
}, 1000);

// ===============================
// SPEECH RECOGNITION
// ===============================

function setupRecognition() {
    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert(
            "Speech Recognition is not supported in this browser. Please use Google Chrome."
        );

        return;
    }

    recognition = new SpeechRecognition();

    recognition.continuous = true;

    recognition.interimResults = true;

    recognition.lang = "en-US";

    // ===========================
    // SPEECH START
    // ===========================

    recognition.onstart = () => {
        isListening = true;

        console.log(
            "🎤 Speech recognition started"
        );

        setListeningState();
    };

    // ===========================
    // SPEECH RESULT
    // ===========================

    recognition.onresult = (event) => {
        let interim = "";
        let finalText = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {
            const transcript =
                event.results[i][0].transcript;

            if (
                event.results[i].isFinal
            ) {
                finalText +=
                    transcript + " ";
            } else {
                interim += transcript;
            }
        }

        interimTranscript = interim;

        // ==========================================
        // POSSIBLE ECHO
        // ==========================================

        const detectedText =
            (
                interim +
                " " +
                finalText
            ).trim();

        const looksLikeEcho =
            isSpeaking &&
            detectedText.length > 0 &&
            isLikelyEcho(detectedText);

        // ==========================================
        // USER INTERRUPTS AI
        // ==========================================

        if (
            isSpeaking &&
            !interruptionActive &&
            detectedText.length > 0 &&
            !looksLikeEcho
        ) {
            console.log(
                "🛑 USER INTERRUPTED AI"
            );

            // Mark interruption
            interruptionActive = true;

            // Invalidate old request
            requestVersion++;

            // Stop current Rime audio
            stopAudio();

            // Clear pending audio
            audioQueue = [];

            ttsBuffer = "";

            // Unlock audio queue
            isPlayingQueue = false;

            currentlySpeakingText = "";

            // Reset state
            isSpeaking = false;
            isProcessing = false;

            // User gets priority
            setListeningState();
        }

        // ==========================================
        // UPDATE USER TEXT
        // ==========================================

        if (userText) {
            if (finalText.trim()) {
                userText.textContent =
                    finalText.trim();
            } else if (interim.trim()) {
                userText.textContent =
                    interim.trim();
            }
        }

        // ==========================================
        // FINAL USER COMMAND
        // ==========================================

        if (finalText.trim()) {
            // Reset interruption state
            // for the new request
            interruptionActive = false;

            const command =
                finalText.trim();

            finalTranscript +=
                command + " ";

            console.log(
                "🗣️ Final command:",
                command
            );

            // Prevent duplicate command
            if (
                command.toLowerCase() !==
                lastSentText.toLowerCase()
            ) {
                lastSentText =
                    command;

                sendInstruction(
                    command
                );
            }
        }
    };

    // ===========================
    // SPEECH END
    // ===========================

    recognition.onend = () => {
        console.log(
            "🎤 Speech recognition ended"
        );

        isListening = false;

        if (!manuallyStopped) {
            setTimeout(() => {
                try {
                    recognition.start();
                } catch (error) {
                    console.log(
                        "Recognition restart skipped"
                    );
                }
            }, 150);
        }
    };

    // ===========================
    // SPEECH ERROR
    // ===========================

    recognition.onerror = (event) => {
        console.log(
            "Speech recognition error:",
            event.error
        );

        if (
            event.error === "not-allowed" ||
            event.error === "service-not-allowed"
        ) {
            manuallyStopped = true;

            isListening = false;

            setIdleState();
        }
    };
}

// ===============================
// ECHO PROTECTION
// ===============================

function isLikelyEcho(text) {
    if (!isSpeaking) {
        return false;
    }

    if (!currentlySpeakingText) {
        return false;
    }

    const spoken =
        normalizeText(
            currentlySpeakingText
        );

    const heard =
        normalizeText(text);

    if (
        !spoken ||
        !heard
    ) {
        return false;
    }

    const words =
        heard.split(" ");

    if (words.length < 2) {
        return false;
    }

    let matches = 0;

    for (const word of words) {
        if (
            spoken.includes(word)
        ) {
            matches++;
        }
    }

    const similarity =
        matches / words.length;

    return similarity >= 0.65;
}

// ===============================
// NORMALIZE TEXT
// ===============================

function normalizeText(text) {
    return text
        .toLowerCase()
        .replace(
            /[^a-z0-9\s]/g,
            ""
        )
        .replace(
            /\s+/g,
            " "
        )
        .trim();
}

// ===============================
// START LISTENING
// ===============================

function startListening() {
    if (!recognition) {
        setupRecognition();
    }

    manuallyStopped = false;

    interruptionActive = false;

    finalTranscript = "";

    interimTranscript = "";

    lastSentText = "";

    // New listening session
    requestVersion++;

    // Stop existing audio
    stopAudio();

    // Clear queues
    audioQueue = [];

    ttsBuffer = "";

    isPlayingQueue = false;

    currentlySpeakingText = "";

    isSpeaking = false;

    isProcessing = false;

    try {
        recognition.start();

        console.log(
            "🎤 Starting microphone..."
        );
    } catch (error) {
        console.log(
            "Recognition already running."
        );
    }
}

// ===============================
// STOP EVERYTHING
// ===============================

function stopEverything() {
    console.log(
        "⛔ STOP EVERYTHING"
    );

    // Invalidate all requests
    requestVersion++;

    manuallyStopped = true;

    interruptionActive = false;

    isListening = false;

    isProcessing = false;

    isSpeaking = false;

    // Clear audio
    audioQueue = [];

    ttsBuffer = "";

    currentAgentResponse = "";

    currentlySpeakingText = "";

    isPlayingQueue = false;

    // Stop recognition
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            console.log(
                "Recognition already stopped"
            );
        }
    }

    // Stop Rime
    stopAudio();

    setIdleState();
}

// ===============================
// SEND INSTRUCTION
// ===============================

async function sendInstruction(text) {
    if (
        !text ||
        !text.trim()
    ) {
        return;
    }

    const cleanText =
        text.trim();

    // Every new request starts
    // with a clean interruption state
    interruptionActive = false;

    // New request version
    const myVersion =
        ++requestVersion;

    isProcessing = true;

    // Clear previous response
    currentAgentResponse = "";

    ttsBuffer = "";

    audioQueue = [];

    // Unlock previous queue
    isPlayingQueue = false;

    currentlySpeakingText = "";

    // Stop old audio
    stopAudio();

    setThinkingState();

    console.log(
        "🧠 Sending instruction:",
        cleanText
    );

    try {
        const response =
            await fetch(
                `${API_BASE}/instruction`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        conversation_id:
                            conversationId,

                        instruction:
                            cleanText
                    })
                }
            );

        if (!response.ok) {
            throw new Error(
                `Backend error: ${response.status}`
            );
        }

        if (!response.body) {
            throw new Error(
                "Streaming response is not supported."
            );
        }

        // ======================================
        // READ STREAM
        // ======================================

        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder("utf-8");

        let buffer = "";

        while (true) {
            // Check stale request
            if (
                myVersion !==
                requestVersion
            ) {
                console.log(
                    "⚠️ Stream cancelled because request is stale"
                );

                try {
                    await reader.cancel();
                } catch (error) {}

                return;
            }

            const {
                value,
                done
            } = await reader.read();

            if (done) {
                break;
            }

            buffer +=
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );

            // ======================================
            // NDJSON
            // ======================================

            const lines =
                buffer.split("\n");

            buffer =
                lines.pop();

            for (
                const line of lines
            ) {
                if (
                    !line.trim()
                ) {
                    continue;
                }

                let data;

                try {
                    data =
                        JSON.parse(
                            line
                        );
                } catch (error) {
                    console.log(
                        "⚠️ Invalid stream chunk:",
                        line
                    );

                    continue;
                }

                // ======================================
                // STALE CHECK
                // ======================================

                if (
                    myVersion !==
                    requestVersion
                ) {
                    console.log(
                        "⚠️ Ignoring stale stream chunk"
                    );

                    try {
                        await reader.cancel();
                    } catch (error) {}

                    return;
                }

                // ======================================
                // TEXT CHUNK
                // ======================================

                if (
                    data.type ===
                    "text"
                ) {
                    const chunk =
                        data.text || "";

                    if (!chunk) {
                        continue;
                    }

                    currentAgentResponse +=
                        chunk;

                    if (agentText) {
                        agentText.textContent =
                            currentAgentResponse;
                    }

                    // Add to TTS
                    ttsBuffer +=
                        chunk;

                    extractSentences(
                        myVersion
                    );

                    // First text received
                    if (
                        !isSpeaking &&
                        !isPlayingQueue
                    ) {
                        setSpeakingState();
                    }
                }

                // ======================================
                // STREAM COMPLETE
                // ======================================

                if (
                    data.type ===
                    "done"
                ) {
                    console.log(
                        "✅ Gemini stream completed"
                    );

                    // Speak remaining text
                    if (
                        ttsBuffer.trim()
                    ) {
                        addSentenceToQueue(
                            ttsBuffer.trim(),
                            myVersion
                        );

                        ttsBuffer = "";
                    }

                    isProcessing = false;

                    playNextAudio(
                        myVersion
                    );
                }

                // ======================================
                // STREAM ERROR
                // ======================================

                if (
                    data.type ===
                    "error"
                ) {
                    throw new Error(
                        data.text ||
                        "Streaming error"
                    );
                }
            }
        }

        // ======================================
        // PROCESS REMAINING BUFFER
        // ======================================

        if (
            buffer.trim()
        ) {
            try {
                const data =
                    JSON.parse(
                        buffer.trim()
                    );

                if (
                    data.type ===
                    "text"
                ) {
                    const chunk =
                        data.text || "";

                    currentAgentResponse +=
                        chunk;

                    if (agentText) {
                        agentText.textContent =
                            currentAgentResponse;
                    }

                    ttsBuffer +=
                        chunk;
                }
            } catch (error) {
                console.log(
                    "Final stream parse skipped"
                );
            }
        }

        // ======================================
        // SPEAK REMAINING TEXT
        // ======================================

        if (
            myVersion ===
                requestVersion &&
            ttsBuffer.trim()
        ) {
            addSentenceToQueue(
                ttsBuffer.trim(),
                myVersion
            );

            ttsBuffer = "";

            isProcessing = false;

            playNextAudio(
                myVersion
            );
        }
    } catch (error) {
        console.error(
            "❌ Instruction error:",
            error
        );

        // Ignore stale request
        if (
            myVersion !==
            requestVersion
        ) {
            return;
        }

        isProcessing = false;

        if (agentText) {
            agentText.textContent =
                "Sorry, I couldn't process that request.";
        }

        setListeningState();
    }
}

// ===============================
// EXTRACT COMPLETE SENTENCES
// ===============================

function extractSentences(
    audioVersion
) {
    if (
        audioVersion !==
        requestVersion
    ) {
        return;
    }

    // IMPORTANT:
    // Detect complete sentences correctly
    const sentenceRegex =
        /^([\s\S]*?[.!?])(\s+|$)/;

    while (true) {
        const match =
            ttsBuffer.match(
                sentenceRegex
            );

        if (!match) {
            break;
        }

        const sentence =
            match[1].trim();

        ttsBuffer =
            ttsBuffer
                .slice(
                    match[0].length
                )
                .trimStart();

        if (sentence) {
            addSentenceToQueue(
                sentence,
                audioVersion
            );
        }
    }

    // Safety for long text
    if (
        ttsBuffer.length > 180
    ) {
        const breakPoint =
            ttsBuffer.lastIndexOf(
                " ",
                180
            );

        if (
            breakPoint > 40
        ) {
            const sentence =
                ttsBuffer
                    .slice(
                        0,
                        breakPoint
                    )
                    .trim();

            ttsBuffer =
                ttsBuffer
                    .slice(
                        breakPoint
                    )
                    .trimStart();

            if (sentence) {
                addSentenceToQueue(
                    sentence,
                    audioVersion
                );
            }
        }
    }

    playNextAudio(
        audioVersion
    );
}

// ===============================
// ADD SENTENCE TO QUEUE
// ===============================

function addSentenceToQueue(
    text,
    audioVersion
) {
    if (
        audioVersion !==
        requestVersion
    ) {
        return;
    }

    if (
        !text ||
        !text.trim()
    ) {
        return;
    }

    audioQueue.push({
        text: text.trim(),
        version: audioVersion
    });
}

// ===============================
// PLAY NEXT RIME SENTENCE
// ===============================

async function playNextAudio(
    audioVersion
) {
    if (
        audioVersion !==
        requestVersion
    ) {
        return;
    }

    // IMPORTANT:
    // Do not start another sentence while
    // the current sentence is still playing.
    if (isPlayingQueue) {
        return;
    }

    if (
        audioQueue.length === 0
    ) {
        return;
    }

    const item =
        audioQueue.shift();

    if (
        !item ||
        item.version !==
        requestVersion
    ) {
        return;
    }

    isPlayingQueue = true;

    isSpeaking = true;

    currentlySpeakingText =
        item.text;

    setSpeakingState();

    console.log(
        "🔊 Rime sentence:",
        item.text
    );

    try {
        await playRimeAudio(
            item.text,
            item.version
        );
    } catch (error) {
        console.error(
            "❌ Rime sentence error:",
            error
        );
    }

    // ======================================
    // RELEASE QUEUE LOCK
    // ======================================

    isPlayingQueue = false;

    currentlySpeakingText = "";

    if (
        audioVersion ===
        requestVersion
    ) {
        if (
            audioQueue.length > 0
        ) {
            // Play NEXT sentence only after
            // previous sentence has completely
            // finished.
            playNextAudio(
                audioVersion
            );
        } else if (
            !isProcessing &&
            !ttsBuffer.trim()
        ) {
            isSpeaking = false;

            if (!manuallyStopped) {
                setListeningState();
            } else {
                setIdleState();
            }
        }
    }
}

// ===============================
// PLAY RIME AUDIO
// ===============================

async function playRimeAudio(
    text,
    audioVersion
) {
    if (
        audioVersion !==
        requestVersion
    ) {
        console.log(
            "⚠️ Audio response is stale"
        );

        return;
    }

    // ==================================================
    // IMPORTANT FIX:
    //
    // DO NOT call stopAudio() here.
    //
    // playNextAudio() already controls the queue.
    // Calling stopAudio() here was resetting
    // isPlayingQueue and could cause multiple
    // sentences to start at the same time.
    // ==================================================

    const encodedText =
        encodeURIComponent(
            text
        );

    const audioUrl =
        `${API_BASE}/audio/stream?text=${encodedText}`;

    console.log(
        "🔊 Playing Rime:",
        audioUrl
    );

    return new Promise(
        (resolve) => {
            currentAudio =
                new Audio(
                    audioUrl
                );

            currentAudio.preload =
                "auto";

            let finished = false;

            function finish() {
                if (finished) {
                    return;
                }

                finished = true;

                if (
                    currentAudioFinish ===
                    finish
                ) {
                    currentAudioFinish =
                        null;
                }

                resolve();
            }

            // ==================================================
            // IMPORTANT:
            // Save resolver so stopAudio() can resolve
            // the pending audio promise during interruption.
            // ==================================================

            currentAudioFinish =
                finish;

            // ======================================
            // AUDIO PLAY
            // ======================================

            currentAudio.onplay = () => {
                if (
                    audioVersion !==
                    requestVersion
                ) {
                    stopAudio();

                    finish();

                    return;
                }

                isSpeaking = true;

                console.log(
                    "🔊 Rime speaking..."
                );

                setSpeakingState();
            };

            // ======================================
            // AUDIO FINISHED
            // ======================================

            currentAudio.onended = () => {
                console.log(
                    "🔊 Rime sentence finished"
                );

                isSpeaking = false;

                currentAudio = null;

                finish();
            };

            // ======================================
            // AUDIO ERROR
            // ======================================

            currentAudio.onerror = (error) => {
                console.error(
                    "❌ Rime audio error:",
                    error
                );

                isSpeaking = false;

                currentAudio = null;

                finish();
            };

            // ======================================
            // PLAY
            // ======================================

            currentAudio
                .play()
                .catch((error) => {
                    console.error(
                        "❌ Audio play failed:",
                        error
                    );

                    isSpeaking = false;

                    currentAudio = null;

                    finish();
                });
        }
    );
}

// ===============================
// STOP RIME AUDIO
// ===============================

function stopAudio() {
    console.log(
        "🛑 Stopping Rime audio"
    );

    // ======================================
    // IMPORTANT:
    // Resolve pending playRimeAudio()
    // promise BEFORE removing handlers.
    // ======================================

    if (currentAudioFinish) {
        const finish =
            currentAudioFinish;

        currentAudioFinish = null;

        try {
            finish();
        } catch (error) {
            console.log(
                "Audio finish error:",
                error
            );
        }
    }

    if (!currentAudio) {
        isSpeaking = false;

        isPlayingQueue = false;

        currentlySpeakingText = "";

        return;
    }

    try {
        currentAudio.pause();

        currentAudio.currentTime = 0;

        currentAudio.src = "";

        currentAudio.load();
    } catch (error) {
        console.log(
            "Audio stop error:",
            error
        );
    }

    currentAudio.onplay = null;

    currentAudio.onended = null;

    currentAudio.onerror = null;

    currentAudio = null;

    isSpeaking = false;

    // Unlock queue
    isPlayingQueue = false;

    currentlySpeakingText = "";
}

// ===============================
// LISTENING STATE
// ===============================

function setListeningState() {
    if (orbStatus) {
        orbStatus.textContent =
            "LISTENING";
    }

    if (orbSubtitle) {
        orbSubtitle.textContent =
            "I'm listening...";
    }

    if (voiceOrb) {
        voiceOrb.classList.remove(
            "thinking",
            "speaking"
        );

        voiceOrb.classList.add(
            "listening"
        );
    }
}

// ===============================
// THINKING STATE
// ===============================

function setThinkingState() {
    if (orbStatus) {
        orbStatus.textContent =
            "THINKING";
    }

    if (orbSubtitle) {
        orbSubtitle.textContent =
            "Processing your request...";
    }

    if (voiceOrb) {
        voiceOrb.classList.remove(
            "listening",
            "speaking"
        );

        voiceOrb.classList.add(
            "thinking"
        );
    }
}

// ===============================
// SPEAKING STATE
// ===============================

function setSpeakingState() {
    if (orbStatus) {
        orbStatus.textContent =
            "SPEAKING • LISTENING";
    }

    if (orbSubtitle) {
        orbSubtitle.textContent =
            "I'm speaking — you can interrupt me";
    }

    if (voiceOrb) {
        voiceOrb.classList.remove(
            "listening",
            "thinking"
        );

        voiceOrb.classList.add(
            "speaking"
        );
    }
}

// ===============================
// IDLE STATE
// ===============================

function setIdleState() {
    if (orbStatus) {
        orbStatus.textContent =
            "READY";
    }

    if (orbSubtitle) {
        orbSubtitle.textContent =
            "Press the microphone to start";
    }

    if (voiceOrb) {
        voiceOrb.classList.remove(
            "listening",
            "thinking",
            "speaking"
        );
    }
}

// ===============================
// BUTTON EVENTS
// ===============================

// MIC BUTTON

if (micButton) {
    micButton.addEventListener(
        "click",
        () => {
            console.log(
                "🎤 MIC BUTTON CLICKED"
            );

            startListening();
        }
    );
}

// ===============================
// STOP BUTTON
// ===============================

if (stopButton) {
    stopButton.disabled = false;

    stopButton.removeAttribute(
        "disabled"
    );

    stopButton.addEventListener(
        "click",
        (event) => {
            event.preventDefault();

            event.stopPropagation();

            console.log(
                "⛔ STOP BUTTON CLICKED"
            );

            stopEverything();
        }
    );
}

// ===============================
// INITIALIZE
// ===============================

setupRecognition();

setIdleState();

console.log(
    "🚀 DataForge Voice Agent initialized"
);