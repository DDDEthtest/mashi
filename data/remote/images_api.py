import time
import requests


class ImagesApi:
    def get_image_src(self, image_url: str):
        for i in range(5):
            try:
                res = requests.get(image_url)

                if res.status_code != 200:
                    time.sleep(1)
                    continue

                return res.content

            except Exception as e:
                print(e)
                continue

        for i in range(5):
            try:
                res = requests.get(image_url.replace("ipfs.", "ipfs.filebase."))

                if res.status_code != 200:
                    time.sleep(1)
                    continue

                return res.content

            except Exception as e:
                print(e)
                continue

        return None

