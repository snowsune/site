import os
from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


class RandalFanclubView(TemplateView):
    template_name = "randal_fanclub/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get media directory path
        media_dir = os.path.join(settings.MEDIA_ROOT, "randal_fanclub")

        # Hardcoding by year
        context["years"] = [
            {
                "year": "2025",
                "images": [
                    {
                        "filename": "2025/2025 Randal Fanclub.png",
                        "title": "2025 Beach Party!",
                        "description": """Thank you so much <a href='https://www.furaffinity.net/user/tailster13' target='_blank' rel='noopener'>tailster</a> for drawing us once more~ 
                        We got to include their OC frisky as the dog serving their frisky treats! Thank you Tailster!
                        
                        From Left to right, 
                        Katherine Tassler
                        Randal Tassler
                        Vixi Argorrok
                        Galios
                        Luci
                        Ky-Li
                        Shaezie
                        Ruby
                        Aryaltel
                        Hyna
                        Frisky
                        Sinopa
                        Xayla

                        Artist of course~ tailster13 tailster13""",
                        "nsfw": False,
                    },
                    {
                        "filename": "2025/2025 Randal Fanclub (Nude).png",
                        "title": "2025 Randal Fanclub (NSFW)",
                        "description": """Spicy version of the 2025 beach party~
                        If Randal's still wearing his collar, is it really nudity?~""",
                        "nsfw": True,
                    },
                    {
                        "filename": "2025/shae/Shae_summer_with_friends_swimsuitsSunset2.png",
                        "title": "Shae's Summer Special",
                        "description": """A special <a href="https://www.furaffinity.net/user/insydnis" target="_blank" rel="noopener">Shaezie</a> alt with custom music!
                        
                        Link to her track here: <a href="/media/randal_fanclub/2025/shae/Summer of Unity.mp3" target="_blank" rel="noopener">Summer of Unity.mp3</a>
                        
                        It's a beautiful shae-vibe edit <3 Thank you!""",
                        "nsfw": False,
                    },
                ],
            },
            {
                "year": "2024",
                "images": [
                    {
                        "filename": "2024/RandalGroupPicCosplay.png",
                        "title": "Group Cosplay Photo",
                        "description": """Another piece by the lovely <a href='https://www.furaffinity.net/user/tailster13' target='_blank' rel='noopener'>tailster</a>!
                        
                        Dressing up in our favorite characters was absolutly adorable <3

                        From left to right (And including the characters we're cosplaying as~)
                        Ky-Li as Renamon (Digimon)
                        Vixi as Florence Ambrose (Freefall)
                        Luci as Doctor Strange (Marvel)
                        Dalia as Maid Marian (Disney)
                        Shaezie as Sly Cooper (Sony)
                        Chrissy as Scorch (LucasFilm)
                        Randal as Rubedo (Namco)
                        Yeen as Ai from oshi no ko
                        Byakko as Felix
                        Chloe as Krystal (Nintnendo)
                        Maxene as Helluva Boss version (Vivziepop)
                        Aryaltel as Diane Foxington (Universal) """,
                        "nsfw": False,
                    },
                ],
            },
            {
                "year": "2023",
                "images": [
                    {
                        "filename": "2023/randalgrouppicsfw.png",
                        "title": "Group Photo (SFW)",
                        "description": """First appearance of the Kyouch I think~
                        
                        Art done  by <a href='https://www.furaffinity.net/user/tailster13' target='_blank' rel='noopener'>tailster</a> ofc!
                        And such a lovely piece too~ With two lewd alts below! Thank you tailster and everyone who joined in~
                        
                        From left to right
                        Vixi
                        Luci
                        Charolotte
                        Ky-Li (Laying down)
                        Yeen (2 characters)
                        Shae
                        Randal
                        Aryaltel
                        Loretta
                        Dalia (kneeling)
                        Kamryn
                        Vera~""",
                        "nsfw": False,
                    },
                    {
                        "filename": "2023/randalgrouppicNSFW.png",
                        "title": "Group Photo (NSFW)",
                        "description": """Nude version~""",
                        "nsfw": True,
                    },
                    {
                        "filename": "2023/randalgrouppicNSFWver2.png",
                        "title": "Group Photo (NSFW v2)",
                        "description": """Drippy version!""",
                        "nsfw": True,
                    },
                ],
            },
            {
                "year": "2022",
                "images": [
                    {
                        "filename": "2022/Randal Fanclub 2022.png",
                        "title": "Randal Fanclub 2022",
                        "description": """The very first one!
                        This one was done by our own <a href="https://www.furaffinity.net/user/graymt">Dalia</a>! 
                        Thank you so much~
                        <br><br>
                        From left to right
                        Dalia
                        Shaezie
                        Randal
                        Luci
                        Vera
                        Vixi
                        Yeen
                        """,
                        "nsfw": False,
                    },
                ],
            },
        ]

        return context
