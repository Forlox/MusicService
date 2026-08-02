from Database import Database
from MusicManager.MusicManager import MusicManager

_manager = MusicManager()
_db = Database()

def _get_cursor():
    return _db.sql_connect().cursor()

def get_track_by_id(id, normalise=True):
    cursor = _get_cursor()
    if normalise:
        cursor.execute("""
        SELECT id, title, author, album, year FROM tracks WHERE id = ?
        """, (id,))
    else:
        cursor.execute("SELECT * FROM tracks WHERE id = ?", (id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_tracks_by_album(album_name, author=None):
    cursor = _get_cursor()
    if author is None:
        cursor.execute("""
        SELECT id, title, author, album, year FROM tracks WHERE album = ? ORDER BY title
        """, (album_name, ))
    else:
        cursor.execute("""
        SELECT id, title, author, album, year FROM tracks WHERE album = ? AND author = ? ORDER BY title
        """, (album_name, author, ))
    return [dict(row) for row in cursor.fetchall()]

def get_tracks_by_author(author):
    cursor = _get_cursor()
    cursor.execute("""
    SELECT id, title, author, album, year FROM tracks WHERE author = ? ORDER BY title
    """, (author,))
    return [dict(row) for row in cursor.fetchall()]

def search_tracks(query):
    """Ищет каждое слово в полях: title, author, album, year"""
    cursor = _get_cursor()

    if not query or query.strip() == '':
        return []

    clean_query = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in query)
    words = clean_query.strip().split()

    if not words:
        return []

    conditions = []
    params = []

    for word in words:
        if not word or len(word.strip()) == 0:
            continue

        safe_word = word.replace('%', '\\%').replace('_', '\\_')

        condition = """
        (title LIKE ? ESCAPE '\\' OR author LIKE ? ESCAPE '\\' OR album LIKE ? ESCAPE '\\' OR year LIKE ? ESCAPE '\\')
        """
        conditions.append(condition)

        like_param = f'%{safe_word}%'
        params.extend([like_param, like_param, like_param, like_param])

    if not conditions:
        return []

    substrings = ' AND '.join(conditions)
    query_sql = f"""
    SELECT id, title, author, album, year
    FROM tracks
    WHERE {substrings}
    ORDER BY title
    """

    cursor.execute(query_sql, params)
    return [dict(row) for row in cursor.fetchall()]

def _organize_files(printLogs=False):
    """Организация файлов треков, синхронизация с БД"""
    _manager.organize_files(printLogs)

def add_music_file(file, printLogs=False):
    """Один конкретный файл организует по папкам и добавляет в БД"""
    return _manager.add_music_file(file, printLogs)

def delete_track_by_id(track_id, print_logs=True):
    return _manager.delete_track(track_id, print_logs)

if __name__ == "__main__":
    result = ""

    try:
        if result:
            for row in result:
                print(dict(row))
        else:
            print(result)
    except TypeError:
        print(dict(result))