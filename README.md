iThis script automates the download of the latest Bee node binary for your operating system and architecture, simplifying the process of acquiring Bee for interacting with the Swarm network. 

**Key Features:**

- **Automatic OS and Architecture Detection:** The script automatically determines your operating system (Linux, macOS, Windows) and architecture (x86_64, arm64) to download the appropriate Bee binary.
- **Simplified Download Process:** No manual searching or version checking is required. The script handles everything for a streamlined experience.
- **Streamlined File Management:** The downloaded Bee binary is saved to a common location based on your OS:
    - **Linux/macOS:** `~/.local/bin`
    - **Windows:** `%LOCALAPPDATA%\bin` (if set) or `~AppData\Local\bin` (fallback)
- **Error Handling:** The script raises informative error messages if the download fails or the architecture is not supported.

**Requirements:**

- Python 3.3 or later (due to the `terminate` method for threads)
- `requests` library (`pip install requests`)

**Installation:**

1. Clone this repository:

   ```bash
   git clone https://github.com/darkobas2/util_beeget.git
