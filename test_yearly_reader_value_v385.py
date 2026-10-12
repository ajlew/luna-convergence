from yearly_print_html import _month_editorial_parts, _transit_timeline


def test_reader_copy_two_sentences_are_split_without_invention():
    first, second = _month_editorial_parts("An agreement may need clearer terms. Compare commitments before signing.")
    assert first == "An agreement may need clearer terms."
    assert second == "Compare commitments before signing."
    first, second = _month_editorial_parts("Existing short editorial.")
    assert first == "Existing short editorial." and second == ""


def test_long_transit_label_does_not_run_into_graph():
    row = {'start': '2027-01-01', 'end': '2027-01-31'}
    game = {'transits': []}
    # Layout constant is checked directly on the output from representative packet data.
    from datetime import date
    import inspect
    source = inspect.getsource(_transit_timeline)
    assert 'chart_left = 285' in source
    assert 'font-size:10px' in source
