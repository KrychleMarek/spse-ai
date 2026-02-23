export function warning(content, onConfirm, onCancel) {
    document.querySelector(".blur").style.display = "block";
    const wrapper = document.createElement("div");
    wrapper.className = "warning";
    const wMessage = `<div class="warning-box">
                        <p>${content}</p>
                        <div>
                            <button class="confirm">Ano</button>
                            <button class="cancel">Ne</button>
                        </div>
                 </div>`
    wrapper.innerHTML = wMessage;

    document.body.appendChild(wrapper);

    wrapper.querySelector(".confirm").onclick = () => {
        wrapper.remove();
        if (onConfirm) onConfirm();
        document.querySelector(".blur").style.display = "none";
    };

    wrapper.querySelector(".cancel").onclick = () => {
        wrapper.remove();
        if (onCancel) onCancel();
        document.querySelector(".blur").style.display = "none";
    };
}

export function messageBox(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "warning";
    document.querySelector(".blur").style.display = "block";
    wrapper.innerHTML = `
        <div class="warning-box">
            <p>${text}</p>
            <div>
                <button class="confirm">Ok</button>
            </div>
        </div>
    `;


    document.body.appendChild(wrapper);

    wrapper.querySelector(".confirm").onclick = () => {
        wrapper.remove();
        document.querySelector(".blur").style.display = "none";
    };
}

export function showLoading() {
    const loadingGifDisplay = document.getElementsByClassName("loadingGif")[0];
    if (loadingGifDisplay) {
        loadingGifDisplay.style.display = "block";
    }
}

export function hideLoading() {
    const loadingGifDisplay = document.getElementsByClassName("loadingGif")[0];
    if (loadingGifDisplay) {
        loadingGifDisplay.style.display = "none";
    }
}

export function get_c() {

    return fetch('/api/collections')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Qdrant Collections Data:", data);
            return data;
        })
        .catch(error => {
            console.error("Could not fetch collections:", error);
        });

}

export function get_ex_svp() {
    return fetch("/api/extractSvp")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            return response.json();
        })
        .then(data => {
            console.log("Svp for extraction:", data);
            return data;
        })
        .catch(error => {
            console.error("Could not fetch svp for extraction:", error);
        })
}

export function get_em_svp() {
    return fetch("/api/embeddSvp")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            return response.json();
        })
        .then(data => {
            console.log("Svp for embedding:", data)
            return data;
        })
        .catch(error => {
            console.error("Could not fetch svp for embedding:", error);
        })
}