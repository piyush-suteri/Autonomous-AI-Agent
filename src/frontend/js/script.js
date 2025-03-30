/*
 * This script includes utility function_calleds for the backend server.
 * Developed by: Piyush Suteri
 * Know More: https://youtube.com/@piyushsuteri
 */

// Constants
const CONFIG = {
  SOCKET_URL: "http://localhost:5000",
  SOCKET_OPTIONS: {
    transports: ["websocket"],
    reconnectionAttempts: 5,
  },
  MAX_INPUT_HEIGHT: 150,
  MIN_INPUT_HEIGHT: 24,
};

// Core application class
class ChatApp {
  constructor() {
    this.state = {
      isProcessing: false,
      currentChatId: null,
    };

    this.elements = this.initializeElements();
    this.socket = this.initializeSocket();

    this.initializeTheme();
    this.setupEventListeners();
    this.updateChatsList();
    this.createNewChat();
  }

  initializeElements() {
    return {
      messages: document.getElementById("messagesArea"),
      input: document.getElementById("userInput"),
      send: document.getElementById("sendButton"),
      status: document.getElementById("statusBar"),
      theme: {
        button: document.getElementById("themeButton"),
        icon: document.getElementById("themeButton").querySelector("i"),
      },
      settings: {
        button: document.getElementById("settingsButton"),
        menu: document.getElementById("settingsMenu"),
      },
      history: {
        toggle: document.getElementById("historyToggle"),
        sidebar: document.getElementById("historySidebar"),
        list: document.getElementById("chatsList"),
        newChat: document.querySelector(".new-chat-btn"),
      },
      html: document.documentElement,
    };
  }

  initializeSocket() {
    const socket = io(CONFIG.SOCKET_URL, CONFIG.SOCKET_OPTIONS);

    socket.on("connect", () => {
      console.log("Connected to server");
      this.elements.status.textContent = "Connected";
    });

    socket.on("disconnect", () => {
      console.log("Disconnected from server");
      this.elements.status.textContent = "Disconnected";
    });

    socket.on("response", (data) => {
      if (data.success) {
        if (data.response) this.addMessage(data.response, "model");
        if (data.chatId) {
          this.state.currentChatId = data.chatId;
          if (data.title) this.updateChatsList();
        }
        this.setProcessing(data.processing || false, data.status);
      } else {
        this.addMessage(
          `Error: ${data.error || "Unknown error occurred"}`,
          "model"
        );
        console.error(data.error);
        this.setProcessing(false);
      }
    });

    return socket;
  }

  initializeTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    this.elements.html.setAttribute("data-theme", savedTheme);
    this.updateThemeIcon(savedTheme);
  }

  updateThemeIcon(theme) {
    this.elements.theme.icon.className =
      theme === "light" ? "fa-solid fa-moon" : "fa-solid fa-sun";
  }

  addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "model" ? "ai" : "user");

    if (sender === "model") {
      messageDiv.innerHTML = marked.parse(text);
      Prism.highlightAllUnder(messageDiv);
    } else if (sender === "user") {
      messageDiv.textContent = text;
    }

    this.elements.messages.appendChild(messageDiv);
    this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
  }

  async createNewChat() {
    this.state.currentChatId = null;
    this.elements.messages.innerHTML = "";
    try {
      await fetch("/api/reset", { method: "POST" });
    } catch (error) {
      console.error("Error resetting chat:", error);
    }
  }

  async loadChat(chatId) {
    try {
      const response = await fetch(`/api/chats/${chatId}/load`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to load chat");

      this.state.currentChatId = chatId;
      this.elements.messages.innerHTML = "";

      const chats = await response.json();

      chats.contents.forEach((msg) => {
        const messageText = msg.parts.join(" ");
        const messageRole = msg.role;

        this.addMessage(messageText, messageRole);
      });
      this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    } catch (error) {
      console.error("Error loading chat:", error);
      this.elements.status.textContent = "Error loading chat";
    }
  }

  async updateChatsList() {
    try {
      const response = await fetch("/api/chats");
      const chats = await response.json();
      this.elements.history.list.innerHTML = "";

      Object.entries(chats)
        .sort(([idA], [idB]) => parseInt(idB) - parseInt(idA))
        .forEach(([id, chat]) => {
          const chatElement = document.createElement("div");
          chatElement.className = `chat-item${
            id === this.state.currentChatId ? " active" : ""
          }`;
          chatElement.innerHTML = `
            <span>${chat.title}</span>
            <button class="delete-btn" aria-label="Delete chat">
              <i class="fa-solid fa-trash"></i>
            </button>
          `;

          chatElement.addEventListener("click", () => this.loadChat(id));
          chatElement
            .querySelector(".delete-btn")
            .addEventListener("click", (e) => this.deleteChat(id, e));

          this.elements.history.list.appendChild(chatElement);
        });
    } catch (error) {
      console.error("Error updating chats list:", error);
    }
  }

  async deleteChat(chatId, event) {
    event.stopPropagation();
    try {
      await fetch(`/api/chats/${chatId}`, { method: "DELETE" });
      if (chatId === this.state.currentChatId) {
        this.elements.messages.innerHTML = "";
        this.state.currentChatId = null;
      }
      this.updateChatsList();
    } catch (error) {
      console.error("Error deleting chat:", error);
    }
  }

  setProcessing(processing, status) {
    this.state.isProcessing = processing;
    this.elements.send.querySelector(".send-icon").style.display = processing
      ? "none"
      : "block";
    this.elements.send.querySelector(".spinner-container").style.display =
      processing ? "block" : "none";
    this.elements.send.classList.toggle("processing", processing);
    this.elements.status.textContent = processing
      ? status || "Processing..."
      : "Ready";
  }

  async sendMessage() {
    if (this.state.isProcessing) return;

    const message = this.elements.input.value.trim();
    if (!message) return;

    this.addMessage(message, "user");
    this.elements.input.value = "";
    this.elements.input.style.height = "auto";
    this.setProcessing(true);

    this.socket.emit("message", {
      message,
      chatId: this.state.currentChatId,
    });
  }

  async stopProcessing() {
    try {
      const response = await fetch("/force_stop", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to stop processing");
      }

      this.setProcessing(false);
      this.elements.status.textContent = "Processing stopped";
    } catch (error) {
      console.error("Error:", error);
      this.elements.status.textContent = "Error stopping processing";
    }
  }

  setupEventListeners() {
    this.elements.theme.button.addEventListener("click", () => {
      const newTheme =
        this.elements.html.getAttribute("data-theme") === "light"
          ? "dark"
          : "light";
      this.elements.html.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      this.updateThemeIcon(newTheme);
    });

    this.elements.input.addEventListener("input", () => {
      this.elements.input.style.height = "auto";
      const newHeight = Math.max(
        CONFIG.MIN_INPUT_HEIGHT,
        Math.min(this.elements.input.scrollHeight, CONFIG.MAX_INPUT_HEIGHT)
      );
      if (newHeight !== parseInt(this.elements.input.style.height)) {
        this.elements.input.style.height = `${newHeight}px`;
      }
    });

    this.elements.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    this.elements.send.addEventListener("click", () =>
      this.state.isProcessing ? this.stopProcessing() : this.sendMessage()
    );

    this.elements.settings.button.addEventListener("click", (e) => {
      e.stopPropagation();
      this.elements.settings.menu.classList.toggle("show");
    });

    this.elements.history.toggle.addEventListener("click", () =>
      this.elements.history.sidebar.classList.toggle("show")
    );
    this.elements.history.newChat.addEventListener("click", () =>
      this.createNewChat()
    );

    document.addEventListener("click", (e) => {
      if (
        !this.elements.settings.menu.contains(e.target) &&
        !this.elements.settings.button.contains(e.target)
      ) {
        this.elements.settings.menu.classList.remove("show");
      }

      if (
        !this.elements.history.sidebar.contains(e.target) &&
        !this.elements.history.toggle.contains(e.target) &&
        this.elements.history.sidebar.classList.contains("show")
      ) {
        this.elements.history.sidebar.classList.remove("show");
      }
    });
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.chatApp = new ChatApp();
});
