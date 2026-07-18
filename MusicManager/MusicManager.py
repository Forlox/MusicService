from pathlib import Path
import mutagen, shutil

EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav"
}
MUSIC_DIR = Path("../Music")



def scan(folder):
    files = []
    for file in Path(folder).rglob("*"):
        if file.suffix.lower() in EXTENSIONS:
            files.append(file)

    return files

def get_metadata(file_path):
    track = mutagen.File(file_path, easy=True)
    if not track:
        return None
    return track


class MusicManager:
    def run(self):
        for file in scan(MUSIC_DIR):
            if file.parent != MUSIC_DIR:
                continue
            self.process(file)

    def process(self, file):
        data = get_metadata(file)

        if not data:
            return

        try:
            author = data["artist"][0].split(",")[0].strip()
        except KeyError:
            author = "Unknown"

        try:
            album = data["album"][0]
        except KeyError:
            album = None

        if album:
            folder = MUSIC_DIR / author / album
        else:
            folder = MUSIC_DIR / author

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        new_path = folder / file.name

        shutil.move(
            file,
            new_path
        )

        data["file_path"] = str(new_path)

        self.save(data)

    def save(self, data):
        print(
            "Добавлен:",
            "Название:", data.get("title", ["Unknown"])[0],
            "Автор:", data.get("artist", ["Unknown"])[0],
            "Альбом:", data.get("album", ["Unknown"])[0],
            "Path:", data.get("file_path")
        )


if __name__ == "__main__":
    musManager = MusicManager()
    musManager.run()