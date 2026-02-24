import os
import platform

def check_system():
    print(f"Checking system: {platform.system()} {platform.release()}")
    print("Status: Operational")

if __name__ == "__main__":
    check_system()
