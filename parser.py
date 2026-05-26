import re

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        commands = []
        while self.pos < len(self.tokens):
            token_type, token_value = self.tokens[self.pos]
            method = getattr(self, f"_parse_{token_type.lower()}", None)
            if method:
                commands.append(method(token_value))
            else:
                # Unknown or unimplemented command
                commands.append(f"# TODO: Implement {token_type} ({token_value})")
            self.pos += 1
        return commands

    def _parse_load(self, token):
        m = re.search(r"LOAD(\s+'([^']+)')?\s*;", token)
        if not m:
            raise ValueError(f"Malformed LOAD command: {token}")
        file_name = m.group(2)
        if file_name:
            return f"df = pd.read_csv('{file_name}')"
        else:
            # No filename provided, skip or raise error as appropriate
            return "# LOAD command without filename ignored"

    def _parse_save(self, token):
        m = re.search(r"SAVE\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed SAVE command: {token}")
        file_name = m.group(1)
        return f"df.to_csv('{file_name}', index=False)"

    def _parse_drop(self, token):
        m = re.search(r"DROP\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed DROP command: {token}")
        column_name = m.group(1)
        return f"df = df.drop(columns=['{column_name}'])"

    def _parse_dropna(self, token):
        return "df = df.dropna()"

    def _parse_fillna(self, token):
        m = re.search(r"FILLNA\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed FILLNA command: {token}")
        col, val = m.group(1), m.group(2)
        return f"df['{col}'] = df['{col}'].fillna('{val}')"

    def _parse_rename(self, token):
        m = re.search(r"RENAME\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed RENAME command: {token}")
        old_name, new_name = m.group(1), m.group(2)
        return f"df = df.rename(columns={{'{old_name}': '{new_name}'}})"

    def _parse_duplicates(self, token):
        return "df = df.drop_duplicates()"

    def _parse_unique(self, token):
        m = re.search(r"UNIQUE\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed UNIQUE command: {token}")
        col = m.group(1)
        return f"df['{col}'].unique()"

    def _parse_head(self, token):
        n = int(token.split()[1].replace(';', ''))
        return f"df = df.head({n})"

    def _parse_tail(self, token):
        n = int(token.split()[1].replace(';', ''))
        return f"df = df.tail({n})"

    def _parse_sort(self, token):
        m = re.search(r"SORT\s+'([^']+)'\s+(ASC|DESC)", token)
        if not m:
            raise ValueError(f"Malformed SORT command: {token}")
        col, order = m.group(1), m.group(2)
        order = "False" if order == "DESC" else "True"
        return f"df = df.sort_values(by='{col}', ascending={order})"

    def _parse_reset_index(self, token):
        return "df = df.reset_index(drop=True)"

    def _parse_set_index(self, token):
        m = re.search(r"SET_INDEX\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed SET_INDEX command: {token}")
        col = m.group(1)
        return f"df = df.set_index('{col}')"

    def _parse_filter(self, token):
        m = re.search(r"FILTER\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed FILTER command: {token}")
        condition = m.group(1)
        return f"df = df.query('{condition}')"

    def _parse_query(self, token):
        m = re.search(r"QUERY\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed QUERY command: {token}")
        condition = m.group(1)
        return f"df = df.query('{condition}')"

    def _parse_describe(self, token):
        return "df.describe()"

    def _parse_info(self, token):
        return "df.info()"

    def _parse_shape(self, token):
        return "df.shape"

    def _parse_columns(self, token):
        return "df.columns"

    def _parse_duplicate_rows(self, token):
        return "df[df.duplicated()]"

    def _parse_isnull(self, token):
        return "df.isnull()"

    def _parse_notnull(self, token):
        return "df.notnull()"

    def _parse_value_counts(self, token):
        m = re.search(r"VALUE_COUNTS\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed VALUE_COUNTS command: {token}")
        col = m.group(1)
        return f"df['{col}'].value_counts()"

    def _parse_apply(self, token):
        m = re.search(r"APPLY\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed APPLY command: {token}")
        col, func = m.group(1), m.group(2)
        return f"df['{col}'] = df['{col}'].apply({func})"

    def _parse_map(self, token):
        m = re.search(r"MAP\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed MAP command: {token}")
        col, func = m.group(1), m.group(2)
        return f"df['{col}'] = df['{col}'].map({func})"

    def _parse_replace(self, token):
        m = re.search(r"REPLACE\s+'([^']+)'\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed REPLACE command: {token}")
        old, new, col = m.group(1), m.group(2), m.group(3)
        return f"df['{col}'] = df['{col}'].replace('{old}', '{new}')"

    def _parse_strip(self, token):
        m = re.search(r"STRIP\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed STRIP command: {token}")
        col = m.group(1)
        return f"df['{col}'] = df['{col}'].str.strip()"

    def _parse_lower(self, token):
        m = re.search(r"LOWER\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed LOWER command: {token}")
        col = m.group(1)
        return f"df['{col}'] = df['{col}'].str.lower()"

    def _parse_upper(self, token):
        m = re.search(r"UPPER\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed UPPER command: {token}")
        col = m.group(1)
        return f"df['{col}'] = df['{col}'].str.upper()"

    def _parse_concat(self, token):
        m = re.search(r"CONCAT\s+'([^']+)'\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed CONCAT command: {token}")
        col1, col2, newcol = m.group(1), m.group(2), m.group(3)
        return f"df['{newcol}'] = df['{col1}'].astype(str) + df['{col2}'].astype(str)"

    def _parse_split(self, token):
        m = re.search(r"SPLIT\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed SPLIT command: {token}")
        col, sep = m.group(1), m.group(2)
        return f"df['{col}'] = df['{col}'].str.split('{sep}')"

    def _parse_merge(self, token):
        # Placeholder: actual merge logic requires another DataFrame
        return "# TODO: Implement MERGE"

    def _parse_join(self, token):
        # Placeholder: actual join logic requires another DataFrame
        return "# TODO: Implement JOIN"

    def _parse_groupby(self, token):
        m = re.search(r"GROUPBY\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed GROUPBY command: {token}")
        col, agg = m.group(1), m.group(2)
        return f"df = df.groupby('{col}').agg('{agg}')"

    def _parse_pivot(self, token):
        # Placeholder: actual pivot logic
        return "# TODO: Implement PIVOT"

    def _parse_melt(self, token):
        # Placeholder: actual melt logic
        return "# TODO: Implement MELT"

    def _parse_aggregate(self, token):
        m = re.search(r"AGGREGATE\s+'([^']+)'\s+'([^']+)'\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed AGGREGATE command: {token}")
        col, by, func = m.group(1), m.group(2), m.group(3)
        return f"df = df.groupby('{by}')['{col}'].agg('{func}')"

    def _parse_sum(self, token):
        m = re.search(r"SUM\s+'([^']+)'", token)
        if not m:
            raise ValueError(f"Malformed SUM command: {token}")
        col = m.group(1)
        return f"df['{col}'].sum()"
    def _parse_cov(self, token):
        parts = token.split("'")
        col1, col2 = parts[1], parts[3]
        return f"df['{col1}'].cov(df['{col2}'])"

    def _parse_sample(self, token):
        n = int(token.split()[1].replace(';', ''))
        return f"df = df.sample({n})"

    def _parse_drop_duplicates(self, token):
        return "df = df.drop_duplicates()"

    def _parse_reindex(self, token):
        col = token.split("'")[1]
        return f"df = df.reindex(columns=['{col}'])"

    def _parse_transpose(self, token):
        return "df = df.transpose()"
