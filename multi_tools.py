
import sublime
import sublime_plugin
import sys
import io
import uuid
import struct

preload_modules = ["math", "random", "re", "os"]
for module in preload_modules:
    exec("from %s import *" % module)

DEBUG = False


def log(*args, **kwds):
    if DEBUG:
        print(*args, **kwds)

MAXINT = 2 ** (struct.Struct('i').size * 8 - 1) - 1

variables = {
    "i":    lambda i: i + 1,
    "a":    lambda i: chr(i + 97),
    "A":    lambda i: chr(i + 65),
    "rd":   lambda i: random(),
    "ri":   lambda i: randint(-MAXINT - 1, MAXINT),
    "uuid": lambda i: uuid.uuid4(),
}

region_variables = {
    "s": lambda view, sel: view.substr(sel),
    "r": lambda view, sel: view.rowcol(sel.b)[0] + 1,
    "c": lambda view, sel: view.rowcol(sel.b)[1] + 1,
}


def evaluate(script, var):
    if not script:
        return ""
    locals().update(var)
    if script.count("\n") == 0:
        return str(eval(script, globals(), locals()))
    output = io.StringIO()
    ostdout = sys.stdout
    sys.stdout = output
    exec(script, globals(), locals())
    sys.stdout = ostdout
    return output.getvalue()


def generate_var_and_seletion(view):
    var = {}
    for i, sel in enumerate(view.sel()):
        for k, v in variables.items():
            var[k] = v(i)
        for k, v in region_variables.items():
            var[k] = v(view, sel)
        yield i, var, sel


class MultiEvaluateCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        for _, var, sel in generate_var_and_seletion(self.view):
            script = self.view.substr(sel)
            self.view.replace(edit, sel, evaluate(script, var))


class MultiInsertImplCommand(sublime_plugin.TextCommand):

    def run(self, edit, lines):
        lines_len = len(lines)
        for i, sel in enumerate(self.view.sel()):
            self.view.replace(edit, sel, lines[i % lines_len])


class MultiInsertCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.view.window().show_input_panel(
            "Inserted texts (separated by ctrl+enter):", "",
            lambda text: self.view.run_command(
                "multi_insert_impl", args={"lines": text.split('\n')}),
            None, None
        )


class MultiEvaluateAndInsertCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.view.window().show_input_panel(
            "Evaluated scripts (separated by ctrl+enter):", "",
            self.on_done,
            None, None
        )

    def on_done(self, scripts):
        scripts = scripts.split('\n')
        scripts_len = len(scripts)
        lines = []
        for i, var, sel in generate_var_and_seletion(self.view):
            lines.append(evaluate(scripts[i % scripts_len], var))
        self.view.run_command("multi_insert_impl", args={"lines": lines}),
