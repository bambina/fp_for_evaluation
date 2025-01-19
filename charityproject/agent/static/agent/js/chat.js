// This script is used to handle the WebSocket connection for the chatbot.

// The following variables are passed from the Django template:
const hostName = JSON.parse(document.getElementById("host-name").textContent);
const roomName = JSON.parse(document.getElementById("room-name").textContent);
// Check if the current page is loaded over HTTPS
const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
// Construct WebSocket URL
const url = `${wsProtocol}${hostName}/ws/chat/${roomName}/`;
const MESSAGE_TYPE_CLOSE = "close.connection";
const MESSAGE_TYPE_ASSISTANT = "assistant.message";
const MESSAGE_TYPE_ERROR = "error.message";
const SESSION_TERMINATE_CODE = 4000;
const UNAUTHORIZED_ACCESS_CODE = 4001;
const MAX_RETRIES = 3;
const RECONNECT_INTERVAL = 1000 * 5;
const TOAST_DELAY = 5000;
const ASSISTANT_DISPLAY_NAME = "Assistant Nico";
const USER_DISPLAY_NAME = "User";
const SENDER_NAME_USER = "user"; // Supported value for the OpenAI API

// WebSocket client class
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.maxRetries = MAX_RETRIES;
    this.autoReconnectInterval = RECONNECT_INTERVAL;
    this.messageHandlers = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      if (this.maxRetries !== MAX_RETRIES) {
        console.log("WebSocket connection restored.");
      }
      this.maxRetries = MAX_RETRIES;
      this.triggerHandler("open");
    };
    this.ws.onclose = (e) => {
      if (
        e.code === SESSION_TERMINATE_CODE ||
        e.code === UNAUTHORIZED_ACCESS_CODE
      ) {
        // toggleFormElements(true);
      } else {
        if (!e.wasClean) {
          this.reconnect();
        }
      }
    };
    this.ws.onerror = (e) => {
      console.error("WebSocket error:", e);
      this.ws.close();
    };
    this.ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      this.triggerHandler("message", data);
    };
  }

  reconnect() {
    if (this.maxRetries > 0) {
        console.log("WebSocket connection lost. Reconnecting...");
      setTimeout(() => {
        this.connect();
        this.maxRetries--;
      }, this.autoReconnectInterval);
    } else {
        console.log("WebSocket connection has been lost. Please try accessing from the Top page again, or wait a while before retrying.");
    }
  }

  send(message, sender) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          message: message,
          sender: sender,
        })
      );
    } else {
        console.log("WebSocket connection is not open.");
    }
  }

  addHandler(event, handler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event).add(handler);
  }

  triggerHandler(event, data) {
    const handlers = this.messageHandlers.get(event) || new Set();
    for (const handler of handlers) {
      handler(data);
    }
  }

}

// Initialize the WebSocket client
const client = new WebSocketClient(url);

// Add event handlers
client.addHandler("open", () => {
  setupFormEventListeners();
//   toggleFormElements(false);
});

client.addHandler("message", (data) => {
  if (data.type === MESSAGE_TYPE_CLOSE) {
    handleSessionEnd(data);
  } else if (data.type === MESSAGE_TYPE_ASSISTANT || data.type === MESSAGE_TYPE_ERROR) {
    // Add a message from the assistant
    createCard(data, isAssistant=true);
  }
});

function handleSessionEnd(data) {
//   toggleFormElements(true);
  createCard(data);
}

function createCard(question, isAssistant=false) {
  // Create a new row wrapper for the card
  var rowWrapper = document.createElement("div");
  if (isAssistant) {
    rowWrapper.className = "row mb-1 justify-content-start";
  } else {
    rowWrapper.className = "row mb-1 justify-content-end";
  }
  // Create a column with auto width
  var autoWidth = document.createElement("div");
  autoWidth.className = "col-auto";
  rowWrapper.appendChild(autoWidth);
  // Create the card element
  var card = document.createElement("div");
  card.className = "card";
  if (isAssistant) {
    card.classList.add("bg-light"); // Assistant messages have a light background
  }
  autoWidth.appendChild(card);
  // Create the card body
  var cardBody = document.createElement("div");
  cardBody.className = "card-body";
  card.appendChild(cardBody);
  // Add the sender name
  var sender = document.createElement("h5");
  sender.className = "card-title";
  if (isAssistant) {
    sender.textContent = ASSISTANT_DISPLAY_NAME;
  } else {
    sender.textContent = USER_DISPLAY_NAME;
  }
  cardBody.appendChild(sender);
  // Add the question message
  var newPost = document.createElement("p");
  newPost.className = "card-text";
  newPost.innerHTML = question.message.replace(/\n/g, "<br>");
  cardBody.appendChild(newPost);
  // Remove the generating message
  var generatingMsg = document.getElementById("generatingMsg");
  if (generatingMsg) {
    generatingMsg.remove();
  }
  document.getElementById("chat-container").appendChild(rowWrapper);
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  });
}

function sendMessage() {
  const messageInputDom = document.getElementById("message_input");
  const message = messageInputDom.value;
  createCard({ message: message });
  client.send(message, SENDER_NAME_USER);
  messageInputDom.value = "";
  appendGeneratingMessage();
}

function appendGeneratingMessage() {
  var message = document.createElement("div");
  message.id = "generatingMsg";
  message.className = "text-primary blink";
  message.textContent = "Generating...";
  document.getElementById("chat-container").appendChild(message);
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  });
}

function setupFormEventListeners() {
  let messageInput = document.getElementById("message_input");
  let postBtn = document.getElementById("send_btn");

  if (messageInput) {
    messageInput.onkeydown = function (e) {
        if (e.isComposing || e.key === 'Process' || e.keyCode === 229) {
            // IME input in progress
            return;
        }
        if (messageInput.value.trim().length <= 0 && e.key === "Enter") {
            e.preventDefault();
            return; // Prevent line break when input is empty
        }
        if (e.key === "Enter" && !e.shiftKey && messageInput.value.trim().length > 0) {
            e.preventDefault();
            sendMessage(); // Send the message when Enter is pressed without Shift
        }
    };

    messageInput.oninput = function () {
        if (messageInput.value.trim().length === 0) {
            postBtn.disabled = true;
        } else {
            postBtn.disabled = false;
        }
    };
  }

  if (postBtn) {
    postBtn.onclick = function () {
      sendMessage();
    };
  }
}

client.connect();
