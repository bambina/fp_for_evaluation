// This script is used to handle the WebSocket connection for the chatbot.

// The following variables are passed from the Django template:
const hostName = JSON.parse(document.getElementById("host-name").textContent);
const roomName = JSON.parse(document.getElementById("room-name").textContent);
const senderNameUser = JSON.parse(document.getElementById("sender-user-name").textContent);
// Check if the current page is loaded over HTTPS
const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
// Construct WebSocket URL
const url = `${wsProtocol}${hostName}/ws/chat/${roomName}/`;
// Constants for the WebSocket connection
const MESSAGE_TYPE_CLOSE = "close.connection";
const MESSAGE_TYPE_ASSISTANT = "assistant.message";
const MESSAGE_TYPE_ERROR = "error.message";
const SESSION_TERMINATE_CODE = 4000;
const UNAUTHORIZED_ACCESS_CODE = 4001;
const MAX_RETRIES = 3;
const RECONNECT_INTERVAL = 1000 * 5;
// Constants for the chat interface
const ASSISTANT_DISPLAY_NAME = "Assistant Nico";
const USER_DISPLAY_NAME = "User";
const THINKING_MESSAGE_TEXT = "Thinking...";
// Element IDs
const THINKING_MESSAGE_ID = "thinkingMsg";
const MESSAGE_INPUT_ID = "message_input";
const SEND_BTN_ID = "send_btn";
const CHAT_CONTAINER_ID = "chat-container";

/**
 * WebSocket client class.
 */
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.maxRetries = MAX_RETRIES; // Max retry attempts for reconnection
    this.autoReconnectInterval = RECONNECT_INTERVAL; // Interval between reconnection attempts
    this.messageHandlers = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    // Triggered when the connection is opened
    this.ws.onopen = () => {
      if (this.maxRetries !== MAX_RETRIES) {
        console.log("WebSocket connection restored.");
      }
      this.maxRetries = MAX_RETRIES;
      // Trigger custom 'open' event handlers
      this.triggerHandler("open");
    };

    // Triggered when the connection is closed
    this.ws.onclose = (e) => {
      if (
        e.code === SESSION_TERMINATE_CODE ||
        e.code === UNAUTHORIZED_ACCESS_CODE
      ) {
        toggleFormElements(true);
      } else {
        if (!e.wasClean) {
          this.reconnect();
        }
      }
    };

    // Triggered on a WebSocket error
    this.ws.onerror = (e) => {
      console.error("WebSocket error:", e);
      this.ws.close();
    };

    // Triggered when a message is received from the server
    this.ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      // Trigger custom 'message' event handlers
      this.triggerHandler("message", data);
    };
  }

  /**
   * Reconnects to the WebSocket server.
   */
  reconnect() {
    if (this.maxRetries > 0) {
      console.log("WebSocket connection lost. Reconnecting...");
      // Retry connection after a specified interval
      setTimeout(() => {
        this.connect();
        this.maxRetries--;
      }, this.autoReconnectInterval);
    } else {
      console.log(
        "WebSocket connection lost. Please refresh the Chat page or try again later."
      );
    }
  }

  /**
   * Sends a message to the WebSocket server.
   */
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

  /**
   * Adds a handler for a specific WebSocket event.
   */
  addHandler(event, handler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event).add(handler);
  }

  /**
   * Triggers all handlers for a specific event.
   */
  triggerHandler(event, data) {
    const handlers = this.messageHandlers.get(event) || new Set();
    for (const handler of handlers) {
      handler(data);
    }
  }
}

// Initialize the WebSocket client
const client = new WebSocketClient(url);

// Add an event handler for the "open" event
client.addHandler("open", () => {
  // Set up form event listeners and enable form elements
  setupFormEventListeners();
  toggleFormElements(false);
});

// Add an event handler for the "message" event
client.addHandler("message", (data) => {
  if (data.type === MESSAGE_TYPE_CLOSE) {
    // Terminate the chat session
    handleSessionEnd(data);
  } else if (
    data.type === MESSAGE_TYPE_ASSISTANT ||
    data.type === MESSAGE_TYPE_ERROR
  ) {
    // Display a message from the assistant
    displayMessage(data.message, (isAssistant = true));
  }
});

/**
 * Handles the end of the chat session.
 */
function handleSessionEnd(data) {
  // Disable the message input field
  toggleFormElements(true);
  // Display the session end message
  displayMessage(data.message, (isAssistant = true));
}

/**
 * Creates a DOM element representing the assistant's message.
 */
function createAssistantMessageDom(message) {
  // 1. Create a wrapper for the row
  var rowWrapper = document.createElement("div");
  rowWrapper.className = "row mb-1 justify-content-start";
  // 2. Create a column for the card with automatic width
  var columnWrapper = document.createElement("div");
  columnWrapper.className = "col-auto";
  // 3. Create the card element
  var card = document.createElement("div");
  card.className = "card bg-light";
  // 4. Create the card body
  var cardBody = document.createElement("div");
  cardBody.className = "card-body";
  // 5. Add the sender's name
  var sender = document.createElement("h5");
  sender.className = "card-title";
  sender.textContent = ASSISTANT_DISPLAY_NAME;
  // 6. Add the message content
  var messageContent = document.createElement("p");
  messageContent.className = "card-text";
  // Replace newlines with <br> for formatting
  messageContent.innerHTML = message.replace(/\n/g, "<br>");
  // 7. Assemble the card structure
  rowWrapper.appendChild(columnWrapper);
  columnWrapper.appendChild(card);
  card.appendChild(cardBody);
  cardBody.appendChild(sender);
  cardBody.appendChild(messageContent);
  // 8. Return the completed DOM structure
  return rowWrapper;
}

