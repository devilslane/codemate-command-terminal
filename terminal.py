import os
import sys
import subprocess
import shlex
import psutil
import platform
import time
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class PythonTerminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.command_history = []
        self.aliases = {
            'll': 'ls -la',
            'la': 'ls -a',
            'grep': 'findstr' if platform.system() == 'Windows' else 'grep'
        }
        self.environment_vars = dict(os.environ)
        
    def execute_command(self, command_line: str) -> Dict[str, Any]:
        """Execute a command and return structured result"""
        if not command_line.strip():
            return {"output": "", "error": "", "exit_code": 0}
            
        # Add to history
        self.command_history.append({
            "command": command_line,
            "timestamp": datetime.now().isoformat(),
            "directory": self.current_dir
        })
        
        # Parse command
        try:
            parts = shlex.split(command_line.strip())
        except ValueError as e:
            return {"output": "", "error": f"Parse error: {str(e)}", "exit_code": 1}
            
        if not parts:
            return {"output": "", "error": "", "exit_code": 0}
            
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Check for aliases
        if command in self.aliases:
            expanded = self.aliases[command]
            try:
                parts = shlex.split(expanded) + args
                command = parts[0].lower()
                args = parts[1:]
            except ValueError:
                pass
        
        # Built-in commands
        builtin_commands = {
            'cd': self._cmd_cd,
            'pwd': self._cmd_pwd,
            'ls': self._cmd_ls,
            'dir': self._cmd_ls,  # Windows compatibility
            'mkdir': self._cmd_mkdir,
            'rmdir': self._cmd_rmdir,
            'rm': self._cmd_rm,
            'del': self._cmd_rm,  # Windows compatibility
            'touch': self._cmd_touch,
            'cat': self._cmd_cat,
            'type': self._cmd_cat,  # Windows compatibility
            'cp': self._cmd_cp,
            'copy': self._cmd_cp,  # Windows compatibility
            'mv': self._cmd_mv,
            'move': self._cmd_mv,  # Windows compatibility
            'find': self._cmd_find,
            'ps': self._cmd_ps,
            'kill': self._cmd_kill,
            'top': self._cmd_top,
            'df': self._cmd_df,
            'du': self._cmd_du,
            'whoami': self._cmd_whoami,
            'date': self._cmd_date,
            'echo': self._cmd_echo,
            'env': self._cmd_env,
            'set': self._cmd_set,
            'export': self._cmd_export,
            'history': self._cmd_history,
            'clear': self._cmd_clear,
            'cls': self._cmd_clear,  # Windows compatibility
            'help': self._cmd_help,
            'alias': self._cmd_alias,
            'unalias': self._cmd_unalias,
            'which': self._cmd_which,
            'where': self._cmd_which,  # Windows compatibility
            'tree': self._cmd_tree,
            'wc': self._cmd_wc,
            'head': self._cmd_head,
            'tail': self._cmd_tail,
            'grep': self._cmd_grep,
            'findstr': self._cmd_grep,  # Windows compatibility
        }
        
        try:
            if command in builtin_commands:
                return builtin_commands[command](args)
            else:
                # Try to execute as system command
                return self._execute_system_command(command_line)
        except Exception as e:
            return {"output": "", "error": f"Error executing command: {str(e)}", "exit_code": 1}
    
    def _cmd_cd(self, args: List[str]) -> Dict[str, Any]:
        """Change directory command"""
        if not args:
            # Go to home directory
            target = os.path.expanduser("~")
        elif args[0] == "-":
            # Go to previous directory (simplified)
            target = os.path.expanduser("~")
        else:
            target = args[0]
            
        target = os.path.expanduser(target)
        if not os.path.isabs(target):
            target = os.path.join(self.current_dir, target)
            
        target = os.path.normpath(target)
        
        if os.path.isdir(target):
            self.current_dir = target
            os.chdir(target)
            return {"output": "", "error": "", "exit_code": 0}
        else:
            return {"output": "", "error": f"cd: {target}: No such directory", "exit_code": 1}
    
    def _cmd_pwd(self, args: List[str]) -> Dict[str, Any]:
        """Print working directory command"""
        return {"output": self.current_dir, "error": "", "exit_code": 0}
    
    def _cmd_ls(self, args: List[str]) -> Dict[str, Any]:
        """List directory contents"""
        show_all = "-a" in args or "-la" in args or "-al" in args
        long_format = "-l" in args or "-la" in args or "-al" in args
        
        # Remove flags from args to get directory path
        path_args = [arg for arg in args if not arg.startswith("-")]
        target_dir = path_args[0] if path_args else self.current_dir
        
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.current_dir, target_dir)
            
        try:
            if os.path.isfile(target_dir):
                # List single file
                if long_format:
                    stat = os.stat(target_dir)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%b %d %H:%M")
                    mode = oct(stat.st_mode)[-3:]
                    return {"output": f"-rw-r--r-- 1 user user {size:>8} {mtime} {os.path.basename(target_dir)}", "error": "", "exit_code": 0}
                else:
                    return {"output": os.path.basename(target_dir), "error": "", "exit_code": 0}
            
            items = os.listdir(target_dir)
            if not show_all:
                items = [item for item in items if not item.startswith('.')]
                
            items.sort()
            
            if long_format:
                output_lines = []
                for item in items:
                    item_path = os.path.join(target_dir, item)
                    try:
                        stat = os.stat(item_path)
                        is_dir = os.path.isdir(item_path)
                        size = stat.st_size if not is_dir else 4096
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%b %d %H:%M")
                        mode_char = "d" if is_dir else "-"
                        permissions = "rwxr-xr-x" if is_dir else "rw-r--r--"
                        output_lines.append(f"{mode_char}{permissions} 1 user user {size:>8} {mtime} {item}")
                    except OSError:
                        output_lines.append(f"?????????? ? ?    ?        ?            ? {item}")
                return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
            else:
                # Simple format - arrange in columns
                if not items:
                    return {"output": "", "error": "", "exit_code": 0}
                return {"output": "  ".join(items), "error": "", "exit_code": 0}
                
        except PermissionError:
            return {"output": "", "error": f"ls: cannot access '{target_dir}': Permission denied", "exit_code": 1}
        except FileNotFoundError:
            return {"output": "", "error": f"ls: cannot access '{target_dir}': No such file or directory", "exit_code": 1}
    
    def _cmd_mkdir(self, args: List[str]) -> Dict[str, Any]:
        """Create directory command"""
        if not args:
            return {"output": "", "error": "mkdir: missing operand", "exit_code": 1}
            
        recursive = "-p" in args
        dirs = [arg for arg in args if not arg.startswith("-")]
        
        errors = []
        for dir_name in dirs:
            if not os.path.isabs(dir_name):
                dir_path = os.path.join(self.current_dir, dir_name)
            else:
                dir_path = dir_name
                
            try:
                if recursive:
                    os.makedirs(dir_path, exist_ok=True)
                else:
                    os.mkdir(dir_path)
            except FileExistsError:
                errors.append(f"mkdir: cannot create directory '{dir_name}': File exists")
            except OSError as e:
                errors.append(f"mkdir: cannot create directory '{dir_name}': {str(e)}")
                
        if errors:
            return {"output": "", "error": "\n".join(errors), "exit_code": 1}
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_rmdir(self, args: List[str]) -> Dict[str, Any]:
        """Remove empty directory command"""
        if not args:
            return {"output": "", "error": "rmdir: missing operand", "exit_code": 1}
            
        errors = []
        for dir_name in args:
            if not os.path.isabs(dir_name):
                dir_path = os.path.join(self.current_dir, dir_name)
            else:
                dir_path = dir_name
                
            try:
                os.rmdir(dir_path)
            except OSError as e:
                errors.append(f"rmdir: failed to remove '{dir_name}': {str(e)}")
                
        if errors:
            return {"output": "", "error": "\n".join(errors), "exit_code": 1}
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_rm(self, args: List[str]) -> Dict[str, Any]:
        """Remove files/directories command"""
        if not args:
            return {"output": "", "error": "rm: missing operand", "exit_code": 1}
            
        recursive = "-r" in args or "-rf" in args
        force = "-f" in args or "-rf" in args
        files = [arg for arg in args if not arg.startswith("-")]
        
        errors = []
        for file_name in files:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                if os.path.isdir(file_path):
                    if recursive:
                        import shutil
                        shutil.rmtree(file_path)
                    else:
                        errors.append(f"rm: cannot remove '{file_name}': Is a directory")
                else:
                    os.remove(file_path)
            except OSError as e:
                if not force:
                    errors.append(f"rm: cannot remove '{file_name}': {str(e)}")
                    
        if errors:
            return {"output": "", "error": "\n".join(errors), "exit_code": 1}
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_touch(self, args: List[str]) -> Dict[str, Any]:
        """Create empty file or update timestamp"""
        if not args:
            return {"output": "", "error": "touch: missing operand", "exit_code": 1}
            
        for file_name in args:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                Path(file_path).touch()
            except OSError as e:
                return {"output": "", "error": f"touch: cannot touch '{file_name}': {str(e)}", "exit_code": 1}
                
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_cat(self, args: List[str]) -> Dict[str, Any]:
        """Display file contents"""
        if not args:
            return {"output": "", "error": "cat: missing operand", "exit_code": 1}
            
        output_lines = []
        for file_name in args:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    output_lines.append(f.read().rstrip())
            except OSError as e:
                return {"output": "", "error": f"cat: {file_name}: {str(e)}", "exit_code": 1}
                
        return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
    
    def _cmd_cp(self, args: List[str]) -> Dict[str, Any]:
        """Copy files/directories"""
        if len(args) < 2:
            return {"output": "", "error": "cp: missing operand", "exit_code": 1}
            
        recursive = "-r" in args
        files = [arg for arg in args if not arg.startswith("-")]
        
        if len(files) < 2:
            return {"output": "", "error": "cp: missing operand", "exit_code": 1}
            
        source_files = files[:-1]
        dest = files[-1]
        
        if not os.path.isabs(dest):
            dest_path = os.path.join(self.current_dir, dest)
        else:
            dest_path = dest
            
        try:
            import shutil
            if len(source_files) == 1:
                src = source_files[0]
                if not os.path.isabs(src):
                    src_path = os.path.join(self.current_dir, src)
                else:
                    src_path = src
                    
                if os.path.isdir(src_path):
                    if recursive:
                        if os.path.exists(dest_path):
                            dest_path = os.path.join(dest_path, os.path.basename(src_path))
                        shutil.copytree(src_path, dest_path)
                    else:
                        return {"output": "", "error": f"cp: -r not specified; omitting directory '{src}'", "exit_code": 1}
                else:
                    if os.path.isdir(dest_path):
                        dest_path = os.path.join(dest_path, os.path.basename(src_path))
                    shutil.copy2(src_path, dest_path)
            else:
                # Multiple sources - destination must be directory
                if not os.path.isdir(dest_path):
                    return {"output": "", "error": f"cp: target '{dest}' is not a directory", "exit_code": 1}
                    
                for src in source_files:
                    if not os.path.isabs(src):
                        src_path = os.path.join(self.current_dir, src)
                    else:
                        src_path = src
                    
                    if os.path.isdir(src_path) and recursive:
                        shutil.copytree(src_path, os.path.join(dest_path, os.path.basename(src_path)))
                    elif os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)
                        
        except OSError as e:
            return {"output": "", "error": f"cp: {str(e)}", "exit_code": 1}
            
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_mv(self, args: List[str]) -> Dict[str, Any]:
        """Move/rename files"""
        if len(args) < 2:
            return {"output": "", "error": "mv: missing operand", "exit_code": 1}
            
        source_files = args[:-1]
        dest = args[-1]
        
        if not os.path.isabs(dest):
            dest_path = os.path.join(self.current_dir, dest)
        else:
            dest_path = dest
            
        try:
            import shutil
            if len(source_files) == 1:
                src = source_files[0]
                if not os.path.isabs(src):
                    src_path = os.path.join(self.current_dir, src)
                else:
                    src_path = src
                    
                if os.path.isdir(dest_path):
                    dest_path = os.path.join(dest_path, os.path.basename(src_path))
                shutil.move(src_path, dest_path)
            else:
                # Multiple sources - destination must be directory
                if not os.path.isdir(dest_path):
                    return {"output": "", "error": f"mv: target '{dest}' is not a directory", "exit_code": 1}
                    
                for src in source_files:
                    if not os.path.isabs(src):
                        src_path = os.path.join(self.current_dir, src)
                    else:
                        src_path = src
                    shutil.move(src_path, dest_path)
                    
        except OSError as e:
            return {"output": "", "error": f"mv: {str(e)}", "exit_code": 1}
            
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_find(self, args: List[str]) -> Dict[str, Any]:
        """Find files and directories"""
        if not args:
            search_dir = self.current_dir
            pattern = "*"
        elif len(args) == 1:
            if os.path.isdir(args[0]):
                search_dir = args[0]
                pattern = "*"
            else:
                search_dir = self.current_dir
                pattern = args[0]
        else:
            search_dir = args[0]
            pattern = args[1]
            
        if not os.path.isabs(search_dir):
            search_dir = os.path.join(self.current_dir, search_dir)
            
        results = []
        try:
            import fnmatch
            for root, dirs, files in os.walk(search_dir):
                for name in files + dirs:
                    if fnmatch.fnmatch(name, pattern):
                        results.append(os.path.join(root, name))
        except OSError as e:
            return {"output": "", "error": f"find: {str(e)}", "exit_code": 1}
            
        return {"output": "\n".join(results), "error": "", "exit_code": 0}
    
    def _cmd_ps(self, args: List[str]) -> Dict[str, Any]:
        """List running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'],
                        'memory': pinfo['memory_info'].rss if pinfo['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu'] or 0, reverse=True)
            
            output_lines = ["PID     NAME                 CPU%    MEMORY"]
            output_lines.append("-" * 50)
            
            for proc in processes[:20]:  # Show top 20
                memory_mb = proc['memory'] / (1024 * 1024)
                cpu_str = f"{proc['cpu']:.1f}%" if proc['cpu'] else "0.0%"
                output_lines.append(f"{proc['pid']:<8} {proc['name']:<20} {cpu_str:<8} {memory_mb:.1f}MB")
                
            return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
            
        except Exception as e:
            return {"output": "", "error": f"ps: {str(e)}", "exit_code": 1}
    
    def _cmd_kill(self, args: List[str]) -> Dict[str, Any]:
        """Kill process by PID"""
        if not args:
            return {"output": "", "error": "kill: missing operand", "exit_code": 1}
            
        try:
            pid = int(args[0])
            proc = psutil.Process(pid)
            proc.terminate()
            return {"output": f"Process {pid} terminated", "error": "", "exit_code": 0}
        except ValueError:
            return {"output": "", "error": f"kill: invalid PID '{args[0]}'", "exit_code": 1}
        except psutil.NoSuchProcess:
            return {"output": "", "error": f"kill: no such process: {args[0]}", "exit_code": 1}
        except psutil.AccessDenied:
            return {"output": "", "error": f"kill: permission denied: {args[0]}", "exit_code": 1}
    
    def _cmd_top(self, args: List[str]) -> Dict[str, Any]:
        """Display system resource usage"""
        try:
            # System info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            output_lines = [
                f"System: {platform.system()} {platform.release()}",
                f"CPU Usage: {cpu_percent:.1f}%",
                f"Memory: {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB ({memory.percent:.1f}%)",
                f"Disk: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB ({disk.percent:.1f}%)",
                "",
                "Top Processes:",
                "PID     NAME                 CPU%    MEMORY"
            ]
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'],
                        'memory': pinfo['memory_info'].rss if pinfo['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            processes.sort(key=lambda x: x['cpu'] or 0, reverse=True)
            
            for proc in processes[:10]:
                memory_mb = proc['memory'] / (1024 * 1024)
                cpu_str = f"{proc['cpu']:.1f}%" if proc['cpu'] else "0.0%"
                output_lines.append(f"{proc['pid']:<8} {proc['name']:<20} {cpu_str:<8} {memory_mb:.1f}MB")
                
            return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
            
        except Exception as e:
            return {"output": "", "error": f"top: {str(e)}", "exit_code": 1}
    
    def _cmd_df(self, args: List[str]) -> Dict[str, Any]:
        """Display filesystem disk space usage"""
        try:
            output_lines = ["Filesystem      Size  Used Avail Use% Mounted on"]
            
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = partition_usage.total / (1024**3)
                    used_gb = partition_usage.used / (1024**3)
                    free_gb = partition_usage.free / (1024**3)
                    percent = (partition_usage.used / partition_usage.total) * 100
                    
                    output_lines.append(
                        f"{partition.device:<15} {total_gb:>5.1f}G {used_gb:>5.1f}G {free_gb:>5.1f}G {percent:>3.0f}% {partition.mountpoint}"
                    )
                except PermissionError:
                    continue
                    
            return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
            
        except Exception as e:
            return {"output": "", "error": f"df: {str(e)}", "exit_code": 1}
    
    def _cmd_du(self, args: List[str]) -> Dict[str, Any]:
        """Display directory space usage"""
        target_dir = args[0] if args else self.current_dir
        
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.current_dir, target_dir)
            
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(target_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
                        
            size_mb = total_size / (1024 * 1024)
            return {"output": f"{size_mb:.1f}M\t{target_dir}", "error": "", "exit_code": 0}
            
        except OSError as e:
            return {"output": "", "error": f"du: {str(e)}", "exit_code": 1}
    
    def _cmd_whoami(self, args: List[str]) -> Dict[str, Any]:
        """Display current username"""
        import getpass
        return {"output": getpass.getuser(), "error": "", "exit_code": 0}
    
    def _cmd_date(self, args: List[str]) -> Dict[str, Any]:
        """Display current date and time"""
        return {"output": datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"), "error": "", "exit_code": 0}
    
    def _cmd_echo(self, args: List[str]) -> Dict[str, Any]:
        """Echo arguments"""
        return {"output": " ".join(args), "error": "", "exit_code": 0}
    
    def _cmd_env(self, args: List[str]) -> Dict[str, Any]:
        """Display environment variables"""
        output_lines = []
        for key, value in sorted(self.environment_vars.items()):
            output_lines.append(f"{key}={value}")
        return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
    
    def _cmd_set(self, args: List[str]) -> Dict[str, Any]:
        """Set environment variable (Windows style)"""
        if not args:
            return self._cmd_env(args)
            
        if "=" in args[0]:
            key, value = args[0].split("=", 1)
            self.environment_vars[key] = value
            return {"output": "", "error": "", "exit_code": 0}
        else:
            return {"output": "", "error": "set: invalid format", "exit_code": 1}
    
    def _cmd_export(self, args: List[str]) -> Dict[str, Any]:
        """Export environment variable (Unix style)"""
        if not args:
            return self._cmd_env(args)
            
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                self.environment_vars[key] = value
            else:
                # Export existing variable
                if arg in os.environ:
                    self.environment_vars[arg] = os.environ[arg]
                    
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_history(self, args: List[str]) -> Dict[str, Any]:
        """Display command history"""
        output_lines = []
        for i, entry in enumerate(self.command_history[-50:], 1):  # Show last 50
            output_lines.append(f"{i:>4}  {entry['command']}")
        return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
    
    def _cmd_clear(self, args: List[str]) -> Dict[str, Any]:
        """Clear screen command"""
        return {"output": "CLEAR_SCREEN", "error": "", "exit_code": 0}
    
    def _cmd_help(self, args: List[str]) -> Dict[str, Any]:
        """Display help information"""
        help_text = """
