from Database import Database

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
    if author == None:
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


if __name__ == "__main__":
    results = search_tracks("Океан")

    try:
        if results:
            for row in results:
                print(dict(row))
    except TypeError: print(dict(results))