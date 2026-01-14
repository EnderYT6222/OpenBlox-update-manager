import requests, io, time, random, sys, os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from PIL import Image
from colorama import init

# Initialize Windows Terminal for TrueColor support
init(autoreset=True)
console = Console(color_system="truecolor", style="on black")

# --- VERSION & UPDATE CONFIG ---
CURRENT_VERSION = "OpenBeta0.1"
# REPLACE THESE WITH YOUR ACTUAL GITHUB PATHS
VERSION_URL = "https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/openblox.py"

# --- THEME CONFIG ---
P_MAIN = "#8F00FF"  # Electric Purple
C_WHITE = "#FFFFFF"

def check_for_updates():
    """Checks GitHub for a newer version and self-updates if found."""
    try:
        console.print(f"[{P_MAIN}]SYSTEM > Checking for updates...[/]")
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            latest_version = response.text.strip()
            if latest_version != CURRENT_VERSION:
                console.print(f"[{P_MAIN}]UPDATE > New version {latest_version} found! Downloading...[/]")
                new_code = requests.get(UPDATE_URL, timeout=10).text
                
                # Get the name of the current script
                file_path = os.path.realpath(sys.argv[0])
                
                # Write the new code over the old file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                
                console.print("[bold green]UPDATE > Success! Restarting system...[/]")
                time.sleep(2)
                # Restart the script
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                console.print(f"[dim green]SYSTEM > Version {CURRENT_VERSION} is up to date.[/]")
                time.sleep(1)
        else:
            console.print("[dim red]SYSTEM > Update server unreachable.[/]")
            time.sleep(1)
    except Exception as e:
        console.print(f"[dim red]SYSTEM > Update failed: {e}[/]")
        time.sleep(1)

def get_color_ascii(url, width=45):
    """Downloads image to RAM and manually injects RGB ANSI codes for perfect color."""
    try:
        res = requests.get(url, timeout=5)
        img = Image.open(io.BytesIO(res.content)).convert("RGB")
        
        # Calculate height based on terminal character aspect ratio (~0.5)
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.48)
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        pixels = img.load()
        chars = ["@", "#", "8", "&", "o", ":", "*", ".", " "]
        output = Text()

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                brightness = sum((r, g, b)) / 3
                char = chars[min(int(brightness / 32), len(chars)-1)]
                output.append(char, style=f"rgb({r},{g},{b})")
            output.append("\n")
        return output
    except Exception:
        return Text("IMAGE_RENDER_FAILED", style="bold red")

def handshake_ui(label="SYNCING"):
    """Purple packet transfer animation."""
    frames = [
        f"💻 [{P_MAIN}]📦[/]       ☁️ ", f"💻   [{P_MAIN}]📦[/]     ☁️ ", 
        f"💻     [{P_MAIN}]📦[/]   ☁️ ", f"💻       [{P_MAIN}]📦[/] ☁️ ",
        f"💻         [{P_MAIN}]✔[/] ☁️ ", f"💻       [{P_MAIN}]📦[/] ☁️ "
    ]
    with Live(refresh_per_second=12, transient=True) as live:
        for _ in range(2):
            for f in frames:
                live.update(Panel(Text.from_markup(f, justify="center"), border_style=P_MAIN, title=f"[dim]{label}[/]"))
                time.sleep(0.06)

# --- ENGINE MODULES ---

