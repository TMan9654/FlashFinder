from src.main import launch_flashfinder

from multiprocessing import freeze_support

def main():
    launch_flashfinder()

if __name__ == "__main__":
    freeze_support()
    main()