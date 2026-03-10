import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from tkinterweb import HtmlFrame
from html.parser import HTMLParser
from urllib.request import urlopen
import random
import io
import contextlib

# =========================
# V1 COMPONENTS: Memory, Process, FileSystem
# =========================

# Memory Management (from v1)
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

# Process (from v1)
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
        self.next_pid = 1000

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

    def get(self, pid):
        return self.processes.get(pid)

# File System (from v1)
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

# HTML Title Parser (from v1)
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

# =========================
# V2 COMPONENTS: Window Manager
# =========================

class WindowManager:
    def __init__(self, root):
        self.root = root

    def open_window(self, title, width=700, height=500):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"{width}x{height}")
        return win

# =========================
# V2.1 KERNEL (Unified)
# =========================

class OhiOS:
    def __init__(self, root):
        self.root = root
        self.wm = WindowManager(root)
        
        # Initialize v1 components
        self.memory = Memory(2048)
        self.process_manager = ProcessManager()
        self.filesystem = FileSystem()
        
        root.title("ohiOS 2.1 Desktop")
        root.geometry("1200x700")

        # ===== Top Bar =====
        top_bar = tk.Frame(root, bg="#222")
        top_bar.pack(side="top", fill="x")
        tk.Label(top_bar, text="ohiOS 2.1", bg="#222", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        tk.Button(top_bar, text="Launch Browser", command=self.open_browser).pack(side="left", padx=5, pady=5)

        # ===== Bottom Bar (buttons) =====
        bottom_bar = tk.Frame(root, bg="#222")
        bottom_bar.pack(side="bottom", fill="x")

        buttons = [
            ("Browser", self.open_browser),
            ("Notepad", self.open_notepad),
            ("Python", self.open_python_runner),
            ("Memory", self.show_memory_window),
            ("PS", self.show_processes_window),
            ("File Mgr", self.show_filesystem_window),
            ("Help", self.show_help),
            ("Reset", self.reset_system),
            ("About", self.show_about)
        ]

        for text, cmd in buttons:
            tk.Button(bottom_bar, text=text, command=cmd, width=12).pack(side="left", padx=2, pady=4)

        # ===== Side Panels =====
        left_frame = tk.Frame(root)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(left_frame, text="Shell", bg="#333", fg="white").pack()
        self.shell = tk.Text(left_frame, bg="black", fg="lime", height=20, width=50)
        self.shell.pack(fill="both", expand=True)
        self.shell.bind("<Return>", self.handle_command)

        right_frame = tk.Frame(root)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(right_frame, text="GUI Output", bg="#333", fg="white").pack()
        self.gui = tk.Text(right_frame, bg="#111", fg="white", height=20, width=50)
        self.gui.pack(fill="both", expand=True)

        self.print_gui("Welcome to ohiOS 2.1")
        self.print_gui("Unified kernel with real memory & filesystem")
        self.print_gui("Type 'help' for shell commands")
        self.print_gui("")
        self.print_memory_info()

    # =========================
    # Utility
    # =========================
    
    def print_gui(self, text):
        self.gui.insert("end", text + "\n")
        self.gui.see("end")

    def print_memory_info(self):
        info = self.memory.get_info()
        self.print_gui(f"[MEM] {info['used']}/{info['total']} used | {info['free']} free")

    # =========================
    # Shell Commands
    # =========================
    
    def handle_command(self, event):
        cmd = self.shell.get("1.0", "end-1c").strip()
        self.shell.delete("1.0", "end")
        if cmd:
            self.print_gui(f"shell://$ {cmd}")
            self.execute(cmd)
        return "break"

    def execute(self, cmd):
        parts = cmd.split()
        if not parts:
            return
        
        command = parts[0].lower()

        try:
            if command == "help":
                self.show_help()
            elif command == "ls":
                for f in self.filesystem.list_dir():
                    self.print_gui(f"{'[DIR]' if f.is_dir else '[FILE]'} {f.name} ({f.size}B)")
            elif command == "mkfile":
                if len(parts) > 1:
                    result = self.filesystem.create_file(parts[1])
                    self.print_gui("File created." if result else "Already exists.")
                else:
                    self.print_gui("Usage: mkfile <name>")
            elif command == "write":
                if len(parts) > 2:
                    name = parts[1]
                    content = " ".join(parts[2:])
                    result = self.filesystem.write_file(name, content)
                    self.print_gui("Written." if result else "Write failed.")
                else:
                    self.print_gui("Usage: write <name> <content>")
            elif command == "read":
                if len(parts) > 1:
                    content = self.filesystem.read_file(parts[1])
                    self.print_gui(content if content else "File not found.")
                else:
                    self.print_gui("Usage: read <name>")
            elif command == "mkdir":
                if len(parts) > 1:
                    result = self.filesystem.mkdir(parts[1])
                    self.print_gui("Directory created." if result else "Already exists.")
                else:
                    self.print_gui("Usage: mkdir <name>")
            elif command == "delete":
                if len(parts) > 1:
                    result = self.filesystem.delete(parts[1])
                    self.print_gui("Deleted." if result else "Not found.")
                else:
                    self.print_gui("Usage: delete <name>")
            elif command == "mem":
                info = self.memory.get_info()
                self.print_gui(f"Memory: {info['used']}/{info['total']} used | {info['free']} free")
            elif command == "ps":
                procs = self.process_manager.list()
                if not procs:
                    self.print_gui("No running processes.")
                else:
                    for p in procs:
                        addr_str = f"@0x{p.memory_start:04x}" if p.memory_start else "@0x?????"
                        self.print_gui(f"{p.pid}: {p.name} [{p.memory_size}B] {addr_str}")
            elif command == "python":
                code = " ".join(parts[1:])
                try:
                    exec(code)
                    self.print_gui("Code executed.")
                except Exception as e:
                    self.print_gui(f"Error: {e}")
            elif command == "reset":
                self.reset_system()
            else:
                self.print_gui(f"Unknown command: {command}")
        except Exception as e:
            self.print_gui(f"Error: {e}")

    def show_help(self):
        self.print_gui("--- Shell Commands ---")
        self.print_gui("help - Show this help")
        self.print_gui("ls - List directory")
        self.print_gui("mkfile <name> - Create file")
        self.print_gui("write <name> <content> - Write to file")
        self.print_gui("read <name> - Read file")
        self.print_gui("mkdir <name> - Create directory")
        self.print_gui("delete <name> - Delete file/dir")
        self.print_gui("mem - Show memory info")
        self.print_gui("ps - List processes")
        self.print_gui("python <code> - Execute Python code")
        self.print_gui("reset - Reset system")

    def reset_system(self):
        self.shell.delete("1.0", "end")
        self.gui.delete("1.0", "end")
        self.memory = Memory(2048)
        self.process_manager = ProcessManager()
        self.filesystem = FileSystem()
        self.print_gui("System Reset Complete")
        self.print_gui("Welcome to ohiOS 2.1")

    def show_about(self):
        messagebox.showinfo("About", "ohiOS 2.1 Desktop\nHybrid OS Simulator\nv1 Internals + v2 UI")

    # =========================
    # Memory Window
    # =========================
    
    def show_memory_window(self):
        win = self.wm.open_window("Memory Manager", 600, 400)
        
        text = tk.Text(win, bg="#111", fg="white", font=("Courier", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh():
            text.delete("1.0", "end")
            info = self.memory.get_info()
            text.insert("end", f"Total Memory: {info['total']} bytes\n")
            text.insert("end", f"Used: {info['used']} bytes\n")
            text.insert("end", f"Free: {info['free']} bytes\n")
            text.insert("end", f"Usage: {(info['used']/info['total']*100):.1f}%\n\n")
            text.insert("end", "Allocations:\n")
            text.insert("end", "-" * 40 + "\n")
            for pid, (addr, size) in self.memory.allocations.items():
                proc = self.process_manager.get(pid)
                proc_name = proc.name if proc else f"PID{pid}"
                text.insert("end", f"0x{addr:04x}: {size:4d}B [{proc_name}]\n")
        
        refresh()
        
        tk.Button(win, text="Refresh", command=refresh).pack(pady=5)

    # =========================
    # Process Window
    # =========================
    
    def show_processes_window(self):
        win = self.wm.open_window("Process Manager", 600, 400)
        
        text = tk.Text(win, bg="#111", fg="white", font=("Courier", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh():
            text.delete("1.0", "end")
            procs = self.process_manager.list()
            if not procs:
                text.insert("end", "No running processes.\n")
            else:
                text.insert("end", f"{'PID':<6} {'Name':<20} {'Memory':<10} {'Address':<10}\n")
                text.insert("end", "-" * 50 + "\n")
                for p in procs:
                    addr_str = f"0x{p.memory_start:04x}" if p.memory_start else "None"
                    text.insert("end", f"{p.pid:<6} {p.name:<20} {p.memory_size:<10} {addr_str:<10}\n")
        
        refresh()
        
        tk.Button(win, text="Refresh", command=refresh).pack(pady=5)

    # =========================
    # Filesystem Window
    # =========================
    
    def show_filesystem_window(self):
        win = self.wm.open_window("File Manager", 700, 500)
        
        text = tk.Text(win, bg="#111", fg="white", font=("Courier", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh():
            text.delete("1.0", "end")
            text.insert("end", "Current Directory: /\n")
            text.insert("end", "-" * 50 + "\n")
            text.insert("end", f"{'Type':<8} {'Name':<30} {'Size':<10}\n")
            text.insert("end", "-" * 50 + "\n")
            for f in self.filesystem.list_dir():
                ftype = "DIR" if f.is_dir else "FILE"
                text.insert("end", f"{ftype:<8} {f.name:<30} {f.size:<10}\n")
        
        refresh()
        
        tk.Button(win, text="Refresh", command=refresh).pack(pady=5)

    # =========================
    # Applications
    # =========================

    # Browser
    def open_browser(self):
        name = "Browser"
        proc = self.process_manager.create(name, 256)
        addr = self.memory.allocate(256, proc.pid)
        if addr is None:
            self.print_gui(f"Not enough memory for {name}")
            self.process_manager.terminate(proc.pid)
            return
        proc.memory_start = addr
        
        win = self.wm.open_window(f"ohiOS Browser (PID {proc.pid})", 900, 600)

        top_frame = tk.Frame(win, bg="#333")
        top_frame.pack(fill="x")

        status_label = tk.Label(top_frame, text="Ready", bg="#333", fg="white")
        status_label.pack(side="right", padx=5)

        url_entry = tk.Entry(top_frame)
        url_entry.pack(side="left", fill="x", expand=True, padx=5)

        go_history = []

        frame = HtmlFrame(win, horizontal_scrollbar="auto")
        frame.pack(fill="both", expand=True)
        frame.load_website("https://example.com")

        def go_url(event=None):
            url = url_entry.get().strip()
            if not url:
                return
            status_label.config(text="Loading...")
            
            if any(url.endswith(s) for s in [".top", ".com", ".org", ".net", ".edu", ".gov"]):
                if not url.startswith("http://") and not url.startswith("https://"):
                    url = "https://" + url
                frame.load_website(url)
                go_history.append(url)
            else:
                search_url = "https://www.google.com/search?q=" + url.replace(" ", "+")
                frame.load_website(search_url)
                go_history.append(search_url)
            
            win.after(800, lambda: status_label.config(text="Ready"))

        def back():
            if len(go_history) > 1:
                go_history.pop()
                frame.load_website(go_history[-1])
                status_label.config(text="Ready")

        def on_close():
            self.memory.deallocate(proc.pid)
            self.process_manager.terminate(proc.pid)
            self.print_gui(f"Process {proc.pid} ({name}) terminated")
            win.destroy()

        tk.Button(top_frame, text="<-", command=back).pack(side="left", padx=2)
        tk.Button(top_frame, text="Go", command=go_url).pack(side="left", padx=2)
        url_entry.bind("<Return>", go_url)

        win.protocol("WM_DELETE_WINDOW", on_close)

    # Notepad
    def open_notepad(self):
        name = "Notepad"
        proc = self.process_manager.create(name, 128)
        addr = self.memory.allocate(128, proc.pid)
        if addr is None:
            self.print_gui(f"Not enough memory for {name}")
            self.process_manager.terminate(proc.pid)
            return
        proc.memory_start = addr
        
        win = self.wm.open_window(f"ohiOS Notepad (PID {proc.pid})", 700, 500)
        text = tk.Text(win, bg="white", fg="black")
        text.pack(fill="both", expand=True, padx=5, pady=5)

        def save_file():
            file = filedialog.asksaveasfilename(defaultextension=".txt")
            if file:
                with open(file, "w") as f:
                    f.write(text.get("1.0", "end"))
                self.print_gui(f"File saved: {file}")

        def on_close():
            self.memory.deallocate(proc.pid)
            self.process_manager.terminate(proc.pid)
            self.print_gui(f"Process {proc.pid} ({name}) terminated")
            win.destroy()

        tk.Button(win, text="Save", command=save_file).pack(pady=5)
        win.protocol("WM_DELETE_WINDOW", on_close)

    # Python Runner
    def open_python_runner(self):
        name = "Python"
        proc = self.process_manager.create(name, 200)
        addr = self.memory.allocate(200, proc.pid)
        if addr is None:
            self.print_gui(f"Not enough memory for {name}")
            self.process_manager.terminate(proc.pid)
            return
        proc.memory_start = addr
        
        win = self.wm.open_window(f"ohiOS Python Runner (PID {proc.pid})", 700, 600)

        code = tk.Text(win, height=15, bg="white", fg="black")
        code.pack(fill="both", expand=True, padx=5, pady=5)

        output = tk.Text(win, height=10, bg="black", fg="lime", font=("Courier", 10))
        output.pack(fill="both", expand=True, padx=5, pady=5)

        def run_code():
            output.delete("1.0", "end")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                try:
                    exec(code.get("1.0", "end"))
                except Exception as e:
                    print(e)
            output.insert("end", buffer.getvalue())

        def on_close():
            self.memory.deallocate(proc.pid)
            self.process_manager.terminate(proc.pid)
            self.print_gui(f"Process {proc.pid} ({name}) terminated")
            win.destroy()

        tk.Button(win, text="Run Code", command=run_code).pack(pady=5)
        win.protocol("WM_DELETE_WINDOW", on_close)

# =========================
# Launch ohiOS 2.1
# =========================

if __name__ == "__main__":
    root = tk.Tk()
    app = OhiOS(root)
    root.mainloop()
