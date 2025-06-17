import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
from concurrent.futures import ThreadPoolExecutor
import time

class MinimalTextureSorterGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.create_widgets()
        
    def setup_window(self):
        self.root.title("TEX Sorter 1.0.0.0")
        self.root.geometry("784x181")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)
        
        # Set custom icon - works for both .py and .exe
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # Running as .exe - PyInstaller bundles files in sys._MEIPASS
                icon_path = os.path.join(sys._MEIPASS, "sort.ico")
            else:
                # Running as .py script
                icon_path = "sort.ico"
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (784 // 2)
        y = (self.root.winfo_screenheight() // 2) - (181 // 2)
        self.root.geometry(f"784x181+{x}+{y}")
        
    def setup_variables(self):
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.operation_var = tk.StringVar(value="COPY")
        self.is_processing = False
        self.cancel_requested = False
        self.total_files = 0
        self.processed_count = 0
        self.failed_count = 0
        
    def create_widgets(self):
        # Main content area - no header frame
        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        # Source Folder section
        source_frame = tk.Frame(content_frame, bg='#f0f0f0')
        source_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.source_btn = tk.Button(source_frame, text="Source Folder",
                              command=self.browse_input,
                              font=('Segoe UI', 10),
                              bg='#e1e1e1', fg='#000000',
                              relief='solid', bd=1,
                              highlightbackground='#666666',
                              highlightcolor='#666666',
                              highlightthickness=1,
                              width=20, height=1,
                              cursor='hand2')
        self.source_btn.pack(side=tk.LEFT)
        
        # Source path display (initially hidden)
        self.source_path_label = tk.Label(source_frame, text="",
                                         font=('Segoe UI', 9),
                                         bg='#f0f0f0', fg='#000000',
                                         anchor='w')
        # Don't pack initially
        
        # Output Folder section  
        output_frame = tk.Frame(content_frame, bg='#f0f0f0')
        output_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.output_btn = tk.Button(output_frame, text="Output Folder",
                              command=self.browse_output,
                              font=('Segoe UI', 10),
                              bg='#e1e1e1', fg='#000000',
                              relief='solid', bd=1,
                              highlightbackground='#666666',
                              highlightcolor='#666666',
                              highlightthickness=1,
                              width=20, height=1,
                              cursor='hand2')
        self.output_btn.pack(side=tk.LEFT)
        
        # Output path display (initially hidden)
        self.output_path_label = tk.Label(output_frame, text="",
                                         font=('Segoe UI', 9),
                                         bg='#f0f0f0', fg='#000000',
                                         anchor='w')
        # Don't pack initially
        
        # Operation dropdown
        self.operation_menu = tk.OptionMenu(content_frame, self.operation_var,
                                           "COPY", "MOVE")
        self.operation_menu.configure(font=('Segoe UI', 9),
                                     bg='white', fg='#000000',
                                     relief='solid', bd=1,
                                     highlightbackground='#666666',
                                     highlightcolor='#666666',
                                     highlightthickness=0,
                                     activebackground='#e0e0e0',
                                     width=17)
        self.operation_menu.pack(anchor='w', pady=(15, 10))
        
        # Sort button frame to hold button and progress bar side by side
        sort_frame = tk.Frame(content_frame, bg='#f0f0f0')
        sort_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Sort button with dynamic text
        self.sort_btn = tk.Button(sort_frame, text="Sort 0 Textures",
                                 command=self.start_sorting_threaded,
                                 font=('Segoe UI', 10),
                                 bg='#e1e1e1', fg='#000000',
                                 relief='solid', bd=1,
                                 highlightbackground='#666666',
                                 highlightcolor='#666666',
                                 highlightthickness=1,
                                 width=20, height=1,
                                 cursor='hand2')
        self.sort_btn.pack(side=tk.LEFT)
        
        # Progress bar elements (initially hidden)
        self.progress_canvas = tk.Canvas(sort_frame, height=26, width=550, bg='#e0e0e0', 
                                       relief='solid', bd=1, highlightthickness=0)
        
        self.progress_text = tk.Label(sort_frame, text="0/0",
                                    font=('Segoe UI', 9),
                                    bg='#f0f0f0', fg='#000000')
        # Don't pack the progress text - we'll draw it on the canvas instead
        
        self.cancel_btn = tk.Button(sort_frame, text="Cancel",
                                  command=self.cancel_processing,
                                  font=('Segoe UI', 9),
                                  bg='#e1e1e1', fg='#000000',
                                  relief='solid', bd=1,
                                  width=9, height=1,
                                  cursor='hand2')
        
        # Status label (hidden by default)
        self.status_label = tk.Label(content_frame, text="",
                                    font=('Segoe UI', 7),
                                    bg='#f0f0f0', fg='#666666')
        
    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.input_var.set(folder)
            # Show the source path to the right of the button
            self.source_path_label.configure(text=folder)
            if not self.source_path_label.winfo_manager():
                self.source_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
            self.update_texture_count()
            
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_var.set(folder)
            # Show the output path to the right of the button
            self.output_path_label.configure(text=folder)
            if not self.output_path_label.winfo_manager():
                self.output_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
            
    def update_texture_count(self):
        """Count texture files in the source folder and update button text"""
        source_dir = self.input_var.get().strip()
        if not source_dir or not os.path.isdir(source_dir):
            self.sort_btn.configure(text="Sort 0 Textures")
            self.total_files = 0
            return
            
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds", ".webp")
        count = 0
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(image_extensions):
                    count += 1
        
        self.total_files = count
        self.sort_btn.configure(text=f"Sort {count} Textures")
        
    def start_sorting_threaded(self):
        if self.is_processing:
            return
        
        # Run sorting in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.start_sorting)
        thread.daemon = True
        thread.start()
        
    def start_sorting(self):
        input_dir = self.input_var.get().strip()
        output_dir = self.output_var.get().strip()
        move_files = self.operation_var.get() == "MOVE"
        
        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showerror("Error", "Please select a valid source folder.")
            return
            
        if not output_dir:
            messagebox.showerror("Error", "Please select an output folder.")
            return
            
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output folder: {e}")
                return
        
        # Start processing
        self.is_processing = True
        self.cancel_requested = False
        self.processed_count = 0
        self.failed_count = 0
        
        self.root.after(0, lambda: self.sort_btn.configure(state='disabled', text="Processing...", bg='#cccccc'))
        self.root.after(0, self.show_progress_bar)
        
        try:
            self.sort_textures(input_dir, output_dir, move_files)
            if not self.cancel_requested:
                self.root.after(0, lambda: messagebox.showinfo("Success", "Texture sorting completed!"))
        except Exception as e:
            if not self.cancel_requested:
                self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
        finally:
            # Reset UI
            self.is_processing = False
            self.cancel_requested = False
            self.root.after(0, lambda: self.sort_btn.configure(state='normal', text=f"Sort {self.total_files} Textures", bg='#e1e1e1'))
            self.root.after(0, self.hide_progress_bar)
    
    def show_progress_bar(self):
        """Show the progress bar and related elements to the right of the sort button"""
        self.cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_canvas.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
    def hide_progress_bar(self):
        """Hide the progress bar and related elements"""
        self.progress_canvas.pack_forget()
        self.cancel_btn.pack_forget()
        
    def cancel_processing(self):
        """Cancel the current processing operation"""
        self.cancel_requested = True
        
    def update_progress(self, current, total):
        """Update the progress bar and text - thread-safe version"""
        def _update():
            if total > 0:
                # Clear canvas completely
                self.progress_canvas.delete("all")
                
                # Get actual canvas width (it will expand to fill available space)
                canvas_width = self.progress_canvas.winfo_width()
                
                # If canvas width is 0, use the initial width
                if canvas_width == 0:
                    canvas_width = 550
                
                # Calculate fill width (subtract 2 pixels for border to reach the edge)
                progress_percent = current / total
                fill_width = max(1, int(progress_percent * (canvas_width - 2)))
                
                # Draw the green progress rectangle
                if current > 0:  # Only draw if we've processed at least 1 file
                    self.progress_canvas.create_rectangle(1, 1, fill_width + 1, 25, 
                                                        fill='#4CAF50', outline='#4CAF50')
                
                # Draw the progress text in the center of the progress bar
                progress_text = f"{current}/{total}"
                center_x = canvas_width // 2
                self.progress_canvas.create_text(center_x, 13, text=progress_text,
                                               font=('Segoe UI', 9, 'bold'),
                                               fill='#000000')
        
        # Schedule UI update on main thread
        self.root.after(0, _update)
    
    def get_image_size(self, file_path):
        """Get image size with better error handling and file closing"""
        try:
            # Ensure file exists and is accessible
            if not os.path.exists(file_path):
                return None
                
            # Use context manager to ensure file is properly closed
            with Image.open(file_path) as img:
                return img.size
                
        except (OSError, IOError, Image.UnidentifiedImageError) as e:
            return None
        except Exception as e:
            return None
    
    def process_single_file(self, file_info):
        """Process a single file - designed for parallel execution"""
        full_path, file, rel_path, output_dir, move_files = file_info
        
        if self.cancel_requested:
            return False
            
        # Check if file still exists
        if not os.path.exists(full_path):
            return False
            
        size = self.get_image_size(full_path)
        if not size:
            return False

        parts = rel_path.split(os.sep)
        root_type = parts[0] if parts and parts[0] != '.' else "Root"

        res_folder = f"{size[0]}x{size[1]}"
        target_folder = os.path.join(output_dir, root_type, res_folder)
        
        # Create directory if it doesn't exist (thread-safe)
        try:
            os.makedirs(target_folder, exist_ok=True)
        except:
            return False

        destination = os.path.join(target_folder, file)
        
        # Handle file name conflicts
        if os.path.exists(destination):
            base_name, ext = os.path.splitext(file)
            counter = 1
            while os.path.exists(destination):
                new_name = f"{base_name}_{counter}{ext}"
                destination = os.path.join(target_folder, new_name)
                counter += 1
        
        try:
            if move_files:
                shutil.move(full_path, destination)
            else:
                shutil.copy2(full_path, destination)
            return True
        except Exception:
            return False
    
    def sort_textures(self, input_dir, output_dir, move_files=False):
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds", ".webp")
        
        # Collect all file paths first
        file_list = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, input_dir)
                    file_list.append((full_path, file, rel_path, output_dir, move_files))
        
        total_files = len(file_list)
        
        # Initialize progress
        self.update_progress(0, total_files)
        
        # Use ThreadPoolExecutor for parallel processing
        # Use fewer threads for MOVE operations to avoid conflicts
        max_workers = 2 if move_files else 4
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process files in batches for better progress updates
            batch_size = max(1, total_files // 100)  # Update progress 100 times max
            
            for i in range(0, total_files, batch_size):
                if self.cancel_requested:
                    break
                    
                batch = file_list[i:i + batch_size]
                
                # Submit batch to thread pool
                futures = [executor.submit(self.process_single_file, file_info) for file_info in batch]
                
                # Wait for batch completion and count results
                for j, future in enumerate(futures):
                    if self.cancel_requested:
                        break
                        
                    try:
                        success = future.result(timeout=30)  # 30 second timeout per file
                        if success:
                            self.processed_count += 1
                        else:
                            self.failed_count += 1
                    except Exception:
                        self.failed_count += 1
                    
                    # Update progress
                    current_file = i + j + 1
                    if current_file % 10 == 0 or current_file == total_files:  # Update every 10 files
                        self.update_progress(current_file, total_files)

        # Final progress update
        self.update_progress(total_files, total_files)
        
        # Show final results if there were failures
        if self.failed_count > 0:
            def show_warning():
                messagebox.showwarning("Warning", 
                                     f"Processing completed.\nSuccessful: {self.processed_count}\nFailed: {self.failed_count}")
            self.root.after(0, show_warning)

if __name__ == "__main__":
    root = tk.Tk()
    app = MinimalTextureSorterGUI(root)
    root.mainloop()