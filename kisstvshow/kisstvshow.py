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
            show_link_short = tds[0].find("a")["href"]
            show_link_complete = urljoin(self.url, show_link_short)

            latest_item = tds[1]
            show_latest = latest_item.get_text().strip()
            show_latest_url = ""
            if latest_item.find("a"):
                show_latest_url = urljoin(self.url, latest_item.find("a").get("href"))

            show_just_updated = (
                True if i.find("img", attrs={"title": "Just updated"}) else False
            )
            show_hot = True if i.find("img", attrs={"title": "Popular show"}) else False

            # append
            results.append(
                {
                    "title": show_title,
                    "link": {"short": show_link_short, "complete": show_link_complete},
                    "latest": {
                        "title": show_latest,
                        "url": show_latest_url,
                    },
                    "just_updated": show_just_updated,
                    "hot": show_hot,
                }
            )

        return results

    def get_show(self, show: str | None = None, url: str | None = None):
        if show is None and url is None:
            raise Exception("Requires atleast one of `show`  or `url` parameters.")

        final_url = ""
        if show is not None:
            if show.startswith("/Show/") or show.startswith("Show/"):
                final_url = urljoin(self.url, show)
            else:
                final_url = urljoin(self.url, f"Show/{show.strip('/')}")

        if url is not None:
            if "/Show/" in url:
                final_url = url

        if final_url == "":
            raise Exception("Final url is empty, is `show` or `url` correct?")

        r = self.session.get(final_url)
        if r.status_code != 200:
            raise Exception("There was a problem when trying to search shows. ", r)

        soup = parse_to_bs4(r.text)
        container = soup.find("div", id="container")

        # get image cover
        show_cover = urljoin(
            self.url,
            container.find("div", id="rightside")
            .find("div", class_="barContent")
            .find("img")
            .get("src"),
        )

        # parse main info / details
        header_ = container.find("div", class_="barContent")

        show_item_ = header_.find("a", class_="bigChar")
        show_title = show_item_.get_text().strip()
        show_link_short = show_item_.get("href")
        show_link_complete = urljoin(self.url, show_link_short)

        details = header_.find_all("p")
        show_details = {}
        for i in details:
            d_title_ = i.find("span", class_="info")

            if d_title_ is None:
                continue

            d_title_text = d_title_.get_text()

            if "Summary" in d_title_text:
                continue
            if "Bookmark" in d_title_text:
                continue

            if "Status" in d_title_text:
                d_more_items = [
                    k.replace("\xa0", "").strip()
                    for k in i.get_text().split(" ")
                    if k != ""
                ]
                show_details["Status"] = d_more_items[0].split(":")[1].strip()
                show_details["Views"] = d_more_items[1].split(":")[1].strip()

                continue

            d_value_ = i.get_text().replace(d_title_text, "").strip()
            show_details[d_title_text.replace(":", "").strip()] = d_value_

        show_details["Summary"] = details[-1].get_text().strip()

        # parse episodes
        episode_table = container.find("table", class_="listing")
        episodes_list = episode_table.find_all("tr")[2:]
        all_episodes = []

        for i in episodes_list:
            ep_tds = i.find_all("td")

            episode_title = ep_tds[0].get_text().strip()
            ep_link = ep_tds[0].find("a")
            episode_link_short = ep_link.get("href")
            episode_link_complete = urljoin(self.url, ep_link.get("href"))
            episode_day_added = ep_tds[1].get_text().strip()

            all_episodes.append(
                {
                    "name": episode_title,
                    "link": {
                        "short": episode_link_short,
                        "complete": episode_link_complete,
                    },
                    "day_added": episode_day_added,
                }
            )

        # parse casts
        casts_container = container.find("div", class_="list-actor")
        casts = [
            k.get_text().strip()
            for k in casts_container.find_all("div", class_="actor-info")
        ]

        return {
            "title": show_title,
            "cover": show_cover,
            "link": {
                "short": show_link_short,
                "complete": show_link_complete,
            },
            "details": show_details,
            "episodes": all_episodes,
            "casts": casts,
        }
