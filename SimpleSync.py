# -*- coding: utf-8 -*-

import fnmatch
import os
import shlex
import signal
import subprocess
import threading

import sublime
import sublime_plugin


PACKAGE_NAME = "SimpleSync"
PACKAGE_SETTINGS = PACKAGE_NAME + ".sublime-settings"


class SimpleSyncCommand(sublime_plugin.EventListener):
    @property
    def settings(self):
        return sublime.load_settings(PACKAGE_SETTINGS)

    def on_post_save_async(self, view):
        if not view:
            return

        projects = self.settings.get("projects", [])

        for project in projects:

            local = project.get("local")
            remote = project.get("remote")

            if not local or not remote:
                continue

            # build full local and remote path
            local_path = view.file_name()
            if not local_path or not local_path.startswith(local):
                continue
            remote_path = remote + local_path.replace(local, "")

            # ignore the file if it matches any exclusion patterns
            patterns = project.get("excludes", [])
            for p in patterns:
                _p = "{}*".format(p) if p.startswith("/") else "*{}*".format(p)
                if fnmatch.fnmatch(local_path, _p):
                    return

            # extend PATH to execute commands outside default system PATH
            path = project.get("path", "")
            path = os.pathsep.join((os.path.expanduser(path), os.environ.get("PATH", "")))

            # 10s timeout by default
            timeout = project.get("timeout", 10)

            commands = project.get("commands", [])
            for cmd in commands:
                cmd = cmd.format(local=local_path, remote=remote_path)
                print("{}: Execute:".format(PACKAGE_NAME), cmd)
                Command(cmd).run(timeout, env=dict(PATH=path))


class Command(object):

    def __init__(self, cmd):
        self.cmd = shlex.split(cmd)
        self.process = None

    def run(self, timeout=10, env=None):

        def target():
            self.process = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, preexec_fn=os.setsid)
            stdout, stderr = self.process.communicate()
            print("{}: Retcode: {} STDOUT: {} STDERR: {}"
                    .format(PACKAGE_NAME, self.process.returncode, stdout, stderr))

        thread = threading.Thread(target=target)
        thread.start()

        ThreadProgress(thread, PACKAGE_NAME,
                       success_message="{} Completed".format(PACKAGE_NAME),
                       failure_message="{} Failed".format(PACKAGE_NAME))

        thread.join(timeout)
        if thread.is_alive():
            print("{}: Timedout".format(PACKAGE_NAME))
            self.terminate()

        thread.ok = self.process.returncode == 0

        return self.process.returncode

    def terminate(self):
        return os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)


class ThreadProgress(object):
    """
    Animates an indicator, [=   ], in the status area while a thread runs

    :param thread:
        The thread to track for activity

    :param message:
        The message to display next to the activity indicator

    :param success_message:
        The message to display once the thread is completed
    """

    def __init__(self, thread, message, success_message="Completed", failure_message="Failed"):
        self.thread = thread
        self.message = message
        self.success_message = success_message
        self.failure_message = failure_message
        self.addend = 1
        self.size = 8
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if not self.thread.is_alive():
            if hasattr(self.thread, "ok") and not self.thread.ok:
                return sublime.status_message(self.failure_message)
            return sublime.status_message(self.success_message)

        before = i % self.size
        after = (self.size - 1) - before

        sublime.status_message("%s [%s=%s]" % \
            (self.message, " " * before, " " * after))

        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend

        sublime.set_timeout(lambda: self.run(i), 100)
