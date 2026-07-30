import os
import tempfile
import pytest
from enstruct.outputs.srt_writer import SRTWriter, format_srt_timestamp
from enstruct.outputs.vtt_writer import VTTWriter, format_vtt_timestamp
from enstruct.outputs.txt_writer import TXTWriter
from enstruct.tools.subtitle import SubtitleGenerator


def test_timestamp_formatting():
    assert format_srt_timestamp(0.0) == "00:00:00,000"
    assert format_srt_timestamp(3661.123) == "01:01:01,123"

    assert format_vtt_timestamp(0.0) == "00:00:00.000"
    assert format_vtt_timestamp(3661.123) == "01:01:01.123"


def test_srt_writer():
    segments = [
        {"start": 0.5, "end": 2.1, "text": "First segment."},
        {"start": 2.5, "end": 4.0, "text": "Second segment."}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.srt")
        SRTWriter.write(segments, output_file)

        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "1\n" in content
        assert "00:00:00,500 --> 00:00:02,100\n" in content
        assert "First segment.\n" in content
        assert "2\n" in content
        assert "00:00:02,500 --> 00:00:04,000\n" in content
        assert "Second segment.\n" in content


def test_vtt_writer():
    segments = [
        {"start": 1.0, "end": 3.5, "text": "Hello world!"}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.vtt")
        VTTWriter.write(segments, output_file)

        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert content.startswith("WEBVTT\n\n")
        assert "1\n" in content
        assert "00:00:01.000 --> 00:00:03.500\n" in content
        assert "Hello world!\n" in content


def test_txt_writer():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Segment one."},
        {"start": 1.0, "end": 2.0, "text": "Segment two."}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.txt")
        TXTWriter.write(segments, output_file)

        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 2
        assert lines[0] == "Segment one."
        assert lines[1] == "Segment two."


def test_subtitle_generator_supported():
    segments = [{"start": 0.0, "end": 1.0, "text": "Test"}]
    generator = SubtitleGenerator()

    with tempfile.TemporaryDirectory() as tmpdir:
        srt_path = os.path.join(tmpdir, "out.srt")
        vtt_path = os.path.join(tmpdir, "out.vtt")
        txt_path = os.path.join(tmpdir, "out.txt")

        generator.generate(segments, srt_path, format="srt")
        generator.generate(segments, vtt_path, format="vtt")
        generator.generate(segments, txt_path, format="txt")

        assert os.path.exists(srt_path)
        assert os.path.exists(vtt_path)
        assert os.path.exists(txt_path)


def test_subtitle_generator_invalid_format():
    generator = SubtitleGenerator()
    with pytest.raises(ValueError):
        generator.generate([], "out.pdf", format="pdf")
