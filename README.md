# Metadata Retrieval for calibre from Google Scholar

``calibre-debug -s; calibre-customize -b googlescholar-metadata/; calibre``


- **2022-11-25** python scholarly hardly to integrate into calibre as it depends not just on urllib3 and requests but also on selenium which was impossible to put into a standalone plugin of calibres structure; gscholar seems to be a simple alternative to previous code
