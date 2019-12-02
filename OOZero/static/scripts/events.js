function decrypt(id){
    let password = document.getElementById("event_password" + id).value;
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            let data = JSON.parse(this.responseText);
            if(data["sucess"]){
                document.getElementById("description" + id).innerHTML = data['data'];
                document.getElementById("decryptForm" + id).style.display = "none";
                document.getElementById("editEvent" + id).style.display = "inline";
                document.getElementById("reEncrypt" + id).style.display = "inline";
            }else{
                document.getElementById("description" + id).innerHTML = '<span style="font-style: italic;color: red;">Incorrect Password<\span>';
            }
        }
    }
    xhttp.open("POST", 'decryptReq/' + id, true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.send("event_password=" + password);
}

function reEncrypt(id){
    let xhttp = new XMLHttpRequest();
    xhttp.open("POST", 'reEncryptReq/' + id, true);
    xhttp.send();
    document.getElementById("reEncrypt" + id).style.display = "none";
    document.getElementById("description" + id).innerHTML = "";
    document.getElementById("decryptForm" + id).style.display = "inline";
    document.getElementById("editEvent" + id).style.display = "none";
}