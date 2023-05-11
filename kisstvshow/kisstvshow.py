from urllib.parse import urljoin

import requests

from kisstvshow.utils import parse_to_bs4


DEFAULT_URL = "https://kisstvshow.to/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"


class KissTVShow:
    def __init__(self, url: str | None = None) -> None:
        self.url = url if url is not None else DEFAULT_URL

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self._login_cookies = {}

    def login(self, username: str, password: str):
        login_url = urljoin(self.url, "Login")

        r = self.session.post(
            login_url,
            data={
                "username": username,
                "password": password,
                "chkRemember": "on",
                "redirect": "",
            },
        )

        if r.status_code == 200:
            return True

        return False

    def search(self, query: str):
        search_url = urljoin(self.url, "Search/Show")

        r = self.session.post(search_url, data={"keyword": query})

        if r.status_code != 200:
            raise Exception("There was a problem when trying to search shows. ", r)

        soup = parse_to_bs4(r.text)
        container = soup.find("table", class_="listing")
        if container is None:
            return []

        results = []

        for i in container.select("tr:not(.head)")[1:]:
            tds = i.find_all("td")

            # get only relevant details
            show_title = tds[0].find("a").get_text().strip()
            show_link = urljoin(self.url, tds[0].find("a")["href"])
            show_latest = tds[1].get_text().strip()
            show_just_updated = (
                True if i.find("img", attrs={"title": "Just updated"}) else False
            )
            show_hot = True if i.find("img", attrs={"title": "Popular show"}) else False

            # append
            results.append(
                {
                    "title": show_title,
                    "link": show_link,
                    "latest": show_latest,
                    "just_updated": show_just_updated,
                    "hot": show_hot,
                }
            )

        return results
