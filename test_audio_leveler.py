
import unittest
import os
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

import audio_leveler

class TestAudioLeveler(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path('test_media')
        self.test_dir.mkdir()
        (self.test_dir / 'video1.mkv').touch()
        (self.test_dir / 'video2.mp4').touch()
        (self.test_dir / 'not_media.txt').touch()
        self.test_file = self.test_dir / 'video1.mkv'

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_media_files(self):
        """Test that media files are found correctly."""
        files = audio_leveler.get_media_files(self.test_dir)
        self.assertEqual(len(files), 2)
        extensions = {f.suffix for f in files}
        self.assertIn('.mkv', extensions)
        self.assertIn('.mp4', extensions)

    @patch('audio_leveler.subprocess.run')
    @patch('audio_leveler.get_stream_info')
    def test_process_file_success(self, mock_get_stream_info, mock_subprocess_run):
        """Test the success case for processing a file."""
        # Mocking ffmpeg pass 1 (analysis)
        mock_pass1_result = Mock()
        mock_pass1_result.returncode = 0
        mock_pass1_result.stderr = """
        [Parsed_loudnorm_0 @ 0x55555555]
        {
            "input_i" : "-14.0",
            "input_tp" : "1.5",
            "input_lra" : "10.0",
            "input_thresh" : "-24.0",
            "output_i" : "-23.9",
            "output_tp" : "-2.0",
            "output_lra" : "7.0",
            "output_thresh" : "-34.0",
            "target_offset" : "0.1"
        }
        """
        
        # Mocking ffmpeg pass 2 (normalization)
        mock_pass2_result = Mock()
        mock_pass2_result.returncode = 0
        mock_pass2_result.stderr = ""

        mock_subprocess_run.side_effect = [mock_pass1_result, mock_pass2_result]
        
        # Mocking stream info for verification
        mock_get_stream_info.return_value = {'format': {'duration': '120.0'}}

        # Create a dummy file to be "processed"
        dummy_file_content = "dummy content"
        with open(self.test_file, "w") as f:
            f.write(dummy_file_content)

        # The temp file needs to exist for os.replace to work
        tmp_path = self.test_file.with_suffix(self.test_file.suffix + '.tmp')
        with open(tmp_path, "w") as f:
            f.write("new content")

        status, duration = audio_leveler.process_file(self.test_file)

        self.assertEqual(status, "processed")
        self.assertTrue(mock_subprocess_run.call_count == 2)
        # Check that os.replace was called, which means the file was processed
        self.assertTrue(os.path.exists(self.test_file))

    @patch('audio_leveler.subprocess.run')
    def test_process_file_skip(self, mock_subprocess_run):
        """Test the skip case for processing a file."""
        # Mocking ffmpeg pass 1 (analysis)
        mock_pass1_result = Mock()
        mock_pass1_result.returncode = 0
        mock_pass1_result.stderr = f"""
        [Parsed_loudnorm_0 @ 0x55555555]
        {{
            "input_i" : "{audio_leveler.LOUDNESS_TARGETS['I']}",
            "input_tp" : "0.0",
            "input_lra" : "7.0",
            "input_thresh" : "-34.0",
            "output_i" : "-23.9",
            "output_tp" : "-2.0",
            "output_lra" : "7.0",
            "output_thresh" : "-34.0",
            "target_offset" : "0.0"
        }}
        """
        mock_subprocess_run.return_value = mock_pass1_result

        status, duration = audio_leveler.process_file(self.test_file)

        self.assertEqual(status, "skipped")
        self.assertEqual(mock_subprocess_run.call_count, 1)

    @patch('audio_leveler.subprocess.run')
    def test_process_file_fail_pass1(self, mock_subprocess_run):
        """Test the fail case for processing a file in pass 1."""
        # Mocking ffmpeg pass 1 (analysis)
        mock_pass1_result = Mock()
        mock_pass1_result.returncode = 1
        mock_pass1_result.stderr = "Error"
        mock_subprocess_run.return_value = mock_pass1_result

        status, duration = audio_leveler.process_file(self.test_file)

        self.assertEqual(status, "failed")
        self.assertEqual(mock_subprocess_run.call_count, 1)

if __name__ == '__main__':
    unittest.main()