Built-in Commands:
  cd <dir>          Change directory
  pwd               Print working directory
  ls [-la] [dir]    List directory contents
  mkdir [-p] <dir>  Create directory
  rmdir <dir>       Remove empty directory
  rm [-rf] <file>   Remove files/directories
  touch <file>      Create empty file
  cat <file>        Display file contents
  cp [-r] <src> <dst> Copy files/directories
  mv <src> <dst>    Move/rename files
  find [dir] [pattern] Find files
  ps                List processes
  kill <pid>        Kill process
  top               System resource usage
  df                Disk space usage
  du [dir]          Directory space usage
  whoami            Current user
  date              Current date/time
  echo <text>       Echo text
  env               Environment variables
  export VAR=value  Set environment variable
  history           Command history
  clear/cls         Clear screen
  help              This help message
  
File Operations:
  head <file>       Show first lines of file
  tail <file>       Show last lines of file
  wc <file>         Word/line/character count
  grep <pattern> <file> Search in file
  tree [dir]        Display directory tree
  
System Monitoring:
  ps                Process list
  top               Real-time system stats
  kill <pid>        Terminate process
  df                Disk usage
  du <dir>          Directory size
  
Aliases and Variables:
  alias name=cmd    Create command alias
  unalias name      Remove alias  
  which <cmd>       Find command location
  export VAR=val    Set environment variable
