document.addEventListener("DOMContentLoaded", function () {

    const chatBtn = document.getElementById("chat-btn");
    const chatbox = document.getElementById("chatbox");
    const messages = document.getElementById("chat-messages");

    if (!chatBtn || !chatbox) {
        console.log("Chatbot elements not found");
        return;
    }

    // Toggle chatbox
    chatBtn.addEventListener("click", function () {
        chatbox.classList.toggle("hidden");
    });

    // Send message
    window.sendMessage = function () {
        const input = document.getElementById("msg");
        const text = input.value.trim();

        if (!text) return;

        addMessage(text, "user");
        input.value = "";

        setTimeout(() => {
            addMessage("Hi 👋 How can I help you?", "bot");
        }, 500);
    };

    function addMessage(text, sender) {
        const div = document.createElement("div");
        div.textContent = text;
        div.style.margin = "6px 0";
        div.style.textAlign = sender === "user" ? "right" : "left";
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

});
