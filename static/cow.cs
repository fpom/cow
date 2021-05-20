editor =
    instances : {}
    nextid : 0
    active : () ->
        num = $("#tabs").tabs("option", "active")
        item = $("#tabs > ul :nth-child(#{ num+1 })").first()
        label = item.find("tt").first()
        name = label.text()
        return
            number : num
            li : item
            tt : label
            filename : name
            codemirror : editor.instances[name]
            tab : item.children("a").attr("href")
    rename : (name) ->
        info = editor.active()
        editor.instances[name] = info.codemirror
        delete editor.instances[info.filename]
        info.tt.html(name)
    create : (name) ->
        ul = $("#tabs > ul")
        num = editor.nextid = editor.nextid + 1
        ul.before("<div id='tabs-#{ num }'></div>")
        ul.append("<li><a href='#tabs-#{ num }'><tt>#{ name }</tt></a></li>")
        ed = CodeMirror(document.getElementById("tabs-#{ num }"),
            styleActiveLine : true
            lineNumbers : true
            autofocus : true
            matchBrackets : true
            mode : "text/x-csrc")
        editor.instances[name] = ed
        $("#tabs").tabs("refresh")
        $("#tabs").tabs("option", "active", -1)
    remove : () ->
        info = editor.active()
        if not editor.instances[info.filename]?
            console.log("cow error: could not delete #{ info.filename }")
        delete editor.instances[info.filename]
        $("#{ info.tab }").remove()
        info.li.remove()
        $("#tabs").tabs("refresh")
    init : () ->
        $("#tabs").tabs().addClass("ui-helper-clearfix");
        $("#tabs li").removeClass("ui-corner-top").addClass("ui-corner-right");

create =
    do : () ->
        name = create.field.val()
        if not name.match /\.c$/
            name = "#{ name }.c"
        editor.create(name)
        create.dialog.dialog("close")
    on_click : () ->
        name = "newfile.c"
        num = 1
        while editor.instances[name]?
            name = "newfile-#{ num }.c"
            num += 1
        create.field.val(name)
        create.dialog.dialog("open")
    on_submit : () ->
        event.preventDefault()
        create.do()
    init : () ->
        create.field = $("#create-field")
        create.dialog = $("#create-dialog-form").dialog
            autoOpen : false
            height : "auto"
            width : 400
            modal : true
            buttons :
                Create : create.do
                Cancel : () ->
                    create.dialog.dialog("close")
            close : () ->
                create.form[0].reset()
        create.form = create.dialog.find("form").on("submit", create.on_submit)
        $("#new").on("click", create.on_click)

rename =
    do : () ->
        name = rename.field.val()
        if not name.match /\.c$/
            name = "#{ name }.c"
        editor.rename(name)
        rename.dialog.dialog("close")
    on_click : () ->
        rename.field.val(editor.active().filename)
        rename.dialog.dialog("open")
    on_submit : () ->
        event.preventDefault()
        rename.do()
    init : () ->
        rename.field = $("#rename-field")
        rename.dialog = $("#rename-dialog-form").dialog
            autoOpen : false
            height : "auto"
            width : 400
            modal : true
            buttons :
                Rename : rename.do
                Cancel : () ->
                    rename.dialog.dialog("close")
            close : () ->
                rename.form[0].reset()
        rename.form = rename.dialog.find("form").on("submit", rename.on_submit)
        $("#rename").on("click", rename.on_click)

remove =
    do : () ->
        editor.remove()
        remove.dialog.dialog("close")
    on_click : () ->
        remove.dialog.dialog("open")
    on_submit : () ->
        event.preventDefault()
        remove.do()
    init : () ->
        remove.dialog = $("#remove-dialog-confirm").dialog
            autoOpen : false
            resizable : false
            height : "auto"
            width : 400
            modal : true
            buttons :
                Yes : remove.do
                No : () ->
                  remove.dialog.dialog("close")
        $("#remove").on("click", remove.on_click)

download =
    on_click : () ->
        info = editor.active()
        $("#download")
            .attr("download", info.filename)
            .attr("href",
                  "data:application/octet-stream;charset=utf-8;base64;,\
                    #{ $.base64.encode(info.codemirror.getValue()) }")
    init : () ->
        $("#download").on("click", download.on_click)

run =
    on_click : () ->
        source = {}
        for filename, codemirror of editor.instances
            console.log filename, codemirror
            source[filename] = codemirror.getValue()
        $.post("/run", source).done(run.on_done)
    on_done : (resp) ->
        win = window.open(resp.link, "_blank")
        if win?
            win.focus()
        else
            alert("You should allow popups for this site")
    init : () ->
        $("#run").on("click", run.on_click)

$ ->
    editor.init()
    rename.init()
    create.init()
    remove.init()
    download.init()
    run.init()
    editor.create("main.c")
