import { get_ex_svp, get_em_svp, warning, showLoading, hideLoading, messageBox } from "/controlPanel/utilityFunctions.js";

const extractBoard = document.querySelector(".extract-board");
const embeddBoard = document.querySelector(".embedd-board");
const extractButton = document.querySelector(".ex-btn");
const embeddButton = document.querySelector(".em-btn");

document.addEventListener('DOMContentLoaded', async () => {
    const addSVP = document.querySelector(".create-subject").children[1];
    extractButton.addEventListener("click", () => startExtraction());
    showLoading();

    embeddButton.addEventListener("click", () => startEmbedding());

    addSVP.addEventListener("click", () => createSvp());
    try {
        const extractSvpData = await get_ex_svp();
        const embeddSvpData = await get_em_svp();
        renderExtractSvp(extractSvpData);
        renderEmbeddSvp(embeddSvpData);
    } catch (error) {
        console.error("Failed to initialize dashboard data:", error);
    }

    hideLoading();
});


function renderExtractSvp(extractSvp) {
    if(!(extractSvp.length === 0)){
    for (const svp of extractSvp) {
        enableButton(extractButton);
        const subjectBlock = document.createElement("div");
        subjectBlock.className = `subject extract-subject subject-${svp}`;

        subjectBlock.innerHTML = `<div>
                    <h2>${svp}</h2>
                    </div>
                    <div class="svp-controls">
                        <div>
                            <h3>SVP čeká na extrakci.</h3>
                        </div>
                        <button class="base-btn">Odstranit SVP</button>
                    </div>
    `;

        subjectBlock.querySelector(".base-btn").addEventListener("click", (event) => deleteExtractSvpHandler(event));

        extractBoard.appendChild(subjectBlock);
    }}else{
        disableButton(extractButton);
    }
}

function renderEmbeddSvp(embeddSvp) {
    if(!(embeddSvp.length === 0)){
    for (const svp of embeddSvp){
        enableButton(embeddButton);
        const subjectBlock = document.createElement("div");
        subjectBlock.className = `subject embedd-subject`;
        subjectBlock.innerHTML = `<div>
                    <h2>${svp}</h2>
                    </div>
                    <div class="svp-controls">
                        <div>
                            <h3>SVP čeká na embedding.</h3>
                        </div>
                        <button class="base-btn">Odstranit extrahované SVP</button>
                    </div>
    `

    subjectBlock.querySelector(".base-btn").addEventListener("click", (event) => deleteEmbeddSvphandler(event));

    embeddBoard.appendChild(subjectBlock);
        }
    }else{
        disableButton(embeddButton);
    }
}

// Šílená prasárna. Budu muset nejspíš přepsat
function createSvp() {
    const subjectBlock = document.createElement("div");
    subjectBlock.className = `subject extract-subject`;
    subjectBlock.innerHTML = `
                    <div class="svp-controls">
                        <input class="oborNameInput" name="oborNameInput" type="text" placeholder="Toto jméno se zobrazí na stránce!">
                        <button class="confirmSvp">✓</button>
                        <button class="removeSvp">✗</button>
                    </div>
    `;

    subjectBlock.querySelector(".removeSvp").addEventListener("click", (event) => {
        event.target.parentNode.parentNode.remove();
    });

    subjectBlock.querySelector(".confirmSvp").addEventListener("click", (event) => {
        if (event.target.parentNode.children[0].value != "") {
            var parentElement = event.target.parentNode.parentNode;
            var oborName = parentElement.children[0].children[0].value;
            parentElement.innerHTML = `<div>
                    <h2>${oborName}</h2>
                    </div>
                    <div class="svp-controls">
                        <div>
                            <label class="changeSVP" for="${oborName}">Přidejte SVP pro ${oborName}</label>
                            <input type="file" accept=".docx" name="${oborName}" id="${oborName}">
                        </div>
                        <button class="base-btn">Odstranit SVP</button>
                    </div>
    `;
            parentElement.querySelector("input").addEventListener("change", (event) => detectFileChange(event));
            parentElement.querySelector(".base-btn").addEventListener("click", () =>
                warning(`Doopravdy chcete odstranit svp <b>${oborName}</b>? Tato akce je nenávratná!`, () => { parentElement.remove(); }, () => { console.log("Deletion cancelled"); }))
        }
        else {
            alert("Vyplněte jméno oboru!");
        }
    })

    document.querySelector(".extract-board").appendChild(subjectBlock);

}

