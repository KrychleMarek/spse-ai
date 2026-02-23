import { showLoading, hideLoading, messageBox, warning, get_c } from '/controlPanel/utilityFunctions.js';

function detectFile(event) {
    const addFiles = document.querySelector(".add-f-btn");
    const label = (event.target.parentNode.children[0].matches('div')) ? event.target.parentNode.children[1] : event.target.parentNode.children[0];
    const status = event.target.parentNode.parentNode.children[0].children[1];
    const fileList = event.target.files;

    if (fileList.length > 0 && fileList[0].name.endsWith('.docx')) {
        label.style.border = "2px solid rgb(27,200,154)";
        label.innerHTML = `Vloženo: ${fileList[0].name}`;
        status.className = "waitingC";
        status.innerHTML = "Změna SVP";
        addFiles.disabled = false; // Nemužu momentálně otestovat
    } else {
        label.style.border = "2px solid red";
        label.innerHTML = `Vložen špatný formát souboru!`;
        status.innerHTML = "Error";
        status.classList = "failedC";
    }

}

async function uploadFiles() {
    showLoading();

    try {
        const response = await fetch('/api/uploadfile/', {
            method: 'POST',
            body: returnSvpFiles()
        });
        const result = await response.json();

        if (response.ok) {
            console.log(result);
            messageBox(`Úspěch: ${result.message}`);
        } else {
            messageBox(`Error: ${result.detail || result.message}`);
        }

    } catch (error) {
        messageBox(`A network error occurred: ${error.message}`);
        console.error('Upload Error:', error);
    } finally {
        hideLoading();
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const addFiles = document.querySelector(".add-f-btn");

    addFiles.addEventListener("click", () => uploadFiles());
    try {
        const collectionsData = await get_c();

        renderActiveC(collectionsData);

    } catch (error) {
        console.error("Failed to initialize dashboard data:", error);
    }
});

function renderActiveC(collections) {
    for (const cKey of Object.keys(collections)) {

        const name = cKey;
        const cDate = collections[cKey].date.replaceAll("-", ". ");
        const cSource = collections[cKey].source_file.replace(".txt", ".docx");
        const div = document.createElement("div");

        const sub = name.trim();
        const subTag = sub.replace(/\s+/g, "-");

        var status;
        switch (collections[cKey].status) {
            case "green": status = `<div class="activeC">Active</div>`; break;
            case "yellow": status = `<div class="waitingC">Waiting</div>`; break;
            case "grey": status = `<div class="pausedC">Paused</div>`; break;
            case "red": status = `<div class="failedC">Error</div>`; break;
            default: status = "";
        }


        div.className = `subject-key subject-${subTag}`;

        div.innerHTML = `
        <input disabled placeholder="Jméno (zobrazí se při výběru oboru v chatu)" value="${sub}" type="text">
        <button style="display: none;" class="confirm-key">✓</button>
        <button class="delete-key">X</button>
    `;

        div.querySelector(".delete-key").addEventListener("click", () => deleteKey(div));

        document.querySelector(".subject-key-board").appendChild(div);

        const subjectBlock = document.createElement("div");
        subjectBlock.className = `subject subject-${subTag}`;

        subjectBlock.innerHTML = `<div>
        <h2>${sub}</h2>${status}
        </div>
        <div>
            <div>
                <p>Kolecke vytvořena z: ${cSource}</p>
                <p>Datum vytvoření: ${cDate}</p>
            </div>
            <label class="changeSVP" for="${subTag}">Změnit SVP</label>
            <input type="file" accept=".docx" name="${subTag}" id="${subTag}">
        </div>
    `;

        subjectBlock.querySelector("input").addEventListener("change", (event) => detectFile(event));

        document.querySelector(".subject-board").appendChild(subjectBlock);

    }
}


function deleteKey(keyElement) {
    const input = keyElement.querySelector("input");
    const sub = input.value.trim();

    const name = sub || "tuto";
    const className = keyElement.className.split(' ').filter(c => c !== 'subject-key').join(' ');
    if (className != "") {
        const status = document.querySelector(`.${className}`).children[0].children[1].innerHTML

        warning(`
            Doopravdy chcete odstranit ${status} obor <b>${name}</b>? Obor už nebude nadále na výběr v AI chatu.  
            Tato akce je nenávratná!
    `,
            async () => {

                await delete_c(name);

                if (sub && keyElement.className !== "subject-key") {
                    const subTag = sub.replace(/\s+/g, "-");
                    const targetClass = `subject-${subTag}`;

                    document.querySelectorAll(`.${targetClass}`).forEach(el => el.remove());
                }
                keyElement.remove();

            },

            // Cancel:
            () => {
                console.log("Deletion cancelled");
            }
        );
    } else {
        keyElement.remove();
    }
}


function returnSvpFiles() {
    let formData = new FormData();
    const subjectBoard = document.getElementsByClassName("subject-board")[0];

    if (!subjectBoard) {
        console.error("DOM Error: '.subject-board' element not found.");
        return formData;
    }

    const svpSubjects = subjectBoard.children;

    for (const svp of svpSubjects) {
        console.log(svp.firstChild);
        const isFileChange = (svp.firstChild.children[1].innerHTML == "Změna SVP") ? true : false;

        const fileInput = svp.querySelector("input[type='file']");

        const isReadyToUpload = fileInput?.files?.length > 0;

        if (isReadyToUpload && isFileChange) {

            const nameElement = svp.querySelector("h2");

            if (nameElement) {
                const oborName = nameElement.innerText.trim();
                const oborFiles = fileInput.files;

                for (let i = 0; i < oborFiles.length; i++) {
                    formData.append(oborName, oborFiles[i]);
                }
            } else {
                console.warn("Subject name (.h2) missing for a subject block. Skipping.");
            }
        }
    }
    return formData;
}

async function delete_c(name) {
    const response = await fetch(`/api/collections/${name}`, {
        method: "DELETE"
    });

    return response.json();
}


