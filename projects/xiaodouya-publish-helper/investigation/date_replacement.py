def detect_date_from_filename(path, today=None):
    """Accept a unique direct-parent delivery date; reject conflicts and ambiguity."""
    source=Path(path)
    reference=today or date.today()
    filename_values=_dates_in_text(source.stem,reference)
    folder_values=_dates_in_text(source.parent.name,reference)
    if len(filename_values)>1 or len(folder_values)>1:
        return ''
    if folder_values:
        if filename_values and filename_values[0]!=folder_values[0]:
            return ''
        return folder_values[0]
    return filename_values[0] if len(filename_values)==1 else ''
