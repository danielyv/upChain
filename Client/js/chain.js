
el=document.getElementById("page-content")
main=document.getElementById("main")
var list=null
if(el){
    el.addEventListener("onload",historic())


}
function search(str) {
    let val= document.getElementById("waterfall-exp").value
    let doc =document.getElementById("page-content")
    str=""
    str+="<ul class=\"demo-list-icon mdl-list\">"
    str2=""
    for(i in list){

        if(list[i]["name"].toLowerCase().indexOf(val.toLowerCase())!==-1){
            str2="<li class=\"mdl-list__item\"><span class=\"mdl-list__item-primary-content\">" +
                "<i class=\"material-icons mdl-list__item-icon\">insert_drive_file\n</i>&emsp;<span>"+list[i]["name"] +
                "</span>&emsp;<a class=\"mdl-list__item-secondary-action\" id='"+list[i]["URL"]+"' ><i class=\"material-icons\">content_copy</i></a></span></li>"+str2
        }

    }
    str+=str2
    str+="</ul>"
    doc.innerHTML=str
}
if(main){
    main.ondrop=(e)=>sendFile(e)
    main.ondragover = () => {
        return false;
    };

    main.ondragleave = () => {
        return false;
    };

    main.ondragend = () => {
        return false;
    };
}
function historic() {
    const { ipcRenderer } = require('electron');

    // Some data that will be sent to the main process

    // Add the event listener for the response from the main process
    ipcRenderer.on('loadHistoricM', (event, arg) => {
        let doc =document.getElementById("page-content")
        var json = JSON.parse(arg);

        if(json.length>0){
            str=""
            str+="<ul class=\"demo-list-icon mdl-list\">"
            str2=""
            console.log(json[0])
            for(i in json){
                str2="<li class=\"mdl-list__item\"><span class=\"mdl-list__item-primary-content\">" +
                    "<i class=\"material-icons mdl-list__item-icon\">insert_drive_file\n</i>&emsp;<span>"+json[i]["name"] +
                    "</span>&emsp;<a class=\"mdl-list__item-secondary-action\" id='"+json[i]["URL"]+"' ><i class=\"material-icons\">content_copy</i></a></span></li>"+str2

            }
            str+=str2
            str+="</ul>"
            doc.innerHTML=str
            //Faire les listener sur l'id des noms pour le clipboard
            for( i in json){
                document.getElementById(json[i]["URL"]).addEventListener("onclick",ipcRenderer.send('clipboardR',json[i]["URL"]))
            }
            list=json
        }
    });
    ipcRenderer.send('loadHistoricR');
}
function sendFile(e) {
    const { ipcRenderer } = require('electron');
    e.preventDefault();

    // Some data that will be sent to the main process

    // Add the event listener for the response from the main process
    ipcRenderer.on('sendImageM', (event, arg) => {
        var snackbarContainer = document.querySelector('#demo-snackbar-example');
        var data = {
            message: 'File sent and link copied!',
            timeout: 2000,
            actionText: 'Undo'
        };
        var json = JSON.parse(arg);
        snackbarContainer.MaterialSnackbar.showSnackbar(data);
        ipcRenderer.send('clipboardR',json["URL"])
        ipcRenderer.send('loadHistoricR');
    });
    for (let f of e.dataTransfer.files) {
        ipcRenderer.send('sendImageR',f.path);
    }
}