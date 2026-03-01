import re


def validate_url(url: str) -> str:
    patterns = [
        r'carid=(\d+)',
        r'/detail/(\d+)',
        r'/(\d+)\?',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return ''