def fetch_user_intel(target):
    if not target: return
    uid = target if target.isdigit() else None
    if not uid:
        try:
            r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [target]}).json()
            uid = str(r['data'][0]['id'])
        except: return console.print(f"[{P_MAIN}]ERROR: USER NOT FOUND[/]")

    handshake_ui("USER_INTEL")
    
    try:
        prof = requests.get(f"https://users.roblox.com/v1/users/{uid}").json()
        pres = requests.post("https://presence.roblox.com/v1/presence/users", json={"userIds": [int(uid)]}).json()
        groups = requests.get(f"https://groups.roblox.com/v2/users/{uid}/groups/roles").json()
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png").json()
        
        avatar = get_color_ascii(thumb['data'][0]['imageUrl'], width=36)
        p_info = pres['userPresences'][0]
        status = {0: "Offline", 1: "Online", 2: "In Game", 3: "In Studio"}.get(p_info['userPresenceType'], "Unknown")
        
        info = Text(f"\n {prof['displayName']} (@{prof['name']})\n", style=f"bold {P_MAIN}")
        info.append("━" * 40 + "\n", style=C_WHITE)
        info.append(f" ID:      {uid}\n STATUS:  {status}\n JOINED:  {prof['created'][:10]}\n", style=C_WHITE)
        
        if groups.get('data'):
            g = groups['data'][0]
            info.append(f" GROUP:   {g['group']['name']}\n RANK:    {g['role']['name']}", style=f"italic {P_MAIN}")

        grid = Table.grid(padding=2)
        grid.add_row(Panel(avatar, title="AVATAR", border_style=P_MAIN), Panel(info, title="SYSTEM_DATA", border_style=C_WHITE))
        console.print(Panel(grid, title=f"[bold {C_WHITE}]OPENBLOX INTEL[/]", border_style=P_MAIN, expand=False))
    except Exception as e: console.print(f"[red]USER_FETCH_ERROR: {e}[/]")

def fetch_experience_intel(pid):
    if not pid.isdigit(): return console.print("[red]INVALID ID[/]")
    handshake_ui("EXP_INTEL")
    try:
        u_data = requests.get(f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={pid}").json()
        if not u_data: raise Exception("Invalid Place ID or Private")
        
        univ_id = u_data[0]['universeId']
        details = requests.get(f"https://games.roblox.com/v1/games?universeIds={univ_id}").json()['data'][0]
        t_data = requests.get(f"https://thumbnails.roblox.com/v1/games/multiget/thumbnails?universeIds={univ_id}&size=768x432&format=Png").json()
        
        render = get_color_ascii(t_data['data'][0]['thumbnails'][0]['imageUrl'], width=65)
        
        info = Text(f"\n {details['name']}\n", style=f"bold {P_MAIN}")
        info.append(f" CREATOR: {details['creator']['name']} | ACTIVE: {details['playing']:,}\n VISITS:  {details['visits']:,}", style=C_WHITE)

        console.print(Panel(render, title="WORLD_RENDER", border_style=P_MAIN))
        console.print(Panel(info, border_style=C_WHITE))
    except Exception as e: console.print(f"[{P_MAIN}]EXP_ERROR: Check if ID is public.[/]")

def fetch_group_intel(gid):
    if not gid.isdigit(): return
    handshake_ui("GROUP_INTEL")
    try:
        res = requests.get(f"https://groups.roblox.com/v1/groups/{gid}").json()
        members = requests.get(f"https://groups.roblox.com/v1/groups/{gid}/users?sortOrder=Desc&limit=10").json()
        
        table = Table(border_style=P_MAIN, title=f"[{C_WHITE}]{res['name']}[/]")
        table.add_column("Username", style=C_WHITE); table.add_column("Rank", style=P_MAIN)
        for m in members['data']: table.add_row(m['user']['username'], m['role']['name'])
        
        console.print(Panel(f" OWNER: {res['owner']['username']}\n MEMBERS: {res['memberCount']:,}", border_style=P_MAIN))
        console.print(table)
    except Exception: console.print("[red]GROUP_ERROR[/]")

# --- MAIN LOOP ---

if __name__ == "__main__":
    check_for_updates() # Run update check immediately on launch
    while True:
        console.clear()
        console.print(Panel(Text(f" OPENBLOX INTEL v{CURRENT_VERSION} ", style=f"bold {C_WHITE} on {P_MAIN}"), border_style=P_MAIN))
        console.print(f"\n [1] [{P_MAIN}]USER[/]  [2] [{P_MAIN}]EXP[/]  [3] [{P_MAIN}]GROUP[/]  [4] [{P_MAIN}]EXIT[/]")
        
        try:
            choice = console.input(f"\n[{P_MAIN}]SYSTEM > [/]")
            if choice == "1": fetch_user_intel(console.input(f"[{P_MAIN}]TARGET > [/]"))
            elif choice == "2": fetch_experience_intel(console.input(f"[{P_MAIN}]PLACE_ID > [/]"))
            elif choice == "3": fetch_group_intel(console.input(f"[{P_MAIN}]GROUP_ID > [/]"))
            elif choice == "4": break
        except KeyboardInterrupt: break
        console.input(f"\n[dim {P_MAIN}]Press Enter to continue...[/]")