function detectFileChange(event) {
    var parentElement = event.target.parentNode;
    let formData = new FormData();
    parentElement.children[0].remove();
    parentElement.innerHTML = `<h3>SVP čeká na extrakci. SVP vloženo: ${event.target.files[0].name}</h3>`;
    var oborName = parentElement.parentNode.parentNode.querySelector("h2").innerHTML;
    var svpFile = event.target.files;
    formData.append(oborName, svpFile[0]);
    parentElement.parentNode.parentNode.remove();
    uploadFile(formData);
}

function deleteExtractSvpHandler(keyElement) {
    const extractSvp = keyElement.target.parentNode.parentNode;
    const name = (null === extractSvp.querySelector("h2")) ? "" : extractSvp.querySelector("h2").innerHTML;

    warning(`
            Doopravdy chcete odstranit svp <b>${name}</b>?  
            Tato akce je nenávratná!
    `,
        async () => {
            clearChildren(extractBoard);
            await delete_ex_svp(name);
            try {
            const extractSvpData = await get_ex_svp();
            renderExtractSvp(extractSvpData);
            } catch (error) {
            console.error("Failed to initialize dashboard data:", error);
            }
        },

        // Cancel:
        () => {
            console.log("Deletion cancelled");
        }
    );
}

function deleteEmbeddSvphandler(keyElement) {
    const embeddSvp = keyElement.target.parentNode.parentNode;
    const name = (null === embeddSvp.querySelector("h2")) ? "" : embeddSvp.querySelector("h2").innerHTML;

    warning(`
            Doopravdy chcete odstranit extrahované svp <b>${name}</b>?
            Tato akce je nenávratná! 
    `,
        async () => {
            clearChildren(embeddBoard);
            await delete_em_svp(name);
            try {
            const embeddSvpData = await get_em_svp();
            renderEmbeddSvp(embeddSvpData);
            } catch (error) {
            console.error("Failed to initialize dashboard data:", error);
            }

        },
        // Cancel:
        () => {
            console.log("Deletion cancelled");
        }
    );
}

async function delete_ex_svp(name) {
    const response = await fetch(`/api/extractSvp/${name}`, {
        method: "DELETE"
    });

    return response.json();
}

async function delete_em_svp(name){
    const response = await fetch(`/api/embeddSvp/${name}`, {
        method: "DELETE"
    });

    return response.json();
}

async function uploadFile(formData) {

    try {
        const response = await fetch('/api/uploadfile/', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (response.ok) {
            const uploadedFiles = Object.keys(result.results);
            console.log(result);
        } else {
            messageBox(`Error: ${result.detail || result.message}`);
        }

    } catch (error) {
        messageBox(`A network error occurred: ${error.message}`);
        console.error('Upload Error:', error);
    } finally {
        clearChildren(extractBoard);
        try {
            const collectionsData = await get_ex_svp();

            renderExtractSvp(collectionsData);

        } catch (error) {
            console.error("Failed to initialize dashboard data:", error);
        }
    }
}

async function startExtraction(){
    const response = await fetch('/api/extractAllSvp/');
    const data = await response.json();
    console.log(data.message);
    messageBox("Proces extrakce zahájen! Extrakce může trvat různé časi dle počru souborů. Prosím o strpení.");
}

async function startEmbedding(){
    const response = await fetch('/api/embeddAllSvp/');
    const data = await response.json();
    console.log(data.message);
}

function clearChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function disableButton(button){
    button.disabled = true;
}
function enableButton(button){
    button.disabled = false;
}