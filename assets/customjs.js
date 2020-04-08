// function copytoclipboard(smal_url) {
//     alert(smal_url + "Copied to ClipBoard")
// }i

function copyToClipboard(elementId) {

    // Create an auxiliary hidden input
    var aux = document.createElement("input");

    var inner_html = document.getElementById(elementId).innerHTML
    // Get the text from the element passed into the input
    aux.setAttribute("value", document.getElementById(elementId).innerHTML);

    // Append the aux input to the body
    document.body.appendChild(aux);

    // Highlight the content
    aux.select();


    // Execute the copy command
    document.execCommand("copy");

    // Remove the input from the body
    document.body.removeChild(aux);
    alert(inner_html + " Copied To Clipboard")


}

var myInterval = setInterval(function () {
    var tiny_url_element = document.getElementById('url-container');
    if (tiny_url_element.innerHTML === "") { return; }
    copyToClipboard('url-container')
    tiny_url_element.innerHTML = ""
}, 1000);