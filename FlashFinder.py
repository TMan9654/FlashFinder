from src.main import launch_flashfinder
from src.utils.utils import check_config_paths

from multiprocessing import freeze_support

def main():
    check_config_paths()
    launch_flashfinder()

if __name__ == "__main__":
    # freeze_support()
    main()
