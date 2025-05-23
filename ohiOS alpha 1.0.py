import tkinter as tk
from tkinter import simpledialog
from urllib.request import urlopen
from html.parser import HTMLParser

# Memory
class Memory:
    def __init__(self, size):
        self.size = size
        self.used = 0
        self.allocations = {}

    def allocate(self, size, pid):
        if self.used + size <= self.size:
            addr = self.used
            self.allocations[pid] = (addr, size)
            self.used += size
            return addr
        return None

    def deallocate(self, pid):
        if pid in self.allocations:
            _, size = self.allocations.pop(pid)
            self.used -= size
            return True
        return False

    def get_info(self):
        return {"total": self.size, "used": self.used, "free": self.size - self.used}

# Process
class Process:
    def __init__(self, pid, name, memory_size):
        self.pid = pid
        self.name = name
        self.memory_size = memory_size
        self.memory_start = None
        self.state = "Running"

class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.next_pid = 1

    def create(self, name, memory_size):
        pid = self.next_pid
        self.next_pid += 1
        proc = Process(pid, name, memory_size)
        self.processes[pid] = proc
        return proc

    def terminate(self, pid):
        return self.processes.pop(pid, None)

    def list(self):
        return list(self.processes.values())

# File System
class File:
    def __init__(self, name, is_dir=False):
        self.name = name
        self.is_dir = is_dir
        self.content = "" if not is_dir else None
        self.size = 0
        self.children = {} if is_dir else None

class FileSystem:
    def __init__(self):
        self.root = File("/", True)
        self.cwd = self.root

    def list_dir(self):
        return list(self.cwd.children.values())

    def create_file(self, name):
        if name in self.cwd.children:
            return False
        self.cwd.children[name] = File(name)
        return True

    def write_file(self, name, content):
        f = self.cwd.children.get(name)
        if f and not f.is_dir:
            f.content = content
            f.size = len(content)
            return True
        return False

    def read_file(self, name):
        f = self.cwd.children.get(name)
        if f and not f.is_dir:
            return f.content
        return None

    def delete(self, name):
        if name in self.cwd.children:
            del self.cwd.children[name]
            return True
        return False

    def mkdir(self, name):
        if name in self.cwd.children:
            return False
        self.cwd.children[name] = File(name, True)
        return True

# HTML title parser for the "Internet" button
class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

# OS Core
class ohiOS:
    def __init__(self):
        self.memory = Memory(1024)
        self.process_manager = ProcessManager()
        self.filesystem = FileSystem()

