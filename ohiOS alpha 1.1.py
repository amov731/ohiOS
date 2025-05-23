import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import sys
import io

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
        self.path_stack = [self.root]

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

    def cd(self, name):
        if name == "..":
            if len(self.path_stack) > 1:
                self.path_stack.pop()
                self.cwd = self.path_stack[-1]
                return True
            else:
                return False
        elif name in self.cwd.children and self.cwd.children[name].is_dir:
            self.cwd = self.cwd.children[name]
            self.path_stack.append(self.cwd)
            return True
        else:
            return False

    def pwd(self):
        names = []
        for dir in self.path_stack:
            if dir.name != "/":
                names.append(dir.name)
        return "/" + "/".join(names)

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

        # Shell Output Label
        tk.Label(root, text="shell://").pack()
        self.shell_output = tk.Text(root, height=15, width=80)
        self.shell_output.pack()

        # Shell Input
        self.shell_input = tk.Entry(root, width=80)
        self.shell_input.pack()
        self.shell_input.bind("<Return>", self.execute_shell_command)

        # GUI Output Label
        tk.Label(root, text="guioutput://").pack()
        self.gui_output = tk.Text(root, height=10, width=80)
        self.gui_output.pack()

        button_frame = tk.Frame(root)
        button_frame.pack()

        actions = [
            ("Run", self.run_process),
            ("Kill", self.kill_process),
            ("Memory", self.show_memory),
            ("Processes", self.list_processes),
            ("MkDir", self.make_directory),
            ("List Dir", self.list_directory),
            ("CD", self.change_directory),
            ("PWD", self.print_working_dir),
            ("MkTxtFile", self.make_txt_file),
            ("Write", self.write_file),
            ("Read", self.read_file),
            ("Delete", self.delete_file),
            ("Python", self.python_shell),
            ("Internet", self.internet_popup),
        ]
        for text, func in actions:
            tk.Button(button_frame, text=text, command=func, width=10).pack(side="left", padx=2, pady=5)

    def log_shell(self, msg):
        self.shell_output.insert(tk.END, msg + "\n")
        self.shell_output.see(tk.END)

    def log_gui(self, msg):
        self.gui_output.insert(tk.END, msg + "\n")
        self.gui_output.see(tk.END)

    def execute_shell_command(self, event=None):
        command = self.shell_input.get().strip()
        self.shell_input.delete(0, tk.END)
        self.log_shell(f"ohiOS> {command}")
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()

        try:
            if cmd == "/help":
                self.log_shell("Commands: /help, run name size, kill pid, mem, ps, mkdir name, ls, cd dir, pwd, python code..., internet, mkTxtFile name, write name content, read name, del name")
            elif cmd == "run":
                name, size = parts[1], int(parts[2])
                proc = self.os.process_manager.create(name, size)
                addr = self.os.memory.allocate(size, proc.pid)
                if addr is not None:
                    proc.memory_start = addr
                    self.log_shell(f"Started {name} (PID {proc.pid}) at 0x{addr:04x}")
                else:
                    self.os.process_manager.terminate(proc.pid)
                    self.log_shell("Not enough memory.")
            elif cmd == "kill":
                pid = int(parts[1])
                ok = self.os.memory.deallocate(pid) and self.os.process_manager.terminate(pid)
                self.log_shell(f"Process {pid} {'terminated' if ok else 'not found'}")
            elif cmd == "mem":
                info = self.os.memory.get_info()
                self.log_shell(f"Memory: {info['used']} used / {info['total']} total / {info['free']} free")
            elif cmd == "ps":
                for p in self.os.process_manager.list():
                    self.log_shell(f"{p.pid}: {p.name} [{p.memory_size}B] @0x{p.memory_start:04x}")
            elif cmd == "mkdir":
                name = parts[1]
                self.log_shell("Directory created." if self.os.filesystem.mkdir(name) else "Already exists.")
            elif cmd == "ls":
                for f in self.os.filesystem.list_dir():
                    self.log_shell(f"{'DIR' if f.is_dir else 'FILE'} {f.name} ({f.size}B)")
            elif cmd == "cd":
                if len(parts) < 2:
                    self.log_shell("Usage: cd dirname")
                else:
                    success = self.os.filesystem.cd(parts[1])
                    self.log_shell("Changed directory." if success else "Directory not found.")
            elif cmd == "pwd":
                self.log_shell(self.os.filesystem.pwd())
            elif cmd == "mktxtfile":
                if len(parts) < 2:
                    self.log_shell("Usage: mkTxtFile filename")
                else:
                    self.make_txt_file(parts[1])
            elif cmd == "write":
                if len(parts) < 3:
                    self.log_shell("Usage: write filename content...")
                else:
                    name = parts[1]
                    content = " ".join(parts[2:])
                    self.log_shell("File written." if self.os.filesystem.write_file(name, content) else "Write failed.")
            elif cmd == "read":
                if len(parts) < 2:
                    self.log_shell("Usage: read filename")
                else:
                    name = parts[1]
                    content = self.os.filesystem.read_file(name)
                    self.log_shell(content if content else "File not found.")
            elif cmd == "del":
                if len(parts) < 2:
                    self.log_shell("Usage: del filename")
                else:
                    name = parts[1]
                    self.log_shell("Deleted." if self.os.filesystem.delete(name) else "Not found.")
            elif cmd == "python":
                code = command[7:].strip()  # everything after 'python '
                if code:
                    output = self.run_python_code(code)
                    self.log_shell(output)
                else:
                    self.log_shell("Usage: python code")
            elif cmd == "internet":
                self.internet_popup()
            else:
                self.log_shell("Unknown command.")
        except Exception as e:
            self.log_shell(f"Error: {e}")

    def run_python_code(self, code):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        sys.stderr = redirected_output
        try:
            exec(code, {})
            return redirected_output.getvalue().strip() or "Code executed."
        except Exception as e:
            return f"Error: {e}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    # GUI Button functions - All now output to GUI area

    def run_process(self):
        name = simpledialog.askstring("Process Name", "Enter process name:")
        size = simpledialog.askinteger("Memory", "Enter memory size:")
        if name and size:
            proc = self.os.process_manager.create(name, size)
            addr = self.os.memory.allocate(size, proc.pid)
            if addr is not None:
                proc.memory_start = addr
                self.log_gui(f"[GUI] Started {name} (PID {proc.pid}) at 0x{addr:04x}")
            else:
                self.os.process_manager.terminate(proc.pid)
                self.log_gui("[GUI] Not enough memory to start process.")

    def kill_process(self):
        pid = simpledialog.askinteger("Kill PID", "Enter PID:")
        if pid:
            ok = self.os.memory.deallocate(pid) and self.os.process_manager.terminate(pid)
            self.log_gui(f"[GUI] Process {pid} {'terminated' if ok else 'not found'}.")

    def show_memory(self):
        info = self.os.memory.get_info()
        self.log_gui(f"[GUI] Memory Status: {info['used']}B used / {info['total']}B total / {info['free']}B free")

    def list_processes(self):
        processes = self.os.process_manager.list()
        if processes:
            self.log_gui("[GUI] Running Processes:")
            for p in processes:
                self.log_gui(f"  PID {p.pid}: {p.name} [{p.memory_size}B] @0x{p.memory_start:04x}")
        else:
            self.log_gui("[GUI] No running processes.")

    def make_directory(self):
        name = simpledialog.askstring("Directory Name", "Enter directory name:")
        if name:
            result = self.os.filesystem.mkdir(name)
            self.log_gui(f"[GUI] Directory '{name}' {'created successfully' if result else 'already exists'}.")

    def list_directory(self):
        files = self.os.filesystem.list_dir()
        current_path = self.os.filesystem.pwd()
        self.log_gui(f"[GUI] Contents of {current_path}:")
        if files:
            for f in files:
                file_type = "DIR" if f.is_dir else "FILE"
                self.log_gui(f"  {file_type} {f.name} ({f.size}B)")
        else:
            self.log_gui("  (empty directory)")

    def change_directory(self):
        name = simpledialog.askstring("Change Directory", "Enter directory name (.. to go up):")
        if name:
            success = self.os.filesystem.cd(name)
            if success:
                new_path = self.os.filesystem.pwd()
                self.log_gui(f"[GUI] Changed directory to: {new_path}")
            else:
                self.log_gui(f"[GUI] Directory '{name}' not found.")

    def print_working_dir(self):
        current_path = self.os.filesystem.pwd()
        self.log_gui(f"[GUI] Current directory: {current_path}")

    def make_txt_file(self, filename=None):
        if filename is None:
            filename = simpledialog.askstring("Make .txt File", "Enter text file name (without extension):")
            if not filename:
                return
            filename += ".txt"
        else:
            if not filename.endswith(".txt"):
                filename += ".txt"
        
        # Create in filesystem
        if filename in self.os.filesystem.cwd.children:
            self.log_gui(f"[GUI] File '{filename}' already exists.")
            return
        
        success = self.os.filesystem.create_file(filename)
        if success:
            self.log_gui(f"[GUI] Created text file: {filename}")
            
            # Optional: Save to disk
            save_to_disk = messagebox.askyesno("Save to Disk", f"Save '{filename}' to your computer?")
            if save_to_disk:
                filepath = filedialog.asksaveasfilename(
                    title="Save Text File As", 
                    defaultextension=".txt", 
                    initialfile=filename,
                    filetypes=[("Text Files", "*.txt")]
                )
                if filepath:
                    try:
                        with open(filepath, "w") as f:
                            f.write("")  # empty file
                        self.log_gui(f"[GUI] File saved to disk: {filepath}")
                    except Exception as e:
                        self.log_gui(f"[GUI] Error saving to disk: {e}")
        else:
            self.log_gui(f"[GUI] Failed to create file: {filename}")

    def write_file(self):
        name = simpledialog.askstring("File Name", "Enter file name:")
        if not name:
            return
        
        if name not in self.os.filesystem.cwd.children:
            self.log_gui(f"[GUI] File '{name}' does not exist.")
            return
        
        content = simpledialog.askstring("Content", "Enter content to write:")
        if content is None:
            return
        
        success = self.os.filesystem.write_file(name, content)
        if success:
            self.log_gui(f"[GUI] Content written to '{name}' ({len(content)} bytes)")
            
            # Optional: Save to disk
            save_to_disk = messagebox.askyesno("Save to Disk", f"Save '{name}' to your computer?")
            if save_to_disk:
                filepath = filedialog.asksaveasfilename(title="Save File As", initialfile=name)
                if filepath:
                    try:
                        with open(filepath, "w") as f:
                            f.write(content)
                        self.log_gui(f"[GUI] File saved to disk: {filepath}")
                    except Exception as e:
                        self.log_gui(f"[GUI] Error saving to disk: {e}")
        else:
            self.log_gui(f"[GUI] Failed to write to file: {name}")

    def read_file(self):
        name = simpledialog.askstring("Read File", "Enter file name:")
        if name:
            content = self.os.filesystem.read_file(name)
            if content is not None:
                self.log_gui(f"[GUI] Contents of '{name}':")
                self.log_gui(f"--- BEGIN FILE ---")
                self.log_gui(content)
                self.log_gui(f"--- END FILE ---")
            else:
                self.log_gui(f"[GUI] File '{name}' not found or is a directory.")

    def delete_file(self):
        name = simpledialog.askstring("Delete File", "Enter file/directory name:")
        if name:
            success = self.os.filesystem.delete(name)
            if success:
                self.log_gui(f"[GUI] Deleted: {name}")
            else:
                self.log_gui(f"[GUI] File/directory '{name}' not found.")

    def python_shell(self):
        code = simpledialog.askstring("Python Shell", "Enter python code to run:")
        if code:
            self.log_gui(f"[GUI] Executing Python: {code}")
            output = self.run_python_code(code)
            self.log_gui(f"[GUI] Python Output:")
            self.log_gui(output)

    def internet_popup(self):
        query = simpledialog.askstring("Internet Search", "Enter your search query:")
        if query:
            self.log_gui(f"[GUI] Searching for: {query}")
            # Enhanced fake search results
            results = [
                f"Wikipedia: {query} - The free encyclopedia",
                f"{query} - Official Website",
                f"How to {query} - Tutorial Guide",
                f"{query} News - Latest Updates",
                f"{query} Forum - Community Discussion"
            ]
            self.log_gui("[GUI] Search Results:")
            for i, result in enumerate(results, 1):
                self.log_gui(f"  {i}. {result}")
            self.log_gui(f"[GUI] Found {len(results)} results for '{query}'")

# Launch
if __name__ == "__main__":
    root = tk.Tk()
    os = ohiOS()
    gui = OS_GUI(root, os)
    root.mainloop()