"""
        return {"output": help_text.strip(), "error": "", "exit_code": 0}
    
    def _cmd_alias(self, args: List[str]) -> Dict[str, Any]:
        """Create command alias"""
        if not args:
            # Show all aliases
            output_lines = []
            for name, command in self.aliases.items():
                output_lines.append(f"alias {name}='{command}'")
            return {"output": "\n".join(output_lines), "error": "", "exit_code": 0}
            
        for arg in args:
            if "=" in arg:
                name, command = arg.split("=", 1)
                self.aliases[name] = command.strip("'\"")
            else:
                return {"output": "", "error": f"alias: invalid format '{arg}'", "exit_code": 1}
                
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_unalias(self, args: List[str]) -> Dict[str, Any]:
        """Remove command alias"""
        if not args:
            return {"output": "", "error": "unalias: missing operand", "exit_code": 1}
            
        for name in args:
            if name in self.aliases:
                del self.aliases[name]
            else:
                return {"output": "", "error": f"unalias: {name}: not found", "exit_code": 1}
                
        return {"output": "", "error": "", "exit_code": 0}
    
    def _cmd_which(self, args: List[str]) -> Dict[str, Any]:
        """Find command location"""
        if not args:
            return {"output": "", "error": "which: missing operand", "exit_code": 1}
            
        command = args[0]
        
        # Check built-in commands
        builtin_commands = [
            'cd', 'pwd', 'ls', 'dir', 'mkdir', 'rmdir', 'rm', 'del', 'touch',
            'cat', 'type', 'cp', 'copy', 'mv', 'move', 'find', 'ps', 'kill',
            'top', 'df', 'du', 'whoami', 'date', 'echo', 'env', 'set', 'export',
            'history', 'clear', 'cls', 'help', 'alias', 'unalias', 'which',
            'where', 'tree', 'wc', 'head', 'tail', 'grep', 'findstr'
        ]
        
        if command in builtin_commands:
            return {"output": f"{command}: shell builtin", "error": "", "exit_code": 0}
        
        # Check aliases
        if command in self.aliases:
            return {"output": f"{command}: aliased to '{self.aliases[command]}'", "error": "", "exit_code": 0}
        
        # Check system PATH
        import shutil
        path = shutil.which(command)
        if path:
            return {"output": path, "error": "", "exit_code": 0}
        else:
            return {"output": "", "error": f"which: {command}: not found", "exit_code": 1}
    
    def _cmd_tree(self, args: List[str]) -> Dict[str, Any]:
        """Display directory tree"""
        target_dir = args[0] if args else self.current_dir
        
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.current_dir, target_dir)
            
        if not os.path.isdir(target_dir):
            return {"output": "", "error": f"tree: {target_dir}: No such directory", "exit_code": 1}
        
        def build_tree(directory, prefix="", max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return []
                
            items = []
            try:
                entries = sorted(os.listdir(directory))
                for i, entry in enumerate(entries):
                    if entry.startswith('.'):
                        continue
                        
                    path = os.path.join(directory, entry)
                    is_last = i == len(entries) - 1
                    current_prefix = "└── " if is_last else "├── "
                    items.append(prefix + current_prefix + entry)
                    
                    if os.path.isdir(path):
                        extension = "    " if is_last else "│   "
                        items.extend(build_tree(path, prefix + extension, max_depth, current_depth + 1))
            except PermissionError:
                items.append(prefix + "├── [Permission Denied]")
                
            return items
        
        tree_lines = [target_dir] + build_tree(target_dir)
        return {"output": "\n".join(tree_lines), "error": "", "exit_code": 0}
    
    def _cmd_wc(self, args: List[str]) -> Dict[str, Any]:
        """Word, line, character count"""
        if not args:
            return {"output": "", "error": "wc: missing operand", "exit_code": 1}
            
        results = []
        for file_name in args:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    lines = content.count('\n')
                    words = len(content.split())
                    chars = len(content)
                    results.append(f"{lines:8} {words:8} {chars:8} {file_name}")
            except OSError as e:
                return {"output": "", "error": f"wc: {file_name}: {str(e)}", "exit_code": 1}
                
        return {"output": "\n".join(results), "error": "", "exit_code": 0}
    
    def _cmd_head(self, args: List[str]) -> Dict[str, Any]:
        """Show first lines of file"""
        lines = 10
        files = []
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    lines = int(args[i + 1])
                    i += 2
                except ValueError:
                    return {"output": "", "error": f"head: invalid number '{args[i + 1]}'", "exit_code": 1}
            elif args[i].startswith("-"):
                try:
                    lines = int(args[i][1:])
                    i += 1
                except ValueError:
                    return {"output": "", "error": f"head: invalid option '{args[i]}'", "exit_code": 1}
            else:
                files.append(args[i])
                i += 1
        
        if not files:
            return {"output": "", "error": "head: missing operand", "exit_code": 1}
            
        results = []
        for file_name in files:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_lines = f.readlines()
                    results.extend(file_lines[:lines])
            except OSError as e:
                return {"output": "", "error": f"head: {file_name}: {str(e)}", "exit_code": 1}
                
        return {"output": "".join(results).rstrip(), "error": "", "exit_code": 0}
    
    def _cmd_tail(self, args: List[str]) -> Dict[str, Any]:
        """Show last lines of file"""
        lines = 10
        files = []
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    lines = int(args[i + 1])
                    i += 2
                except ValueError:
                    return {"output": "", "error": f"tail: invalid number '{args[i + 1]}'", "exit_code": 1}
            elif args[i].startswith("-"):
                try:
                    lines = int(args[i][1:])
                    i += 1
                except ValueError:
                    return {"output": "", "error": f"tail: invalid option '{args[i]}'", "exit_code": 1}
            else:
                files.append(args[i])
                i += 1
        
        if not files:
            return {"output": "", "error": "tail: missing operand", "exit_code": 1}
            
        results = []
        for file_name in files:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_lines = f.readlines()
                    results.extend(file_lines[-lines:] if lines <= len(file_lines) else file_lines)
            except OSError as e:
                return {"output": "", "error": f"tail: {file_name}: {str(e)}", "exit_code": 1}
                
        return {"output": "".join(results).rstrip(), "error": "", "exit_code": 0}
    
    def _cmd_grep(self, args: List[str]) -> Dict[str, Any]:
        """Search for pattern in files"""
        if len(args) < 2:
            return {"output": "", "error": "grep: missing operand", "exit_code": 1}
            
        pattern = args[0]
        files = args[1:]
        
        results = []
        for file_name in files:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_dir, file_name)
            else:
                file_path = file_name
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            results.append(f"{file_name}:{line_num}:{line.rstrip()}")
            except OSError as e:
                return {"output": "", "error": f"grep: {file_name}: {str(e)}", "exit_code": 1}
                
        return {"output": "\n".join(results), "error": "", "exit_code": 0}
    
    def _execute_system_command(self, command_line: str) -> Dict[str, Any]:
        """Execute system command"""
        try:
            result = subprocess.run(
                command_line,
                shell=True,
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=30,
                env=self.environment_vars
            )
            
            return {
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"output": "", "error": "Command timed out", "exit_code": 124}
        except Exception as e:
            return {"output": "", "error": f"Command not found: {str(e)}", "exit_code": 127}
    
    def get_prompt(self) -> str:
        """Generate command prompt"""
        user = os.getenv('USER', os.getenv('USERNAME', 'user'))
        hostname = platform.node()
        current_dir = self.current_dir
        
        # Shorten path if too long
        if len(current_dir) > 30:
            current_dir = "..." + current_dir[-27:]
            
        return f"{user}@{hostname}:{current_dir}$ "
    
    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command auto-completion suggestions"""
        builtin_commands = [
            'cd', 'pwd', 'ls', 'dir', 'mkdir', 'rmdir', 'rm', 'del', 'touch',
            'cat', 'type', 'cp', 'copy', 'mv', 'move', 'find', 'ps', 'kill',
            'top', 'df', 'du', 'whoami', 'date', 'echo', 'env', 'set', 'export',
            'history', 'clear', 'cls', 'help', 'alias', 'unalias', 'which',
            'where', 'tree', 'wc', 'head', 'tail', 'grep', 'findstr'
        ]
        
        suggestions = []
        
        # Built-in command suggestions
        for cmd in builtin_commands:
            if cmd.startswith(partial_command.lower()):
                suggestions.append(cmd)
        
        # Alias suggestions
        for alias in self.aliases.keys():
            if alias.startswith(partial_command.lower()):
                suggestions.append(alias)
        
        # File/directory suggestions for the current directory
        if partial_command and not any(partial_command.startswith(cmd) for cmd in builtin_commands):
            try:
                for item in os.listdir(self.current_dir):
                    if item.startswith(partial_command):
                        suggestions.append(item)
            except OSError:
                pass
        
        return sorted(suggestions)


# CLI Interface
class CLIInterface:
    def __init__(self):
        self.terminal = PythonTerminal()
        
    def run(self):
        """Run the CLI interface"""
        print("Python Terminal v1.0")
        print("Type 'help' for available commands, 'exit' to quit.")
        print()
        
        try:
            while True:
                try:
                    prompt = self.terminal.get_prompt()
                    command = input(prompt).strip()
                    
                    if command.lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        break
                    
                    if command:
                        result = self.terminal.execute_command(command)
                        
                        if result['output']:
                            if result['output'] == 'CLEAR_SCREEN':
                                os.system('cls' if platform.system() == 'Windows' else 'clear')
                            else:
                                print(result['output'])
                        
                        if result['error']:
                            print(f"Error: {result['error']}", file=sys.stderr)
                            
                except KeyboardInterrupt:
                    print("\n^C")
                    continue
                except EOFError:
                    print("\nGoodbye!")
                    break
                    
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr)
            sys.exit(1)


# Example usage
if __name__ == "__main__":
    # Create and run CLI interface
    cli = CLIInterface()
    cli.run()