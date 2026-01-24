import requests


class ImagesApi:
    def get_image_src(self, image_url: str):
        try:
            res = requests.get(image_url)
            if res.status_code != 200:
                return None

            return res.content

        except Exception as e:
            print(e)
            return None
