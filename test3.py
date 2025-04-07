import pygame
import tkinter as tk
from PIL import Image, ImageTk
import math
import time
import threading
import queue

# Initialize Pygame
pygame.init()

# === CONFIG ===
ellipse_width, ellipse_height = 200, 100
ellipse_color = (255, 0, 0)  # Use RGB (255, 0, 0) for red
center_screen = (400, 300)

# Tkinter window setup
root = tk.Tk()
root.title("Pygame in Tkinter")
root.geometry("800x600")

# Fullscreen toggle functionality
fullscreen = False
def toggle_fullscreen(event=None):
    global fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        root.attributes("-fullscreen", True)  # Set fullscreen mode
    else:
        root.attributes("-fullscreen", False)  # Return to normal windowed mode

root.bind("<F11>", toggle_fullscreen)

# Frame for the top bar in Tkinter
top_bar = tk.Frame(root, height=30, bg="gray")
top_bar.pack(fill="x", side="top")

# Create the Tkinter label to display the Pygame-rendered image
tk_label = tk.Label(root)
tk_label.pack(fill="both", expand=True)

# Shared state for FPS and other configuration
config = {
    "fps": 60,  # Adjust FPS to be lower for smoother performance
    "scale_factor": 2,
    "rotation_speed": 90
}

# Initialize rotation angle
angle = 0.0

menu_windows = {}

def toggle_menu(name, create_func):
    """
    Toggle the visibility of a menu window.

    Parameters:
      name: A string key for the menu.
      create_func: A function that creates the menu window if it doesn't exist.
    """
    if name in menu_windows and menu_windows[name].winfo_exists():
        # If the window exists, toggle its visibility.
        if menu_windows[name].state() == 'withdrawn':
            menu_windows[name].deiconify()
        else:
            menu_windows[name].withdraw()
    else:
        # Otherwise, create it.
        menu_windows[name] = create_func()

def create_settings_menu():
    window = tk.Toplevel(root)
    window.title("Settings")
    window.geometry("250x275")
    # When the user clicks the close button, we withdraw it (hide it) rather than destroy it.
    window.protocol("WM_DELETE_WINDOW", lambda: window.withdraw())
    tk.Label(window, text="Settings Menu").pack(pady=10)

    tk.Label(window, text="Max FPS:").pack(pady=5, anchor="w", padx=10)
    e1 = tk.Entry(window)
    e1.insert(0, str(config["fps"]))
    e1.pack(fill="x", padx=10, pady=5)

    tk.Label(window, text="Scale (smoothness):").pack(pady=5, anchor="w", padx=10)
    e2 = tk.Entry(window)
    e2.insert(0, str(config["scale_factor"]))
    e2.pack(fill="x", padx=10, pady=5)

    tk.Label(window, text="Rotation deg/sec:").pack(pady=5, anchor="w", padx=10)
    e3 = tk.Entry(window)
    e3.insert(0, str(config["rotation_speed"]))
    e3.pack(fill="x", padx=10, pady=5)

    def apply():
        try:
            config["fps"] = int(e1.get())
            config["scale_factor"] = int(e2.get())
            config["rotation_speed"] = int(e3.get())
        except ValueError:
            pass

    tk.Button(window, text="Apply", command=apply).pack(pady=10)
    return window

def create_options_menu():
    window = tk.Toplevel(root)
    window.title("Options")
    window.geometry("250x250")
    window.protocol("WM_DELETE_WINDOW", lambda: window.withdraw())
    tk.Label(window, text="Options Menu").pack(pady=10)
    # Add options widgets here as needed.
    return window

def create_info_menu():
    window = tk.Toplevel(root)
    window.title("Information")
    window.geometry("250x250")
    window.protocol("WM_DELETE_WINDOW", lambda: window.withdraw())
    tk.Label(window, text="Info Menu").pack(pady=10)
    # Add informational content here as needed.
    return window

# Create the settings toggle button in the top bar
settings_btn = tk.Button(top_bar, text="Settings", 
                         command=lambda: toggle_menu("settings", create_settings_menu))
options_btn = tk.Button(top_bar, text="Options", 
                        command=lambda: toggle_menu("options", create_options_menu))
info_btn = tk.Button(top_bar, text="Info", 
                     command=lambda: toggle_menu("info", create_info_menu))

settings_btn.pack(side="left", padx=5)
options_btn.pack(side="left", padx=5)
info_btn.pack(side="left", padx=5)

# Global time tracking for delta time
last_time = time.time()

# Create a Queue instance for communication between threads
surface_queue = queue.Queue()

# Flag to stop the worker thread gracefully
stop_thread = False

