from app.utils import video_utils


def test_is_problematic_filename():
    assert video_utils.is_problematic_filename("bad file.mp4")
    assert not video_utils.is_problematic_filename("good_file.mp4")


def test_decode_filename():
    encoded = "video%20file.mp4"
    assert video_utils.decode_filename(encoded) == "video file.mp4"

