from Database import Database
from MusicManager import MusicManager

sql = Database().sql_connect()

def normalise_track(track_dict):
    keys = ['id', 'title', 'author', 'album', 'year']
    return {key: track_dict[key] for key in keys}

def get_track_by_id(id):
    cursor = sql.cursor()
    cursor.execute("""
    SELECT * FROM tracks WHERE id = ?
    """, (id,))
    return cursor.fetchone()

def get_tracks_by_album(album_name, author=None):
    cursor = sql.cursor()
    if author is None:
        cursor.execute("""
        SELECT * FROM tracks WHERE album = ? ORDER BY title
        """, (album_name, ))
    else:
        cursor.execute("""
        SELECT * FROM tracks WHERE album = ? AND author = ? ORDER BY title
        """, (album_name, author, ))
    return cursor.fetchall()

def get_tracks_by_author(author):
    cursor = sql.cursor()
    cursor.execute("""
    SELECT * FROM tracks WHERE author = ? ORDER BY title
    """, (author,))

def search_tracks(query):
    """Ищет каждое слово в полях: title, author, album, year"""
    cursor = sql.cursor()

    if not query or query.strip() == '':
        return []

    clean_query = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in query)
    words = clean_query.strip().split()

    if not words:
        return []

    conditions = []
    params = []

    for word in words:
        # Дополнительная проверка: слово не должно быть пустым и должно содержать только безопасные символы
        if not word or len(word.strip()) == 0:
            continue

        # "Экранируем" спецсимволы SQL LIKE (%, _) во избежание инъекций
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
    SELECT id, title, author, album, year, length
    FROM tracks
    WHERE {substrings}
    ORDER BY title
    """

    cursor.execute(query_sql, params)
    return cursor.fetchall()

def organize_files(printLogs=False):
    """Файлы музыки будут автоматом организованы в правильную папку и указаны в БД"""
    manager = MusicManager()
    manager.organize_files(printLogs)

def organize_single_file(file, printLogs=False):
    """Один конкретный файл организует по папкам и добавляет в БД"""
    manager = MusicManager()
    return manager.organize_single_file(file, printLogs)

def delete_track_by_id(track_id, print_logs=True):
    manager = MusicManager()
    return manager.delete_track(track_id, print_logs)

if __name__ == "__main__":
    results = get_track_by_id(35)

    try:
        if results:
            for row in results:
                print(dict(row))
        else: print(results)
    except TypeError: print(dict(results))