# Function to resize the Pygame surface when the Tkinter window is resized
def resize_pygame_surface():
    new_width = root.winfo_width()
    new_height = root.winfo_height() - top_bar.winfo_height()
    global screen
    if new_width > 0 and new_height > 0:  # Ensure dimensions are positive
        if screen.get_size() != (new_width, new_height):
            screen = pygame.Surface((new_width, new_height), pygame.SRCALPHA)

# Draw a rotating ellipse
def draw_ellipse(surface, cx, cy, rx, ry, color, angle):
    """ Draw a filled ellipse at (cx, cy) with radii (rx, ry) and color on the given surface """
    num_segments = 100
    points = []
    for i in range(num_segments):
        angle_rad = 2 * math.pi * i / num_segments
        x = cx + rx * math.cos(angle_rad)
        y = cy + ry * math.sin(angle_rad)
        points.append((x, y))
    
    # Rotate the points
    rotated_points = []
    for x, y in points:
        x_rot = (x - cx) * math.cos(math.radians(angle)) - (y - cy) * math.sin(math.radians(angle)) + cx
        y_rot = (x - cx) * math.sin(math.radians(angle)) + (y - cy) * math.cos(math.radians(angle)) + cy
        rotated_points.append((x_rot, y_rot))
    
    # Draw the rotated ellipse
    pygame.draw.polygon(surface, color, rotated_points)

# Function to update Pygame surface in a separate thread
def update_pygame_surface():
    global last_time, angle, screen

    # Compute delta time
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    # Clear the screen
    screen.fill((30, 30, 30))  # Fill the screen with a dark color

    # Draw the rotating ellipse (centered in the middle of the screen)
    cx, cy = screen.get_width() // 2, screen.get_height() // 2
    draw_ellipse(screen, cx, cy, ellipse_width, ellipse_height, ellipse_color, angle)

    # Increment angle for continuous rotation
    angle += config["rotation_speed"] * dt

    # Put the updated surface in the queue to be processed by Tkinter
    #_surface = pygame.image.tostring(screen, "RGB")
    #surface_queue.put(_surface)

def load_and_process_image():
    global stop_thread
    while not stop_thread:
        try:
            global screen

            # Convert the surface to a format Tkinter can display
            pixels = pygame.image.tostring(screen, "RGB")
            pil_image = Image.frombytes("RGB", screen.get_size(), pixels)
            photo = ImageTk.PhotoImage(image=pil_image)
            
            # Put the processed image in the queue
            surface_queue.put(photo)
            time.sleep(1 / 120)  # Control FPS
        except Exception as e:
            print(f"Error in game loop: {e}")
            stop_thread = True  # Stop the thread if an error occurs
    """ Function to load and process an image in the background """

last_update_time = 0
update_interval = 1 / 60  # Limit to 60 updates per second

# Function to update the Tkinter label with the Pygame surface
def update_tkinter_display():
    global last_update_time

    current_time = time.time()
    if current_time - last_update_time < update_interval:
        return  # Skip the update if it hasn't been long enough

    last_update_time = current_time

    try:
        # Check if the queue has an image to display
        if not surface_queue.empty():
            photo = surface_queue.get_nowait()
            tk_label.configure(image=photo)
            tk_label.image = photo  # Keep a reference to prevent garbage collection
    except queue.Empty:
        pass  # If the queue is empty, nothing to do

    # Call this function again after a delay to update the display
    root.after(1000 // config["fps"], update_tkinter_display)

# Function to start the worker thread that updates the Pygame surface
def tkinter_loop():
    global stop_thread
    while not stop_thread:
        try:
            update_tkinter_display()
            time.sleep(1 / config["fps"] / 2)  # Control FPS
        except Exception as e:
            print(f"Error in game loop: {e}")
            stop_thread = True  # Stop the thread if an error occurs

def pygame_loop():
    global stop_thread
    while not stop_thread:
        try:
            resize_pygame_surface()  # Check for resizing
            update_pygame_surface()
            time.sleep(1 / config["fps"])  # Control FPS
        except Exception as e:
            print(f"Error in game loop: {e}")
            stop_thread = True  # Stop the thread if an error occurs

# Function to stop the worker thread gracefully when Tkinter closes
def on_closing():
    global stop_thread
    stop_thread = True  # Signal the thread to stop
    root.quit()  # Close the Tkinter window
    root.destroy()  # Clean up

# Initialize the screen surface for rendering before starting the game loop
screen = pygame.Surface((800, 600), pygame.SRCALPHA)  # Make sure screen is initialized here

# Start a separate thread to run the game loop
threading.Thread(target=tkinter_loop, daemon=True).start()
threading.Thread(target=pygame_loop, daemon=True).start()

threading.Thread(target=load_and_process_image, daemon=True).start()

# Set up closing event for the Tkinter window
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start Tkinter's main loop
root.mainloop()
