#!/usr/bin/env python3

# swww-controller.py
# GPL v3 or Later
# © Sarthak Shah (matchcase), 2025

import os
import random
import subprocess
import sys
import time
import json

CONFIG_FILE = os.path.expanduser("~/.config/swww-script.json")
DEFAULT_CONFIG = { "mode": "dynamic" }

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}", file=sys.stderr)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except IOError as e:
        print(f"Error saving config: {e}", file=sys.stderr)
        return False

def get_wallpaper_dir():
    """Get the wallpaper directory based on current config"""
    config = load_config()
    if config["mode"] == "static":
        return os.path.expanduser("~/Pictures/Static_Wallpapers")
    else:
        return os.path.expanduser("~/Pictures/Dynamic_Wallpapers")

def get_image_files():
    """Get all image files in the directory"""
    wallpaper_dir = get_wallpaper_dir()
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    image_files = []
    
    for file in os.listdir(wallpaper_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(wallpaper_dir, file))
    
    return image_files

def get_outputs():
    """Get dict from `wlr-randr --json`"""
    result = subprocess.run(["wlr-randr", "--json"], capture_output=True, text=True)
    outputs = json.loads(result.stdout)
    return outputs

def set_random_wallpaper():
    """Set a random image as wallpaper"""
    images = get_image_files()
    if not images:
        print(f"No images found in directory {get_wallpaper_dir()}", file=sys.stderr)
        return False

    outputs = get_outputs()
    for output in outputs:
        output_name = output["name"]
        random_image = random.choice(images)
        set_wallpaper(random_image, output_name)
    return True

def set_wallpaper(image_path, output_name):
    """Set the given image as wallpaper using swww"""
    try:
        subprocess.run(["swww", "img", "--outputs", output_name, "--resize", "crop", image_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error setting wallpaper: {e}", file=sys.stderr)
        return False

def notify_user(event="Nothing"):
    """Notify the user about an event"""
    try:
        subprocess.run(["notify-send", "-t", "1000", event])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error sending notification '{event}': {e}", file=sys.stderr)
        return False
    
def run_daemon(interval=60):
    """Run as a daemon, changing wallpaper every interval seconds"""
    print(f"Starting wallpaper rotation daemon with interval {interval} seconds")

    try:
        subprocess.Popen(["swww-daemon"])
    except subprocess.CalledProcessError as e:
        print(f"Error starting swww daemon: {e}", file=sys.stderr)
    
    while True:
        set_random_wallpaper()
        time.sleep(interval)

def main():
    if len(sys.argv) > 1:
        config = load_config()
        match sys.argv[1]:
            case "--daemon":
                notify_user("Initialized daemon")
                interval = 60  # 60 seconds
                if len(sys.argv) > 2:
                    try:
                        interval = int(sys.argv[2])
                    except ValueError:
                        pass
                run_daemon(interval)
            case "--static":
                config["mode"] = "static"
                save_config(config)
                notify_user("Switched to static wallpapers")
                set_random_wallpaper()
            case "--dynamic":
                config["mode"] = "dynamic"
                save_config(config)
                notify_user("Switched to dynamic wallpapers")
                set_random_wallpaper()
            case _:
                print("Invalid option!")
    else: # for use in i3blocks (sway)
        print(" 📀 ")
        sys.stdout.flush()
        
        button = os.environ.get("BLOCK_BUTTON")
        if button:
            notify_user("Changing the wallpaper...")
            set_random_wallpaper()

if __name__ == "__main__":
    main()
