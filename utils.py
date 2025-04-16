import os
import logging
from datetime import datetime
from typing import List, Tuple, Optional


# --- Helper Functions ---
def parse_txt_file(txt_path: str) -> Tuple[str, str, str]:
    """Parse transaction file to extract transaction, action, and user comment."""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error("File not found: %s", txt_path)
        return "", "STP-Release", ""
    except PermissionError:
        logging.error("Permission denied when reading file %s", txt_path)
        return "", "STP-Release", ""
    except IsADirectoryError:
        logging.error("Path %s is a directory, not a file", txt_path)
        return "", "STP-Release", ""
    except UnicodeDecodeError:
        logging.error("Failed to decode file %s with UTF-8 encoding", txt_path)
        return "", "STP-Release", ""
    except IOError as e:
        logging.error("IO error when reading file %s: %s", txt_path, e)
        return "", "STP-Release", ""

    transaction = lines[0].strip() if len(lines) > 0 else ""
    action = lines[1].strip() if len(lines) > 1 else "STP-Release"
    user_comment = lines[2].strip() if len(lines) > 2 else ""

    return transaction, action, user_comment


def create_output_structure(
    transaction: str, output_dir: str
) -> Tuple[Optional[str], Optional[str]]:
    """Create output folder structure for transaction."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(output_dir, today)
    transaction_folder = os.path.join(date_folder, transaction)

    try:
        os.makedirs(date_folder, exist_ok=True)
        os.makedirs(transaction_folder, exist_ok=True)
        return transaction_folder, date_folder
    except PermissionError:
        logging.error("Permission denied when creating directories in %s", output_dir)
        return None, None
    except NotADirectoryError:
        logging.error("Path %s is not a valid directory", output_dir)
        return None, None
    except OSError as e:
        logging.error("OS error when creating directory structure: %s", e)
        return None, None


def move_screenshots_to_folder(target_folder: str, source_dir: str = ".") -> None:
    """Move screenshots from source directory to target folder.

    Args:
        target_folder: Path to destination folder
        source_dir: Path to source directory (default: current directory)
    """
    # Check if target folder exists
    if not os.path.exists(target_folder):
        try:
            os.makedirs(target_folder, exist_ok=True)
            logging.info("Created target folder: %s", target_folder)
        except PermissionError:
            logging.error("Permission denied when creating folder %s", target_folder)
            return
        except OSError as e:
            logging.error("OS error when creating folder %s: %s", target_folder, e)
            return

    # Check if target folder is a directory
    if not os.path.isdir(target_folder):
        logging.error("Target %s is not a directory", target_folder)
        return

    try:
        files = os.listdir(source_dir)
    except FileNotFoundError:
        logging.error("Source directory %s not found", source_dir)
        return
    except PermissionError:
        logging.error("Permission denied when accessing directory %s", source_dir)
        return
    except NotADirectoryError:
        logging.error("Path %s is not a directory", source_dir)
        return
    except OSError as e:
        logging.error("OS error when accessing directory %s: %s", source_dir, e)
        return

    for file in files:
        if file.endswith(".png"):
            source_path = os.path.join(source_dir, file)
            target_path = os.path.join(target_folder, file)

            try:
                os.rename(source_path, target_path)
                logging.info("Moved screenshot %s to %s", file, target_folder)
            except FileNotFoundError:
                logging.error("Screenshot file %s no longer exists", file)
            except PermissionError:
                logging.error("Permission denied when moving screenshot %s", file)
            except FileExistsError:
                logging.error(
                    "A file with the name %s already exists in target folder", file
                )
            except OSError as e:
                logging.error("OS error when moving screenshot %s: %s", file, e)


def get_txt_files(directory: str) -> List[str]:
    """Get all txt files in a directory."""
    try:
        return [f for f in os.listdir(directory) if f.endswith(".txt")]
    except FileNotFoundError:
        logging.error("Directory not found: %s", directory)
        return []
    except PermissionError:
        logging.error("Permission denied when accessing directory %s", directory)
        return []
    except NotADirectoryError:
        logging.error("Path %s is not a directory", directory)
        return []
    except OSError as e:
        logging.error("OS error when accessing directory %s: %s", directory, e)
        return []
