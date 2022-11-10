from plib import Path


def test_yaml():
    content = {"hello": "world"}
    with Path.tempfile().with_suffix(".yaml") as temp_path:
        temp_path.yaml = content
        assert temp_path.yaml == content
