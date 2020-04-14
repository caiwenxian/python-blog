


def get_page_index(page):
    if page is None or str(page) == '1':
        return 0
    else:
        return (page - 1) * 10

