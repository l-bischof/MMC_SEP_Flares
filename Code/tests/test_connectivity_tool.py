from connectivity_tool.downloader import _download_set
from datetime import datetime
import zipfile

import unittest


class TestMisc(unittest.TestCase):

    def test_download(self):
        date = datetime(year=2024, month=4, day=3, hour=12) # Random Day
        virtual_file = _download_set(date) 

        with zipfile.ZipFile(virtual_file) as zip:
            needed_files = [file.filename for file in zip.filelist if file.filename.endswith("_fileconnectivity.ascii")]
            self.assertEqual(len(needed_files), 1)

            file_content = zip.read(needed_files[0])
            # Each file contains the exact time of recording
            # 2024-05-31 18:00:00
            file_date = file_content.decode().splitlines()[17]
            parsed_date = datetime.fromisoformat(file_date)

            self.assertEqual(parsed_date, date)




if __name__ == "__main__":
    unittest.main()