/**
 * Creates a DOM element representing the user's message.
 */
function createUserMessageDom(message) {
  // 1. Create a wrapper for the row
  var rowWrapper = document.createElement("div");
  rowWrapper.className = "row mb-1 justify-content-end";
  // 2. Create a column for the card with automatic width
  var columnWrapper = document.createElement("div");
  columnWrapper.className = "col-auto";
  // 3. Create the card element
  var card = document.createElement("div");
  card.className = "card";
  // 4. Create the card body
  var cardBody = document.createElement("div");
  cardBody.className = "card-body";
  // 5. Add the sender's name
  var sender = document.createElement("h5");
  sender.className = "card-title";
  sender.textContent = USER_DISPLAY_NAME;
  // 6. Add the user's message content
  var messageContent = document.createElement("p");
  messageContent.className = "card-text";
  // Replace newlines with <br> for formatting
  messageContent.innerHTML = message.replace(/\n/g, "<br>");
  // 7. Assemble the card structure
  rowWrapper.appendChild(columnWrapper);
  columnWrapper.appendChild(card);
  card.appendChild(cardBody);
  cardBody.appendChild(sender);
  cardBody.appendChild(messageContent);
  // 8. Return the completed DOM structure
  return rowWrapper;
}

/**
 * Displays a new message in the chat container.
 */
function displayMessage(message, isAssistant = false) {
  // Determine the appropriate message DOM based on sender type
  let messageDom;
  if (isAssistant) {
    messageDom = createAssistantMessageDom(message);
  } else {
    messageDom = createUserMessageDom(message);
  }
  // Remove the "Thinking..." message if exists
  const thinkingMsg = document.getElementById(THINKING_MESSAGE_ID);
  if (thinkingMsg) {
    thinkingMsg.remove();
  }
  // Append the new message to the chat container
  document.getElementById(CHAT_CONTAINER_ID).appendChild(messageDom);
  // Smooth scroll to the bottom of the page
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: "smooth",
  });
}

/**
 * Sends the message to the chatbot and display the message.
 */
function sendMessage() {
  const messageInputDom = document.getElementById(MESSAGE_INPUT_ID);
  const message = messageInputDom.value;
  // Create a chat card for the user's message
  displayMessage(message);
  // Send the message to the chatbot
  client.send(message, senderNameUser);
  messageInputDom.value = "";
  // Display the "Thinking..." indicator
  appendThinkingMessage();
}

/**
 * Displays a "Thinking..." message while the bot is generating a response.
 */
function appendThinkingMessage() {
  // Create the message element
  var message = document.createElement("div");
  message.id = THINKING_MESSAGE_ID;
  message.textContent = THINKING_MESSAGE_TEXT;
  message.className = "text-primary blink";
  // Append the message to the chat container
  document.getElementById(CHAT_CONTAINER_ID).appendChild(message);
  // Smooth scroll to the bottom of the page
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: "smooth",
  });
}

/**
 * Sets up event listeners for the message input and the send button.
 */
function setupFormEventListeners() {
  let messageInput = document.getElementById(MESSAGE_INPUT_ID);
  let postBtn = document.getElementById(SEND_BTN_ID);

  if (!messageInput && !postBtn) {
    // TODO: Show error message
    console.error("Message input field or post button not found.");
    return;
  }

  // Handle keydown events for the message input field
  messageInput.onkeydown = function (e) {
    // Check if IME (Input Method Editor) input is in progress
    if (e.isComposing || e.key === "Process" || e.keyCode === 229) {
      return;
    }
    // Prevent submitting empty messages
    if (messageInput.value.trim().length <= 0 && e.key === "Enter") {
      e.preventDefault();
      return;
    }
    // Send the message when Enter is pressed without Shift and the input is not empty
    if (
      e.key === "Enter" &&
      !e.shiftKey &&
      messageInput.value.trim().length > 0
    ) {
      e.preventDefault();
      sendMessage();
      postBtn.disabled = true;
    }
  };

  // Handle input events for the message input field
  messageInput.oninput = function () {
    if (messageInput.value.trim().length === 0) {
      postBtn.disabled = true;
    } else {
      postBtn.disabled = false;
    }
  };

  // Handle click events for the post button
  postBtn.onclick = function () {
    sendMessage();
    postBtn.disabled = true;
  };
}

/**
 * Toggles the disabled state of form elements.
 */
function toggleFormElements(disable) {
  // List of element IDs to be toggled.
  const elementIds = [MESSAGE_INPUT_ID];

  elementIds.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      element.disabled = disable;
    }
  });
}

// Connect to the WebSocket server
client.connect();
