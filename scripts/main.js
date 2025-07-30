let keybind_normal = true;
let saved = true;
const state = "deployment";

let lang = "middle";
let short = false;


/* Initializes the chat for the first time */
function initializeChat(){
    const link = document.getElementById("link-input").value;
    deleteInitialWelcome(link);
    updateCurrentOpenName(link);

    configureTabs();
    newChat(link);
    addTab(link);
    document.getElementsByClassName("tab-button")[0].id = "selected";




    document.addEventListener('keydown', submitFollowup);
}

function submitFollowup(key){
    if (key["key"] == 'Enter'){
        if (keybind_normal){
            followupChat(document.getElementById("prompt-input").value);
            document.getElementById("prompt-input").value = ""
        }

    }
}
function deleteItemById(id){
    let item = document.getElementById(id);
    if (!(item===null)){
        item.remove();
    }

}

function configureTabs(){
    const tabs = document.getElementById("tabs");
    const bottom = document.getElementById("bottom");

    tabs.className = "post-config";
    bottom.className = "post-config"

    const add_button = document.createElement("button");
    add_button.id = "add-button";
    add_button.innerHTML = "+";
    add_button.addEventListener("click", promptNewTab)

    tabs.appendChild(add_button);
}

function deleteInitialWelcome(link){
    const body = document.getElementsByTagName("body")[0];

    deleteItemById("welcome-icon");
    deleteItemById("initial-prompt");
    deleteItemById("submit");
    deleteItemById("link-input");

    let name_header = document.createElement("h2");
    name_header.textContent = link;
    name_header.id = "name-header";

    let form = document.getElementById("chat-input-form");
    let main = document.getElementsByTagName("main")[0];

    main.className = "post-config"
    form.className = "post-config";

    let new_textinput = document.createElement("textarea");


    new_textinput.id = "prompt-input";
    new_textinput.cols = "4";
    new_textinput.placeholder = "Anything else to ask?";
    new_textinput.className = "main-page";


    main.prepend(name_header);
    form.appendChild(new_textinput);

}

/* Creates a new chat */
function newChat(link){
    localStorage.setItem(link, "Loading");
    getAjaxSummary(link);
}

/* Clears the current chat from screen */
function clearChatFromScreen(){

    const elements = document.getElementsByClassName("chat-parent");
    const l = elements.length
    for (let i = 0; i<l; i++){
        elements[0].remove();
    }
}

/* Adds a new tab */
function addTab(link){
    const tabs = document.getElementById("tabs");

    const tab_button = document.createElement("span");
    const cancel_button = document.createElement("button");

    cancel_button.className = "cancel";
    cancel_button.innerHTML = "x";
    cancel_button.addEventListener("click", function(){initiateDeleteChat(link)});


    tab_button.innerHTML = "<p>" + link + "</p>";
    tab_button.addEventListener("click", function(){switchTabs(link, tab_button);});
    tab_button.className = "tab-button";
    tab_button.dataset.link_for = link;

    tab_button.appendChild(cancel_button);

    tabs.appendChild(tab_button);
}

function followupChat(q){

    const link = sessionStorage.getItem("current_open");

    const old_storage = localStorage.getItem(link);
    const new_storage = old_storage + "|" + q;
    localStorage.setItem(link, new_storage)

    loadChatFromStorage(link);
    getAjaxFollowup(link, q);

}

function switchTabs(link, button_to_modify){
    for (let item of document.getElementsByClassName("tab-button")){
        item.id = ""
    }

    button_to_modify.id = "selected";
    loadChatFromStorage(link)
}

/* Creates a new AiTextbox object, and adds it to main */
function newAiTextbox(details){
    let main = document.getElementsByTagName("main")[0];

    let parent_div = document.createElement("div");
    let textbox = document.createElement("div");
    let icon = document.createElement("img");

    textbox.className = "textbox";
    textbox.id = "ai"
    parent_div.className = "chat-parent";

    icon.className = "chat-icon";
    icon.src = "static/avatar.png";

    if (!(details===undefined)){
        textbox.innerHTML = details;
    }

    parent_div.appendChild(icon);
    parent_div.appendChild(textbox);
    main.appendChild(parent_div);
}

