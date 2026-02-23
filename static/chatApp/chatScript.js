let selectedTag = null;
let chatHistory = [];
let collections = [];

const tempWrapper = document.createElement("div");
const gif = "<img class='loadingGif' src='/chatApp/img/loading.gif'>"
tempWrapper.innerHTML = gif;
const loadingGif = tempWrapper.firstChild;
const chatContainer = document.getElementsByClassName("chat")[0];
const inputField = document.getElementsByClassName("userInput")[0]; // Element pro input query
const sendBtn = document.getElementsByClassName("sendBtn")[0]; // Element pro submit
const resetButton = document.getElementsByClassName("changeObor")[0]; // Tlačítko na reset a znovuzvolení oboru (zobrazí se pouze když je obor vybraný)
const wrapper = document.getElementsByClassName("oborWrapper")[0];

document.addEventListener('DOMContentLoaded', (event) => {
    fetch('/api/collections')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Successfully fetched collections:", data);      
            if (Array.isArray(data)) {
                collections = data; 
                loadObor(); 
            } else {
                throw new Error("Received data is not a valid collection array.");
            }
        })
        .catch(error => {
            console.error("Could not fetch collections:", error);
        });
});

document.addEventListener('DOMContentLoaded', (event) => {

    addMessageBlock("ai", "Ahoj! O jaký obor se zajímáš?");

    sendBtn.addEventListener("click", async () => { // Při kliknutí na tlačítko Submit
        var query = inputField.value.trim(); // Získá otázku z textového pole a odstraní bílé znaky na začátku a konci
        inputField.disabled = true;
        sendBtn.disabled = true;
        addMessageBlock("user", query);
        inputField.value = "";
        chatContainer.appendChild(loadingGif);
        scrollToBottom(chatContainer.parentNode);
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: query,
                selected_tag: selectedTag,
                chat_history: chatHistory
            })
        });

        const data = await response.json(); // Čeká na odpověď a převede ji na JSON
        
        
        if (data.answer) {
            addMessageBlock(data.ansType, data.answer); // Zobrazí odpověď od AI v chatu
            chatHistory.push({     // Uloží otázku a odpověď do historie
                user: query,
                ai: data.answer
            });
        } else {
            addMessageBlock("error","Došlo k chybě."); // Pokud se něco pokazí, zobrazí chybovou hlášku
        }
        chatContainer.querySelector(".loadingGif").remove();
    });



    inputField.addEventListener("keydown", function (event) {   // Posílání zprávy na stisk enter
        if (event.key === "Enter") {
            event.preventDefault();
            sendBtn.click();   // Aktivuje kliknutí submitButtonu
        }
    });

    resetButton.addEventListener("click", () => changeObor());
});



async function addMessageBlock(type, content){
    if(type === "user"){
        const msg = document.createElement("div");
        msg.classList.add("user-messageStripe","messageStripe");
        const userTemplate = `<img class="user-icon" src="/chatApp/img/user.svg" alt=""> 
                <div class="user-messageWrapper">
                    <img class="user-messagePointer" src="/chatApp/img/user-pointer.svg" alt="">
                    <div class="user-messageContent messageContent">${
                        content.replace(/<\/?[^>]+(>|$)/g, "")}</div>
                </div>
                `
        msg.innerHTML =userTemplate;
        chatContainer.appendChild(msg);}
    else if(type === "ai"){
        const msg = document.createElement("div");
        msg.classList.add("ai-messageStripe","messageStripe");
        const aiTemplate = ` <img class="ai-icon" src="/chatApp/img/spseAI.svg" alt=""> 
                <div class="ai-messageWrapper">
                    <img class="ai-messagePointer" src="/chatApp/img/ai-pointer.svg" alt="">
                    <div class="ai-messageContent messageContent"></div>
                    <div class="messageControl">
                        <img class="copyBtn" src="/chatApp/img/copy.svg" alt="">
                    </div>
                </div>`
        msg.innerHTML = aiTemplate;
        
        const copyButton = msg.querySelector(".copyBtn");

        const contentDiv = msg.querySelector(".messageContent");

        copyButton.addEventListener("click", () => {copyToClipboard(contentDiv.innerText);});

        chatContainer.appendChild(msg);
        await streamText(content);
    }else if(type === "error"){
       const msg = document.createElement("div");
        msg.classList.add("error-messageStripe", "messageStripe");
        const errorTemplate  = `<div class="error-messageStripe messageStripe">
                <div class="error-messageWrapper">
                    <div class="error-messageContent messageContent">${content}</div>
                </div>
            </div>`
            msg.innerHTML = errorTemplate;
            chatContainer.appendChild(msg);
         
    }
    scrollToBottom(chatContainer.parentNode);
    if(chatContainer.children.length!=2 && !(type == "user" || type == "error")){
        inputField.disabled = false;
        sendBtn.disabled = false; 
    }
}
async function streamText(content, delay = 50) {
    const parser = new DOMParser();
    const stripes = document.getElementsByClassName("messageStripe");
    const outputMsg = stripes[stripes.length - 1].querySelector(".messageContent"); 
    let revealed = "";
    let lastHTML = "";

    return new Promise((resolve) => {
        function step() {
            const nextChunk = content.slice(revealed.length, revealed.length + 3);
            
            if (nextChunk.length === 0) {
                resolve(); 
                return; 
            }
            
            revealed += nextChunk;
            const doc = parser.parseFromString(revealed, "text/html");
            const currentHTML = doc.body.innerHTML;
            
            if (currentHTML !== lastHTML) {
                outputMsg.innerHTML = currentHTML;
                lastHTML = currentHTML;
            }

            if (revealed.length < content.length) {
                setTimeout(step, delay);
            } else {
                resolve();
            }
        }

        step(); 
    });
}
function loadObor(){
    if(!(collections === undefined || collections.length == 0)){
    for (const cKey of collections){
        const oborBtn = document.createElement("button");
        oborBtn.innerHTML = cKey;
        oborBtn.addEventListener('click', () => setObor(oborBtn));
        wrapper.appendChild(oborBtn);
    }}else{
        const oborBtn = document.createElement("button");
        oborBtn.innerHTML = "Nenalezeny žádné obory";
        wrapper.appendChild(oborBtn);
    }
}

function setObor(target){
    selectedTag = target.innerText;
    for(const element of target.parentNode.children){
        element.style.display = "none";
    }
    deleteLastMessage();
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.value = "";
    inputField.focus();
    resetButton.style.display = "block";
    addMessageBlock("ai", `Co tě zajíma o ${selectedTag}?`);
}

function changeObor(){
    selectedTag = null;
    chatHistory = [];
    deleteAllMessages();
    inputField.disabled = true;
    sendBtn.disabled = true;
    inputField.value = "Vyberte obor";
    loadObor();
    resetButton.style.display = "none";
    addMessageBlock("ai", "O jaký obor se zajímáš teď?")
}

function deleteLastMessage(){
    chatContainer.children[chatContainer.children.length-1].remove();
}
function deleteAllMessages(){
    const messagesToDelete = [...chatContainer.children]
    for(const message of messagesToDelete){
        if(message != wrapper){
        message.remove();
        }
    }
}

function copyToClipboard(text){
  navigator.clipboard.writeText(text)
    .then(() => {
      console.log('Text successfully copied to clipboard!');
    })
    .catch(err => {
      console.error('Could not copy text: ', err);
    });
}

function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
}

function disableButton(button){
    button.disabled = true;
}

function enableButton(button){
    button.disabled = false;
}