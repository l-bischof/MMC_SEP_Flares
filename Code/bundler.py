import config
import shutil
import os

def pack_epd():
    shutil.make_archive(f"{config.CACHE_DIR}/EPD_DATA", "xztar", f"{config.CACHE_DIR}/EPD_Dataset/")

def unpack_epd():
    if os.path.isdir(f"{config.CACHE_DIR}/EPD_Dataset/"):
        print("Folder already exists! Not unpacking")
        return
    shutil.unpack_archive(f"{config.CACHE_DIR}/EPD_DATA.tar.xz", f"{config.CACHE_DIR}/EPD_Dataset/")


def pack_connectivity_tool():
    shutil.make_archive(f"{config.CACHE_DIR}/CON_DATA", "xztar", f"{config.CACHE_DIR}/connectivity_tool_downloads/")

def unpack_connectivity_tool():
    if os.path.isdir(f"{config.CACHE_DIR}/connectivity_tool_downloads/"):
        print("Folder already exists! Not unpacking")
        return
    shutil.unpack_archive(f"{config.CACHE_DIR}/CON_DATA.tar.xz", f"{config.CACHE_DIR}/connectivity_tool_downloads/")






if __name__ == "__main__":
    pack_epd()
    pack_connectivity_tool()