/* Creates a new UserTextbox object, and adds it to main */
function newUserTextbox(details){
    let main = document.getElementsByTagName("main")[0];

    let parent_div = document.createElement("div");
    let textbox = document.createElement("div");

    textbox.className = "textbox";
    textbox.id = "user"
    parent_div.className = "chat-parent";


    if (!(details===undefined)){
        textbox.textContent = details;
    }

    parent_div.appendChild(textbox);
    main.appendChild(parent_div);
}

function getAjaxSummary(link){
    setRequestConfigs();
    saved = false;
    const data = JSON.stringify({
      'link': link,
      'ip': getIp(),
      'lang': lang,
      'short': short,
      'query': 'string'
    });

    let endpoint = ""
    if (state=="testing"){
        endpoint = "http://127.0.0.1:800/a/";
    }
    else{
        endpoint = "https://tosautomation-backend.vercel.app/a/";
    }


    let request = new XMLHttpRequest();
    request.open('POST', endpoint);
    request.setRequestHeader('accept', 'application/json');
    request.setRequestHeader('Content-Type', 'application/json');

    request.onreadystatechange = function (){
        if (!(this.readyState == 4)){
            localStorage.setItem(link, "Loading...");
            loadChatFromStorage(sessionStorage.getItem("current_open"));

        }
        else if (this.readyState == 4){
            localStorage.setItem(link, this.responseText.replace(/"/g, ""));
            if (sessionStorage.getItem("current_open") == link){
                loadChatFromStorage(sessionStorage.getItem("current_open"));

            }
            saved = true;

        }
    }

    request.send(data);

}



function getAjaxFollowup(link, query){
    setRequestConfigs();
    console.log(lang);
    const data = JSON.stringify({
      'link': link,
      'ip': getIp(),
      'lang': lang,
      'short': short,
      'query': query
    });
    saved = false


    let request = new XMLHttpRequest();
    let endpoint = ""

    if (state=="testing"){
        endpoint = "http://127.0.0.1:800/followup/";
    }
    else{
        endpoint = "https://tosautomation-backend.vercel.app/followup/";
    }

    request.open('POST', endpoint);
    request.setRequestHeader('accept', 'application/json');
    request.setRequestHeader('Content-Type', 'application/json');

    request.onreadystatechange = function (){
        if (!(this.readyState == 4)){

        }
        else if (this.readyState == 4){
            const old_storage = localStorage.getItem(link);
            console.log(this.responseText);
            const new_storage = old_storage + "|" + this.responseText.replace(/"/g, "");
            localStorage.setItem(link, new_storage);

            if (sessionStorage.getItem("current_open") == link){
                loadChatFromStorage(sessionStorage.getItem("current_open"));
            }
            saved = true;
        }
    }

    request.send(data);
}

function loadChatFromStorage(link){
    clearChatFromScreen();

    const chat_details = localStorage.getItem(link);
    const processed = chat_details.split("|");

    for (let i=0; i<processed.length; i++){
        if ((i%2)==0){
            newAiTextbox(processed[i]);

        }
        else{
            newUserTextbox(processed[i]);
        }
    }
    updateCurrentOpenName(link);
}

function promptNewTab(link){
    keybind_normal = false
    const box = document.createElement("div");
    const bg = document.createElement("div");
    const body = document.getElementsByTagName("body")[0];

    bg.id = "bg";
    box.id = "prompt-box";

    box.innerHTML = `<h2 id="prompt-h2">Enter a new link to simplify and then click Go!</h2>
                     <form onsubmit="return false" id="popup">
                        <input id="link-input" class="mini-popup" type="text" placeholder="Link to document" pattern="https?:\\/\\/(www\\.)?[0-9a-zA-Z\\-]+\\.[a-zA-Z]{2,}([\\/\\w\\?\\=\\.\\-&]*)?" title="Please provide a valid link (http:// or https://)">
                        <input class="mini-popup" id="submit" type="submit" value="Go!">
                        <button class="mini-popup" id="cancel" type="button">Cancel</button>
                     </form>`


    body.appendChild(bg);
    body.appendChild(box);

    document.getElementById("cancel").addEventListener("click", cancelPopup);
    document.getElementById("popup").addEventListener("submit", function(){acceptNewTab(document.getElementById("link-input").value)});

}

function cancelPopup(){
    deleteItemById("bg");
    deleteItemById("prompt-box");
    keybind_normal = true;
}

function createChatsFromStorage(){
    const link = localStorage.key(2)
    deleteInitialWelcome(link);
    configureTabs();

    for (let i = 2; i<localStorage.length; i++){
        console.log(localStorage.key(i))
        addTab(localStorage.key(i));
    }

    document.getElementsByClassName("tab-button")[0].id = "selected";

    loadChatFromStorage(link);
    updateCurrentOpenName(link);
}

function acceptNewTab(link){
    if (localStorage.getItem(link) === null){
        clearChatFromScreen();
        cancelPopup();
        newChat(link);
        addTab(link);

        const tabs = document.getElementsByClassName("tab-button");

        for (let item of document.getElementsByClassName("tab-button")){
            item.id = ""
        }

        tabs[tabs.length - 1].id = "selected";

    }
    else{
        loadChatFromStorage(link);
        cancelPopup();
        for (let item of document.getElementsByClassName("tab-button")){

            if (!(item.dataset.link_for==link)){
                item.id = "";
            }
            else{
                item.id = "selected";
            }
        }

    }
    updateCurrentOpenName(link);

}

function updateCurrentOpenName(name){
    sessionStorage.setItem("current_open", name)
    document.getElementById("name-header").textContent = name;
}

function initialBind(){
    window.addEventListener("beforeunload", function(event){preventUnload(event)});
    document.getElementById("settings-button").addEventListener("click", toggleAside);
    configureForm();
    if (localStorage.length <= 2){
        document.getElementById("chat-input-form").addEventListener("submit", initializeChat);
        if (localStorage.length == 0){
            localStorage.setItem("lang", "middle");
            localStorage.setItem("short", "false");
        }

    }
    else{
        createChatsFromStorage();
        document.addEventListener('keydown', submitFollowup);
    }



}

function getIp(){
    let ip = "";
    const request = new XMLHttpRequest();
    request.onreadystatechange = function (){
        if (this.readyState == 4){
            ip = this.responseText;
        }
    }
    request.open("GET", "https://api.ipify.org", false);
    request.send();
    return ip;
}


function initiateDeleteChat(link){
    const body = document.getElementsByTagName("body")[0];

    const bg = document.createElement("div");
    bg.id = "bg"

    const box = document.createElement("div");
    box.id = "prompt-box";

    box.innerHTML = `<h2>Are you sure you would like to close this tab?</h2>
                     <h3 class="warning">Note: This will delete all chat history related to this tab. This cannot be undone</h3>
                     <button id="submit" class="mini-popup">Confirm</button>
                     <button id="cancel" class="mini-popup">Cancel</button>`

    body.appendChild(bg);
    body.appendChild(box);
    document.getElementById("submit").addEventListener("click", function(){deleteChat(link)});
    document.getElementById("cancel").addEventListener("click", cancelPopup);
    keybind_normal = false;

}
function deleteChat(link){
    localStorage.removeItem(link);
    location.reload();
}


function preventUnload(event){
    if (!saved){
        event.preventDefault();
    }


}

function toggleAside(){
    let aside = document.getElementsByTagName("aside")[0];
    if (aside.className == "open"){
        aside.className = "closed";
    }
    else if (aside.className == "closed"){
        aside.className = "open";
    }
}

function setRequestConfigs(){

    lang = localStorage.getItem("lang");
    short = localStorage.getItem("short") === "true";
    console.log(short);
}

function configureForm(){
    if (localStorage.length >= 2){
        for (let item of document.getElementsByClassName("lang-buttons")){

            if (localStorage.getItem("lang") == item.id){
                item.checked = true
            }
        }

        if (localStorage.getItem("short") === "true"){
            document.getElementById("short").checked = true
        }
        else{
            document.getElementById("normal").checked = true
        }
    }

}


initialBind();
