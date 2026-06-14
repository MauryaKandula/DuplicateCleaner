"""
Duplicate File Cleaner v1.0
Lightweight Windows tool to find and remove duplicate files.
Uses SHA256 hashing for exact duplicate detection.
Built with tkinter (no external dependencies).
GitHub-ready single-file application.
"""

import os
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from collections import defaultdict
from pathlib import Path
import time

class DuplicateFileCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Cleaner v1.0")
        self.root.geometry("900x650")
        self.root.minsize(800, 500)
        self.root.configure(bg="#1e1e2e")
        
        # Styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("TButton", background="#45475a", foreground="#cdd6f4", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        self.style.map("TButton", background=[("active", "#585b70")])
        self.style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", insertcolor="#cdd6f4")
        self.style.configure("Treeview", background="#313244", foreground="#cdd6f4", fieldbackground="#313244", rowheight=28)
        self.style.configure("Treeview.Heading", background="#45475a", foreground="#cdd6f4", font=("Segoe UI", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#585b70")], foreground=[("selected", "#ffffff")])
        self.style.configure("Horizontal.TProgressbar", background="#89b4fa", troughcolor="#313244")
        
        # Data storage
        self.duplicates = defaultdict(list)  # {hash: [filepaths]}
        self.file_checkboxes = {}  # {filepath: tk.BooleanVar}
        self.scanning = False
        self.total_files_scanned = 0
        self.total_duplicates_found = 0
        self.space_savings = 0
        
        self.build_ui()
    
    def build_ui(self):
        # Top frame - folder selection
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        ttk.Label(top_frame, text="Select Folder to Scan:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        folder_select_frame = ttk.Frame(top_frame)
        folder_select_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.folder_entry = ttk.Entry(folder_select_frame, font=("Segoe UI", 10))
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        browse_btn = ttk.Button(folder_select_frame, text="Browse", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        scan_btn = ttk.Button(folder_select_frame, text="🔍 Scan for Duplicates", command=self.start_scan)
        scan_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(top_frame, mode="indeterminate", style="Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(8, 0))
        
        # Stats frame
        stats_frame = ttk.Frame(self.root)
        stats_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        self.stats_label = ttk.Label(stats_frame, text="Ready. Select a folder and click Scan.", font=("Segoe UI", 9))
        self.stats_label.pack(anchor=tk.W)
        
        self.space_label = ttk.Label(stats_frame, text="", font=("Segoe UI", 9, "bold"), foreground="#a6e3a1")
        self.space_label.pack(anchor=tk.W)
        
        # Treeview for duplicate groups
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))
        
        # Scrollbar
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("keep", "filepath", "size", "modified"),
            show="headings",
            selectmode="extended",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        self.tree.heading("keep", text="Delete?")
        self.tree.heading("filepath", text="File Path")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Last Modified")
        
        self.tree.column("keep", width=70, anchor=tk.CENTER, minwidth=70)
        self.tree.column("filepath", width=500, minwidth=200)
        self.tree.column("size", width=100, anchor=tk.CENTER, minwidth=80)
        self.tree.column("modified", width=150, anchor=tk.CENTER, minwidth=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Bottom action frame
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        select_all_btn = ttk.Button(action_frame, text="Select All for Deletion", command=self.select_all)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        deselect_all_btn = ttk.Button(action_frame, text="Deselect All", command=self.deselect_all)
        deselect_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        keep_one_btn = ttk.Button(action_frame, text="Keep One Per Group", command=self.keep_one_per_group)
        keep_one_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = ttk.Button(
            action_frame,
            text="🗑️ Delete Selected Duplicates",
            command=self.delete_selected,
            style="Delete.TButton"
        )
        delete_btn.pack(side=tk.RIGHT)
        
        # Delete button style
        self.style.configure("Delete.TButton", background="#e64553", foreground="#ffffff")
        self.style.map("Delete.TButton", background=[("active", "#d32f3f")])
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan for Duplicates")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def start_scan(self):
        folder = self.folder_entry.get().strip()
        if not folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "The specified path does not exist.")
            return
        
        self.clear_results()
        self.scanning = True
        self.progress.start(10)
        self.stats_label.config(text="Scanning... Please wait.", foreground="#89b4fa")
        
        thread = Thread(target=self.scan_folder, args=(folder,), daemon=True)
        thread.start()
    
    def scan_folder(self, folder):
        self.duplicates.clear()
        self.file_checkboxes.clear()
        self.total_files_scanned = 0
        self.total_duplicates_found = 0
        self.space_savings = 0
        
        # First pass: collect all file paths with their sizes
        file_info = []
        for root_dir, _, files in os.walk(folder):
            for filename in files:
                filepath = os.path.join(root_dir, filename)
                try:
                    filesize = os.path.getsize(filepath)
                    file_info.append((filepath, filesize))
                except (OSError, PermissionError):
                    continue
        
        self.total_files_scanned = len(file_info)
        
        # Second pass: hash files, grouped by size first for efficiency
        size_map = defaultdict(list)
        for filepath, filesize in file_info:
            size_map[filesize].append(filepath)
        
        for filesize, filepaths in size_map.items():
            if len(filepaths) < 2:
                continue  # Skip unique sizes — can't be duplicates
            
            hash_map = defaultdict(list)
            for filepath in filepaths:
                try:
                    file_hash = self.hash_file(filepath)
                    hash_map[file_hash].append(filepath)
                except (OSError, PermissionError):
                    continue
            
            for file_hash, dup_paths in hash_map.items():
                if len(dup_paths) > 1:
                    self.duplicates[file_hash] = dup_paths
                    self.total_duplicates_found += len(dup_paths) - 1
                    self.space_savings += filesize * (len(dup_paths) - 1)
        
        self.root.after(0, self.populate_tree)
    
    def hash_file(self, filepath, chunk_size=8192):
        """Compute SHA256 hash of a file efficiently."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.file_checkboxes.clear()
        
        group_colors = ["#313244", "#2a2a3c"]
        color_idx = 0
        
        for file_hash, filepaths in self.duplicates.items():
            bg_tag = f"group_{file_hash[:8]}"
            self.tree.tag_configure(bg_tag, background=group_colors[color_idx % 2])
            color_idx += 1
            
            for filepath in filepaths:
                try:
                    stat = os.stat(filepath)
                    size_mb = stat.st_size / (1024 * 1024)
                    size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{stat.st_size / 1024:.2f} KB"
                    modified_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                except OSError:
                    size_str = "Unknown"
                    modified_time = "Unknown"
                
                var = tk.BooleanVar(value=False)
                self.file_checkboxes[filepath] = var
                
                item_id = self.tree.insert(
                    "",
                    tk.END,
                    values=("☐", filepath, size_str, modified_time),
                    tags=(bg_tag,)
                )
                self.file_checkboxes[f"{item_id}_id"] = (item_id, var)
        
        self.progress.stop()
        self.scanning = False
        
        if self.total_duplicates_found > 0:
            self.stats_label.config(
                text=f"Scan complete! Found {self.total_duplicates_found} duplicate files across {len(self.duplicates)} groups. "
                     f"({self.total_files_scanned} files scanned total)",
                foreground="#a6e3a1"
            )
            space_mb = self.space_savings / (1024 * 1024)
            space_str = f"{space_mb:.2f} MB" if space_mb < 1024 else f"{space_mb / 1024:.2f} GB"
            self.space_label.config(text=f"💾 Potential space savings: {space_str}")
        else:
            self.stats_label.config(text="Scan complete! No duplicates found.", foreground="#f9e2af")
            self.space_label.config(text="")
        
        self.update_checkbox_display()
        
        # Bind click event for checkbox toggling
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
    
    def on_tree_click(self, event):
        """Toggle checkbox when clicking the 'keep' column."""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if region == "cell" and column == "#1" and item:
            key = f"{item}_id"
            if key in self.file_checkboxes:
                _, var = self.file_checkboxes[key]
                var.set(not var.get())
                self.update_checkbox_display()
    
    def update_checkbox_display(self):
        """Update the checkmark symbols in the tree."""
        for key, (item_id, var) in self.file_checkboxes.items():
            if key.endswith("_id"):
                symbol = "☒" if var.get() else "☐"
                current_values = list(self.tree.item(item_id, "values"))
                current_values[0] = symbol
                self.tree.item(item_id, values=current_values)
    
    def select_all(self):
        """Mark all duplicate files for deletion."""
        for key, (item_id, var) in self.file_checkboxes.items():
            if key.endswith("_id"):
                var.set(True)
        self.update_checkbox_display()
    
    def deselect_all(self):
        """Unmark all files."""
        for key, (item_id, var) in self.file_checkboxes.items():
            if key.endswith("_id"):
                var.set(False)
        self.update_checkbox_display()
    
    def keep_one_per_group(self):
        """Automatically keep the first file in each duplicate group, mark the rest for deletion."""
        processed_groups = set()
        for file_hash, filepaths in self.duplicates.items():
            first_path = filepaths[0]
            for i, filepath in enumerate(filepaths):
                if i == 0:
                    # Keep the first file
                    for key, (item_id, var) in self.file_checkboxes.items():
                        if key.endswith("_id"):
                            current_values = list(self.tree.item(item_id, "values"))
                            if current_values[1] == first_path:
                                var.set(False)
                else:
                    # Mark for deletion
                    for key, (item_id, var) in self.file_checkboxes.items():
                        if key.endswith("_id"):
                            current_values = list(self.tree.item(item_id, "values"))
                            if current_values[1] == filepath:
                                var.set(True)
        self.update_checkbox_display()
    
    def delete_selected(self):
        """Delete all files marked for deletion."""
        files_to_delete = []
        for key, (item_id, var) in self.file_checkboxes.items():
            if key.endswith("_id") and var.get():
                filepath = self.tree.item(item_id, "values")[1]
                files_to_delete.append(filepath)
        
        if not files_to_delete:
            messagebox.showinfo("No Selection", "No files selected for deletion. Click the checkbox column to mark files.")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(files_to_delete)} file(s)?\n\n"
            "This action cannot be undone. Files will be permanently deleted.",
            icon="warning"
        )
        
        if not confirm:
            return
        
        deleted_count = 0
        failed_count = 0
        failed_files = []
        
        for filepath in files_to_delete:
            try:
                os.remove(filepath)
                deleted_count += 1
                # Remove from tree
                for key, (item_id, var) in list(self.file_checkboxes.items()):
                    if key.endswith("_id"):
                        if self.tree.item(item_id, "values")[1] == filepath:
                            self.tree.delete(item_id)
                            del self.file_checkboxes[key]
                            break
            except (OSError, PermissionError) as e:
                failed_count += 1
                failed_files.append((filepath, str(e)))
        
        result_msg = f"Successfully deleted: {deleted_count} file(s)"
        if failed_count > 0:
            result_msg += f"\nFailed to delete: {failed_count} file(s)"
            if failed_files:
                result_msg += "\n\nFailed files:"
                for fp, err in failed_files[:5]:
                    result_msg += f"\n- {os.path.basename(fp)}: {err}"
                if len(failed_files) > 5:
                    result_msg += f"\n...and {len(failed_files) - 5} more."
        
        messagebox.showinfo("Operation Complete", result_msg)
        
        # Recalculate stats
        remaining_dupes = sum(len(v) - 1 for v in self.duplicates.values())
        if remaining_dupes <= 0:
            self.clear_results()
            self.stats_label.config(text="All duplicates cleaned up!", foreground="#a6e3a1")
        else:
            self.stats_label.config(text=f"Remaining duplicates: {remaining_dupes}", foreground="#f9e2af")
    
    def clear_results(self):
        """Clear all scan results."""
        self.tree.delete(*self.tree.get_children())
        self.duplicates.clear()
        self.file_checkboxes.clear()
        self.total_files_scanned = 0
        self.total_duplicates_found = 0
        self.space_savings = 0
        self.space_label.config(text="")
        self.stats_label.config(text="Ready. Select a folder and click Scan.", foreground="#cdd6f4")

def main():
    root = tk.Tk()
    app = DuplicateFileCleaner(root)
    root.mainloop()

if __name__ == "__main__":
    main()