# GUI + Shell
class OS_GUI:
    def __init__(self, root, os):
        self.root = root
        self.os = os
        root.title("ohiOS GUI + Shell")

        self.output = tk.Text(root, height=20, width=80)
        self.output.pack()
        self.log("Welcome to ohiOS", prefix="guioutput://")

        self.input = tk.Entry(root, width=80)
        self.input.pack()
        self.input.bind("<Return>", self.execute_shell_command)

        button_frame = tk.Frame(root)
        button_frame.pack()

        actions = [
            ("Run", self.run_process),
            ("Kill", self.kill_process),
            ("Memory", self.show_memory),
            ("Processes", self.list_processes),
            ("MkFile", self.create_file),
            ("Write", self.write_file),
            ("Read", self.read_file),
            ("Delete", self.delete_file),
            ("MkDir", self.make_directory),
            ("List Dir", self.list_directory),
            ("Python", self.run_python_code),
            ("Internet", self.fetch_website_title),
        ]
        for text, func in actions:
            tk.Button(button_frame, text=text, command=func, width=10).pack(side="left", padx=2, pady=5)

    def log(self, msg, prefix="guioutput://"):
        self.output.insert(tk.END, f"{prefix} {msg}\n")
        self.output.see(tk.END)

    def execute_shell_command(self, event=None):
        command = self.input.get().strip()
        self.input.delete(0, tk.END)
        self.log(f"{command}", prefix="shell://")

        parts = command.split()
        if not parts:
            return
        cmd = parts[0]

        try:
            if cmd == "ls":
                for f in self.os.filesystem.list_dir():
                    self.log(f"{'DIR' if f.is_dir else 'FILE'} {f.name} ({f.size}B)")
            elif cmd == "mkfile":
                self.log("File created." if self.os.filesystem.create_file(parts[1]) else "Already exists.")
            elif cmd == "write":
                name = parts[1]
                content = " ".join(parts[2:])
                self.log("Written." if self.os.filesystem.write_file(name, content) else "Write failed.")
            elif cmd == "read":
                content = self.os.filesystem.read_file(parts[1])
                self.log(content if content else "File not found.")
            elif cmd == "python":
                code = " ".join(parts[1:])
                try:
                    exec(code)
                    self.log("Python code executed.")
                except Exception as e:
                    self.log(f"Python Error: {e}")
            else:
                self.log("Unknown command.")
        except Exception as e:
            self.log(f"Error: {e}")

    def run_python_code(self):
        code = simpledialog.askstring("Python Code", "Enter Python code:")
        if code:
            try:
                exec(code)
                self.log("Code executed.")
            except Exception as e:
                self.log(f"Error: {e}")

    def fetch_website_title(self):
        url = simpledialog.askstring("Fetch Title", "Enter URL (http/https):")
        if url:
            try:
                with urlopen(url) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    parser = TitleParser()
                    parser.feed(content)
                    title = parser.title or "No title found"
                    self.log(f"Title: {title}")
            except Exception as e:
                self.log(f"Error fetching: {e}")

    # GUI buttons
    def run_process(self):
        name = simpledialog.askstring("Process Name", "Name:")
        size = simpledialog.askinteger("Memory", "Size:")
        if name and size:
            proc = self.os.process_manager.create(name, size)
            addr = self.os.memory.allocate(size, proc.pid)
            if addr is not None:
                proc.memory_start = addr
                self.log(f"Started {name} (PID {proc.pid}) at 0x{addr:04x}")
            else:
                self.os.process_manager.terminate(proc.pid)
                self.log("Not enough memory.")

    def kill_process(self):
        pid = simpledialog.askinteger("Kill PID", "PID:")
        if pid:
            ok = self.os.memory.deallocate(pid) and self.os.process_manager.terminate(pid)
            self.log(f"Process {pid} {'terminated' if ok else 'not found'}.")

    def show_memory(self):
        info = self.os.memory.get_info()
        self.log(f"Memory: {info['used']} used / {info['total']} total / {info['free']} free")

    def list_processes(self):
        for p in self.os.process_manager.list():
            self.log(f"{p.pid}: {p.name} [{p.memory_size}B] @0x{p.memory_start:04x}")

    def create_file(self):
        name = simpledialog.askstring("File Name", "File:")
        if name:
            self.log("File created." if self.os.filesystem.create_file(name) else "Already exists.")

    def write_file(self):
        name = simpledialog.askstring("File Name", "File:")
        content = simpledialog.askstring("Content", "Content:")
        if name and content is not None:
            self.log("Written." if self.os.filesystem.write_file(name, content) else "Write failed.")

    def read_file(self):
        name = simpledialog.askstring("Read File", "File:")
        if name:
            content = self.os.filesystem.read_file(name)
            self.log(content if content else "File not found.")

    def delete_file(self):
        name = simpledialog.askstring("Delete", "File/Dir:")
        if name:
            self.log("Deleted." if self.os.filesystem.delete(name) else "Not found.")

    def make_directory(self):
        name = simpledialog.askstring("Directory Name", "Directory:")
        if name:
            self.log("Directory created." if self.os.filesystem.mkdir(name) else "Already exists.")

    def list_directory(self):
        for f in self.os.filesystem.list_dir():
            self.log(f"{'DIR' if f.is_dir else 'FILE'} {f.name} ({f.size}B)")

# Launch the app
if __name__ == "__main__":
    root = tk.Tk()
    os = ohiOS()
    gui = OS_GUI(root, os)
    root.mainloop()
