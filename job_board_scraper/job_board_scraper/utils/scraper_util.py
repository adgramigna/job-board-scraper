def get_url_chunks(careers_page_urls, chunk_size):
    url_chunks = []
    single_chunk = []
    for i, url in enumerate(careers_page_urls):
        careers_page_url = url[0]  # UnTuple-ify
        single_chunk.append(careers_page_url)
        if i % chunk_size == chunk_size - 1:
            url_chunks.append(single_chunk)
            single_chunk = []
    if len(single_chunk) > 0:
        url_chunks.append(single_chunk)
    return url_chunks
