// Generated by CoffeeScript 1.12.8
(function() {
  var create, download, editor, lang, remove, rename, run, wait;

  editor = {
    instances: {},
    nextid: 0,
    active: function() {
      var item, label, name, num;
      num = $("#tabs").tabs("option", "active");
      item = $("#tabs > ul :nth-child(" + (num + 1) + ")").first();
      label = item.find("tt").first();
      name = label.text();
      return {
        number: num,
        li: item,
        tt: label,
        filename: name,
        codemirror: editor.instances[name],
        tab: item.children("a").attr("href")
      };
    },
    rename: function(name) {
      var info;
      info = editor.active();
      editor.instances[name] = info.codemirror;
      delete editor.instances[info.filename];
      return info.tt.html(name);
    },
    create: function(name) {
      var ed, num, ul;
      ul = $("#tabs > ul");
      num = editor.nextid = editor.nextid + 1;
      ul.before("<div id='tabs-" + num + "'></div>");
      ul.append("<li><a href='#tabs-" + num + "'><tt>" + name + "</tt></a></li>");
      ed = CodeMirror(document.getElementById("tabs-" + num), {
        styleActiveLine: true,
        lineNumbers: true,
        autofocus: true,
        matchBrackets: true,
        mode: "text/x-csrc"
      });
      editor.instances[name] = ed;
      $("#tabs").tabs("refresh");
      return $("#tabs").tabs("option", "active", -1);
    },
    remove: function() {
      var info;
      info = editor.active();
      if (editor.instances[info.filename] == null) {
        console.log("cow error: could not delete " + info.filename);
      }
      delete editor.instances[info.filename];
      $("" + info.tab).remove();
      info.li.remove();
      return $("#tabs").tabs("refresh");
    },
    init: function() {
      $("#tabs").tabs().addClass("ui-helper-clearfix");
      return $("#tabs li").removeClass("ui-corner-top").addClass("ui-corner-right");
    }
  };

  lang = {
    "do": function() {
      var code, name, ref;
      ref = $("#lang-select").val().split("/", 2), code = ref[0], name = ref[1];
      $("#lang img").attr({
        alt: name,
        title: name + " (change)",
        src: "static/img/" + code + ".png"
      });
      lang.dialog.dialog("close");
      return window.location.href = "/" + code;
    },
    on_click: function() {
      return lang.dialog.dialog("open");
    },
    on_submit: function() {
      event.preventDefault();
      return lang["do"]();
    },
    init: function() {
      lang.dialog = $("#lang-dialog-confirm").dialog({
        autoOpen: false,
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          Yes: lang["do"],
          No: function() {
            return lang.dialog.dialog("close");
          }
        }
      });
      return $("#lang").on("click", lang.on_click);
    }
  };

  create = {
    "do": function() {
      var name;
      name = create.field.val();
      editor.create(name);
      return create.dialog.dialog("close");
    },
    on_click: function() {
      var name, num;
      name = "newfile{{ LANG_EXT[0] }}";
      num = 1;
      while (editor.instances[name] != null) {
        name = "newfile-" + num + "{{ LANG_EXT[0] }}";
        num += 1;
      }
      create.field.val(name);
      return create.dialog.dialog("open");
    },
    on_submit: function() {
      event.preventDefault();
      return create["do"]();
    },
    init: function() {
      create.field = $("#create-field");
      create.dialog = $("#create-dialog-form").dialog({
        autoOpen: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          Create: create["do"],
          Cancel: function() {
            return create.dialog.dialog("close");
          }
        },
        close: function() {
          return create.form[0].reset();
        }
      });
      create.form = create.dialog.find("form").on("submit", create.on_submit);
      return $("#new").on("click", create.on_click);
    }
  };

  rename = {
    "do": function() {
      var name;
      name = rename.field.val();
      editor.rename(name);
      return rename.dialog.dialog("close");
    },
    on_click: function() {
      rename.field.val(editor.active().filename);
      return rename.dialog.dialog("open");
    },
    on_submit: function() {
      event.preventDefault();
      return rename["do"]();
    },
    init: function() {
      rename.field = $("#rename-field");
      rename.dialog = $("#rename-dialog-form").dialog({
        autoOpen: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          Rename: rename["do"],
          Cancel: function() {
            return rename.dialog.dialog("close");
          }
        },
        close: function() {
          return rename.form[0].reset();
        }
      });
      rename.form = rename.dialog.find("form").on("submit", rename.on_submit);
      return $("#rename").on("click", rename.on_click);
    }
  };

  remove = {
    "do": function() {
      editor.remove();
      return remove.dialog.dialog("close");
    },
    on_click: function() {
      return remove.dialog.dialog("open");
    },
    on_submit: function() {
      event.preventDefault();
      return remove["do"]();
    },
    init: function() {
      remove.dialog = $("#remove-dialog-confirm").dialog({
        autoOpen: false,
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          Yes: remove["do"],
          No: function() {
            return remove.dialog.dialog("close");
          }
        }
      });
      return $("#remove").on("click", remove.on_click);
    }
  };

  download = {
    on_click: function() {
      var codemirror, filename, ref, source;
      source = {};
      ref = editor.instances;
      for (filename in ref) {
        codemirror = ref[filename];
        source[filename] = codemirror.getValue();
      }
      return $.post("/dl/{{ LANG }}", source).done(download.on_done);
    },
    init: function() {
      download.dialog = $("#download-dialog-message").dialog({
        autoOpen: false,
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          OK: function() {
            return download.dialog.dialog("close");
          }
        }
      });
      return $("#download").on("click", download.on_click);
    },
    on_done: function(resp) {
      var link;
      if (resp.status === "OK") {
        link = $("<a id=\"zipdl\" download=\"" + resp.filename + "\" href=\"data:application/octet-stream;charset=utf-8;base64;," + resp.data + "\">" + resp.filename + "</a>");
        $("#download-message").html(link);
        link.click(function() {
          return download.dialog.dialog("close");
        });
        return download.dialog.dialog("open");
      }
    }
  };

  wait = {
    init: function() {
      wait.bar = $("#waitbar");
      wait.bar.progressbar({
        value: false
      });
      return wait.dialog = $("#wait-dialog").dialog({
        autoOpen: false,
        resizable: false,
        height: "auto",
        width: 400,
        modal: true
      });
    }
  };

  run = {
    on_click: function() {
      var codemirror, filename, ref, source;
      wait.dialog.dialog("open");
      source = {};
      ref = editor.instances;
      for (filename in ref) {
        codemirror = ref[filename];
        source[filename] = codemirror.getValue();
      }
      return $.post("/run/{{ LANG }}", source).done(run.on_done);
    },
    on_done: function(resp) {
      var win;
      wait.dialog.dialog("close");
      if (resp.status === "OK") {
        win = window.open(resp.link, "_blank");
        if (win != null) {
          win.focus();
          return;
        }
        resp.status = "Your browser has blocked a popup.<br/>You should allow popups for this site";
      }
      $("#run-message").html(resp.status);
      return run.dialog.dialog("open");
    },
    init: function() {
      run.dialog = $("#run-dialog-message").dialog({
        autoOpen: false,
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
          OK: function() {
            return run.dialog.dialog("close");
          }
        }
      });
      return $("#run").on("click", run.on_click);
    }
  };

  $(function() {
    editor.init();
    lang.init();
    rename.init();
    create.init();
    remove.init();
    wait.init();
    download.init();
    run.init();
    return editor.create("main{{ LANG_EXT[0] }}");
  });

}).call(this);
