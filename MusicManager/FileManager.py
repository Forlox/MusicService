from pathlib import Path
import mutagen, shutil, time

EXTENSIONS = {'.mp3', '.flac', '.wav'}
MUSIC_DIR = Path("../Music")


def scan(folder):
    files = []
    for file in Path(folder).rglob('*'):
        if file.suffix.lower() in EXTENSIONS:
            files.append(file)
    return files

def get_metadata(file_path):
    track = mutagen.File(file_path, easy=True)
    if not track:
        return None
    return track

def normalize_author(author):
    separators = [',', ';', '&', ' feat.', ' feat ', 'ft.', ' ft ']
    for sep in separators:
        if sep in author:
            author = author.split(sep)[0]
    return author.strip()

class FileManager:
    def __init__(self):
        self.tracks = []

    def run(self):
        for file in scan(MUSIC_DIR):
            self.process(file)

    def process(self, file):
        data = get_metadata(file)

        if not data:
            return

        try:
            author = normalize_author(data["artist"][0])
        except KeyError:
            author = "Unknown"

        try:
            album = data["album"][0].strip()
        except KeyError:
            album = None

        if album:
            folder = MUSIC_DIR / author / album
        else:
            folder = MUSIC_DIR / author

        folder.mkdir(parents=True, exist_ok=True)

        new_path = folder / file.name
        if file != new_path:
            shutil.move(file, new_path)

        self.save(data, new_path, author, album)

        self.tracks.append({
            "title": data.get("title", ["Unknown"])[0],
            "author": author,
            "album": album,
            "year": data.get("date",[None])[0],
            "file_path": str(new_path)
        })

    def save(self, data, path, author, album):
        print(f"{data.get('title', ['Unknown'])[0]} | {author} | {album or 'Нет'} | {path}")

if __name__ == "__main__":
    start_time = time.time()
    FileManager().run()
    end_time = time.time()
    print(f"\nВыполнено за {round(end_time-start_time, 2)} сек")