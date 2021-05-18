$(function () {
    var editor = CodeMirror.fromTextArea(document.getElementById("cow"), {
        styleActiveLine: true,
        lineNumbers: true,
        autofocus:true,
        matchBrackets: true,
        mode: "text/x-csrc"
    });
    $("#run").on("click", function () {
        $.post("/run", {"source": editor.getValue()}).done(function (resp) {
            var win = window.open(resp.link, "_blank");
            if (win) {
                win.focus();
            } else {
                alert("You should allow popups for this site");
            }
        });
    });
    $("#download").on("click", function () {
        $("#download").attr("href",
                            "data:application/octet-stream;charset=utf-8;base64;,"
                            + $.base64.encode(editor.getValue()));
    });
});
