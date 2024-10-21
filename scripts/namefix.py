from os import rename
from pathlib import Path

if __name__ == "__main__":
    source = Path(__file__).parent.parent.joinpath("results")
    for fp in source.iterdir():
        if ".." in fp.name:
            new_path = fp.parent.joinpath(fp.name.replace("..", "."))
            rename(fp, new_path)
