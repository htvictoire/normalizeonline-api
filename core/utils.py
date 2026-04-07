def parse_form_data(form_data):
    """
    Minimal generic parser for bracket notation.
    Examples:
      name
      items[0][title]
      items[0][tags][0]
      items[1][meta][flags][0]
    """
    payload = {}

    for key, value in form_data.items():
        tokens = []
        current = ""
        in_brackets = False
        for char in key:
            if char == "[":
                if current:
                    tokens.append(current)
                current = ""
                in_brackets = True
                continue
            if char == "]":
                tokens.append(current)
                current = ""
                in_brackets = False
                continue
            current += char
        if current and not in_brackets:
            tokens.append(current)

        if not tokens:
            continue

        cursor = payload
        for i, token in enumerate(tokens):
            is_last = i == len(tokens) - 1
            next_token = tokens[i + 1] if not is_last else None
            next_is_index = next_token is not None and next_token.isdigit()

            if token.isdigit():
                index = int(token)
                if not isinstance(cursor, list):
                    cursor_parent = cursor
                    cursor = []
                    if isinstance(cursor_parent, dict):
                        cursor_parent_key = tokens[i - 1]
                        cursor_parent[cursor_parent_key] = cursor
                while len(cursor) <= index:
                    cursor.append(None)
                if is_last:
                    cursor[index] = value
                else:
                    if cursor[index] is None:
                        cursor[index] = [] if next_is_index else {}
                    cursor = cursor[index]
            else:
                if is_last:
                    if isinstance(cursor, dict):
                        cursor[token] = value
                else:
                    if token not in cursor or cursor[token] is None:
                        cursor[token] = [] if next_is_index else {}
                    cursor = cursor[token]

    return payload
