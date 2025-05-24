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

# Terminal Shell
class Shell:
    def __init__(self, os):
        self.os = os

    def run(self):
        print("=" * 50)
        print("Welcome to ohiOS Shell v1.0")
        print("Type 'help' for available commands")
        print("=" * 50)
        
        while True:
            try:
                current_path = self.os.filesystem.pwd()
                prompt = f"ohiOS:{current_path}$ "
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                self.execute_command(command)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit ohiOS")
            except EOFError:
                print("\nGoodbye!")
                break

    def execute_command(self, command):
        parts = command.split()
        cmd = parts[0].lower()

        try:
            if cmd == "help":
                self.show_help()
            elif cmd == "run":
                self.run_process(parts)
            elif cmd == "kill":
                self.kill_process(parts)
            elif cmd == "mem":
                self.show_memory()
            elif cmd == "ps":
                self.list_processes()
            elif cmd == "mkdir":
                self.make_directory(parts)
            elif cmd == "ls":
                self.list_directory()
            elif cmd == "cd":
                self.change_directory(parts)
            elif cmd == "pwd":
                self.print_working_dir()
            elif cmd == "mkfile":
                self.make_file(parts)
            elif cmd == "write":
                self.write_file(parts)
            elif cmd == "read":
                self.read_file(parts)
            elif cmd == "rm":
                self.delete_item(parts)
            elif cmd == "python":
                self.python_shell(command)
            elif cmd == "clear":
                self.clear_screen()
            elif cmd == "exit":
                print("Goodbye!")
                sys.exit(0)
            else:
                print(f"ohiOS: command not found: {cmd}")
                print("Type 'help' for available commands")
        except Exception as e:
            print(f"Error: {e}")

    def show_help(self):
        help_text = """
ohiOS Shell Commands:
  help             - Show this help message
  run name size    - Start a process with given memory size
  kill pid         - Terminate process by PID
  mem              - Show memory usage
  ps               - List running processes
  mkdir name       - Create directory
  ls               - List directory contents
  cd dirname       - Change directory (.. to go up)
  pwd              - Print working directory
  mkfile name      - Create a file
  write name text  - Write content to file
  read name        - Read file contents
  rm name          - Remove file or directory
  python code      - Execute Python code
  clear            - Clear screen
  exit             - Exit ohiOS
        """
        print(help_text)

    def run_process(self, parts):
        if len(parts) < 3:
            print("Usage: run process_name memory_size")
            return
        
        name, size = parts[1], int(parts[2])
        proc = self.os.process_manager.create(name, size)
        addr = self.os.memory.allocate(size, proc.pid)
        
        if addr is not None:
            proc.memory_start = addr
            print(f"Process '{name}' started (PID {proc.pid}) at memory address 0x{addr:04x}")
        else:
            self.os.process_manager.terminate(proc.pid)
            print(f"Failed to start '{name}': Not enough memory")

    def kill_process(self, parts):
        if len(parts) < 2:
            print("Usage: kill pid")
            return
        
        pid = int(parts[1])
        memory_freed = self.os.memory.deallocate(pid)
        process_terminated = self.os.process_manager.terminate(pid)
        
        if memory_freed and process_terminated:
            print(f"Process {pid} terminated")
        else:
            print(f"Process {pid} not found")

    def show_memory(self):
        info = self.os.memory.get_info()
        print(f"Memory Status:")
        print(f"  Total: {info['total']} bytes")
        print(f"  Used:  {info['used']} bytes")
        print(f"  Free:  {info['free']} bytes")
        print(f"  Usage: {(info['used']/info['total']*100):.1f}%")

    def list_processes(self):
        processes = self.os.process_manager.list()
        if processes:
            print("PID  NAME             MEMORY   ADDRESS")
            print("-" * 40)
            for p in processes:
                print(f"{p.pid:3d}  {p.name:<15} {p.memory_size:6d}B  0x{p.memory_start:04x}")
        else:
            print("No running processes")

    def make_directory(self, parts):
        if len(parts) < 2:
            print("Usage: mkdir directory_name")
            return
        
        name = parts[1]
        if self.os.filesystem.mkdir(name):
            print(f"Directory '{name}' created")
        else:
            print(f"mkdir: cannot create directory '{name}': File exists")

    def list_directory(self):
        files = self.os.filesystem.list_dir()
        
        if files:
            for f in files:
                if f.is_dir:
                    print(f"d {f.name}/")
                else:
                    print(f"- {f.name} ({f.size}B)")
        else:
            print("(empty directory)")

    def change_directory(self, parts):
        if len(parts) < 2:
            print("Usage: cd directory_name")
            return
        
        name = parts[1]
        if self.os.filesystem.cd(name):
            pass  # Success, no output like real shell
        else:
            print(f"cd: no such file or directory: {name}")

    def print_working_dir(self):
        print(self.os.filesystem.pwd())

    def make_file(self, parts):
        if len(parts) < 2:
            print("Usage: mkfile filename")
            return
        
        name = parts[1]
        if self.os.filesystem.create_file(name):
            print(f"File '{name}' created")
        else:
            print(f"mkfile: cannot create file '{name}': File exists")

    def write_file(self, parts):
        if len(parts) < 3:
            print("Usage: write filename content...")
            return
        
        name = parts[1]
        content = " ".join(parts[2:])
        
        if self.os.filesystem.write_file(name, content):
            print(f"{len(content)} bytes written to '{name}'")
        else:
            print(f"write: cannot write to '{name}': No such file")

    def read_file(self, parts):
        if len(parts) < 2:
            print("Usage: read filename")
            return
        
        name = parts[1]
        content = self.os.filesystem.read_file(name)
        
        if content is not None:
            print(content)
        else:
            print(f"read: cannot read '{name}': No such file or directory")

    def delete_item(self, parts):
        if len(parts) < 2:
            print("Usage: rm filename_or_dirname")
            return
        
        name = parts[1]
        if self.os.filesystem.delete(name):
            pass  # Success, no output like real shell
        else:
            print(f"rm: cannot remove '{name}': No such file or directory")

    def python_shell(self, command):
        code = command[7:].strip()  # everything after 'python '
        if not code:
            print("Usage: python code_to_execute")
            return
        
        output = self.run_python_code(code)
        if output:
            print(output)

    def run_python_code(self, code):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        sys.stderr = redirected_output
        
        try:
            exec(code, {})
            result = redirected_output.getvalue().strip()
            return result
        except Exception as e:
            return f"Python Error: {e}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def clear_screen(self):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

# Launch
if __name__ == "__main__":
    os = ohiOS()
    shell = Shell(os)
    shell.run()
