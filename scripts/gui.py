#!/usr/bin/env python3
"""视频剪辑工作流图形界面。

用法：
  python3 scripts/gui.py

可选参数：
  --no-popup   不显示启动署名弹窗，便于截图或自动化检查。
"""
import argparse
import subprocess
import sys
import threading
from pathlib import Path

import ctypes
try:
    ctypes.CDLL("libX11.so.6").XInitThreads()
except OSError:
    pass

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

AUTHOR_QQ = "230154231"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class WorkflowGUI:
    def __init__(self, root: tk.Tk, show_popup: bool = True):
        self.root = root
        self.root.title("视频剪辑工作流")
        self.root.geometry("920x680")
        self.root.minsize(820, 600)

        self.src_dir = tk.StringVar(value="./footage")
        self.work_dir = tk.StringVar(value="./output/clips")
        self.shots_file = tk.StringVar(value="./shots.json")
        self.output_file = tk.StringVar(value="./output/master.mp4")
        self.buttons = []

        self._build_ui()
        if show_popup:
            self.root.after(300, self.show_author_popup)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="视频剪辑工作流", font=("sans-serif", 18, "bold")).pack(anchor=tk.W)

        form = ttk.LabelFrame(outer, text="路径配置", padding=12)
        form.pack(fill=tk.X, pady=(12, 0))
        form.columnconfigure(1, weight=1)

        self._path_row(form, 0, "素材目录", self.src_dir, self.choose_src)
        self._path_row(form, 1, "片段目录", self.work_dir, self.choose_work)
        self._path_row(form, 2, "镜头清单", self.shots_file, self.choose_shots)
        self._path_row(form, 3, "成片文件", self.output_file, self.choose_output)

        actions = ttk.LabelFrame(outer, text="操作", padding=12)
        actions.pack(fill=tk.X, pady=12)
        for column in range(4):
            actions.columnconfigure(column, weight=1)

        for column, (text, command) in enumerate([
            ("抽帧网格", self.run_grid),
            ("生成片段", self.run_clips),
            ("拼接视频", self.run_join),
            ("成片终验", self.run_verify),
        ]):
            button = ttk.Button(actions, text=text, command=command)
            button.grid(row=0, column=column, padx=4, sticky="ew")
            self.buttons.append(button)

        log_frame = ttk.LabelFrame(outer, text="运行日志", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_list = tk.Listbox(log_frame, height=14, activestyle="none")
        self.log_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_list.configure(yscrollcommand=scrollbar.set)

        ttk.Label(outer, text=f"作者QQ：{AUTHOR_QQ}", anchor=tk.W).pack(fill=tk.X, pady=(10, 0))

    def _path_row(self, parent, row, label, variable, command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Label(parent, textvariable=variable, wraplength=560).grid(
            row=row, column=1, sticky=tk.EW, padx=8, pady=4
        )
        ttk.Button(parent, text="浏览", command=command).grid(row=row, column=2, sticky=tk.E, pady=4)

    def choose_src(self):
        value = filedialog.askdirectory(
            initialdir=str(self.resolve_path(self.src_dir.get())), title="选择素材目录"
        )
        if value:
            self.src_dir.set(value)

    def choose_work(self):
        value = filedialog.askdirectory(
            initialdir=str(self.resolve_path(self.work_dir.get())), title="选择片段输出目录"
        )
        if value:
            self.work_dir.set(value)

    def choose_shots(self):
        resolved = self.resolve_path(self.shots_file.get())
        value = filedialog.askopenfilename(
            initialfile=resolved.name,
            initialdir=str(resolved.parent),
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            title="选择镜头清单",
        )
        if value:
            self.shots_file.set(value)

    def choose_output(self):
        resolved = self.resolve_path(self.output_file.get())
        value = filedialog.asksaveasfilename(
            initialfile=resolved.name,
            initialdir=str(resolved.parent),
            defaultextension=".mp4",
            filetypes=[("MP4 视频", "*.mp4"), ("所有文件", "*.*")],
            title="选择成片输出位置",
        )
        if value:
            self.output_file.set(value)

    def show_author_popup(self):
        messagebox.showinfo("署名", f"作者QQ：{AUTHOR_QQ}")

    def append_log(self, text):
        self.log_list.insert(tk.END, text)
        self.log_list.see(tk.END)

    def set_busy(self, busy):
        state = tk.DISABLED if busy else tk.NORMAL
        for button in self.buttons:
            button.configure(state=state)

    def script_path(self, name):
        return str(PROJECT_ROOT / "scripts" / name)

    def resolve_path(self, value):
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    def validate_paths(self, require_shots=True):
        if not self.resolve_path(self.src_dir.get()).exists():
            messagebox.showerror("路径错误", "素材目录不存在。")
            return False
        self.resolve_path(self.work_dir.get()).mkdir(parents=True, exist_ok=True)
        if require_shots and not self.resolve_path(self.shots_file.get()).exists():
            messagebox.showerror("路径错误", "镜头清单不存在。")
            return False
        self.resolve_path(self.output_file.get()).parent.mkdir(parents=True, exist_ok=True)
        return True

    def run_command(self, name, command):
        def worker():
            self.root.after(0, lambda: self.set_busy(True))
            self.append_log(f"=== {name} ===")
            self.append_log(" ".join(command))
            process = subprocess.Popen(
                command,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in process.stdout:
                self.root.after(0, self.append_log, line.rstrip())
            return_code = process.wait()
            self.append_log(f"完成，退出码：{return_code}")
            self.root.after(0, lambda: self.set_busy(False))
            if return_code != 0:
                self.root.after(0, messagebox.showerror, "执行失败", f"{name}执行失败，请查看日志。")

        threading.Thread(target=worker, daemon=True).start()

    def run_grid(self):
        if not self.validate_paths(require_shots=False):
            return
        output = PROJECT_ROOT / "output" / "grid.jpg"
        output.parent.mkdir(parents=True, exist_ok=True)
        self.run_command("抽帧网格", [
            sys.executable, self.script_path("make_grid.py"), self.src_dir.get(), str(output)
        ])

    def run_clips(self):
        if not self.validate_paths(require_shots=True):
            return
        self.run_command("生成片段", [
            sys.executable, self.script_path("make_clips.py"),
            "--src", self.src_dir.get(), "--work", self.work_dir.get(),
            "--shots", self.shots_file.get(),
        ])

    def run_join(self):
        if not self.validate_paths(require_shots=False):
            return
        self.run_command("拼接视频", [
            sys.executable, self.script_path("join.py"),
            "--work", self.work_dir.get(), "--output", self.output_file.get(),
        ])

    def run_verify(self):
        if not self.validate_paths(require_shots=False):
            return
        check_image = Path(self.output_file.get()).parent / "final_check.jpg"
        self.run_command("成片终验", [
            sys.executable, self.script_path("verify_final.py"),
            self.output_file.get(), str(check_image),
        ])


def parse_args():
    parser = argparse.ArgumentParser(description="视频剪辑工作流图形界面")
    parser.add_argument("--no-popup", action="store_true", help="不显示启动署名弹窗")
    return parser.parse_args()


def main():
    args = parse_args()
    root = tk.Tk()
    WorkflowGUI(root, show_popup=not args.no_popup)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
