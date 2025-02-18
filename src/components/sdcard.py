import sys
from machine import SPI, Pin
import uos
sys.path.append("..")  # Add the parent directory to the import path
from util.sdcard import SDCard


class SDCardManager:
    def __init__(self, spi_id=0, sck=18, mosi=19, miso=16, cs=22):
        """Initialize and mount the SD card."""
        self.spi = SPI(spi_id, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.cs = Pin(cs)
        self.sd = SDCard(self.spi, self.cs)

        try:
            uos.mount(self.sd, '/')
            print("SD card mounted successfully.")
        except Exception as e:
            print("Failed to mount SD card:", e)
            raise

    def list_contents(self, path='/'):
        """List the contents of the specified directory on the SD card."""
        try:
            return uos.listdir(path)
        except Exception as e:
            print("Failed to list directory contents:", e)
            return None

    def read_file(self, file_path):
        """Read and return the contents of a file on the SD card."""
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            print("Failed to read file:", e)
            return None

    def write_file(self, file_path, content):
        """Write content to a file on the SD card."""
        try:
            with open(file_path, 'w') as file:
                file.write(content)
            print(f"Text written to {file_path} successfully.")
        except Exception as e:
            print("Failed to write to file:", e)
            return False
        return True

    def write_data(self, file_path, data):
        """Write raw binary data to the SD card."""
        try:
            with open(file_path, 'ab') as file:  # Append mode
                file.write(data)
            print(f"Data written to {file_path} successfully.")
        except Exception as e:
            print("Failed to write data to file:", e)

    def read_data(self, file_path):
        """Read raw binary data from the SD card."""
        try:
            with open(file_path, 'rb') as file:
                return file.read()
        except Exception as e:
            print("Failed to read data from file:", e)
            return None

    def delete_file(self, file_path):
        """Delete a file from the SD card."""
        try:
            uos.remove(file_path)
            print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}:", e)

    def unmount(self):
        """Unmount the SD card."""
        try:
            uos.umount('/')
            print("SD card unmounted successfully.")
        except Exception as e:
            print("Failed to unmount SD card:", e)
            raise


# Example usage
if __name__ == "__main__":
    sd_manager = SDCardManager()

    print("Contents of SD card:", sd_manager.list_contents())

    file_path = '/hello_world.txt'
    sd_manager.write_file(file_path, 'Hello, World!')

    contents = sd_manager.read_file(file_path)
    print("File Contents:", contents)

    sd_manager.unmount()
