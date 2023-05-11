from bs4 import BeautifulSoup


def parse_to_bs4(src: str):
    return BeautifulSoup(src, "lxml")
