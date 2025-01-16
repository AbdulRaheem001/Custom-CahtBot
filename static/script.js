document.getElementById("send-button").addEventListener("click", async () => {
    const userInput = document.getElementById("user-input").value;
    const response = await fetch("/get_response", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userInput }),
    });
    const data = await response.json();
    document.getElementById("user-input").value = "";
    updateChatHistory(data.history);
});

function updateChatHistory(history) {
    const chatHistory = document.getElementById("chat-history");
    chatHistory.innerHTML = "";
    history.forEach(msg => {
        const msgDiv = document.createElement("div");
        msgDiv.className = msg.role;
        msgDiv.textContent = `${msg.role}: ${msg.content}`;
        chatHistory.appendChild(msgDiv);
    });
}
