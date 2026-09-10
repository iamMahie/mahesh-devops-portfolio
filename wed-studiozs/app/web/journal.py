"""Curated photographs from the studio's public Instagram, not a live feed."""

from dataclasses import dataclass

from app.models.enums import PortfolioCategory


@dataclass(frozen=True)
class JournalStory:
    slug: str
    title: str
    category: PortfolioCategory
    description: str
    post_id: str
    alt: str

    @property
    def image_url(self) -> str:
        return f"/static/img/{self.post_id}.jpg"

    @property
    def source_url(self) -> str:
        return f"https://www.instagram.com/wed_studiozs/p/{self.post_id}/"


STORIES = (
    JournalStory(
        "temple-diaries", "Temple diaries", PortfolioCategory.PRE_WEDDINGS,
        "A quiet beginning, framed by temple stone. A pre-wedding story from our journal.",
        "DZPAihNH5lW",
        "A couple in traditional dress sitting together on temple steps.",
    ),
    JournalStory(
        "swaroop-and-gayatri", "Swaroop & Gayatri", PortfolioCategory.PRE_WEDDINGS,
        "Ivory dreams and temple whispers. A collection of moments with Swaroop and Gayatri.",
        "DbLMpWDHwcu",
        "Swaroop and Gayatri in ivory outfits, photographed among temple archways.",
    ),
    JournalStory(
        "a-new-core-memory", "A new core memory", PortfolioCategory.ENGAGEMENTS,
        "The closeness, the anticipation, the beginning. An engagement story from our journal.",
        "DZXbzQLnxeO",
        "An engagement portrait collage showing a couple smiling together.",
    ),
    JournalStory(
        "snehas-wedding", "Sneha's wedding", PortfolioCategory.WEDDINGS,
        "Golden jewellery, a vibrant saree, and Sneha's joyful wedding-day smiles.",
        "DWG0OP8khUz",
        "Sneha wearing a purple and gold saree in a series of bridal portraits.",
    ),
    JournalStory(
        "ethereal-connection", "Ethereal connection", PortfolioCategory.WEDDINGS,
        "Two people, one frame. An intimate portrait from the WED STUDIOZS journal.",
        "DWD4g5WEfLX",
        "A couple leaning close together in warm evening light.",
    ),
)


def find_story(slug: str) -> JournalStory | None:
    return next((story for story in STORIES if story.slug == slug), None)


def filter_stories(category: PortfolioCategory | None, query: str) -> list[JournalStory]:
    search = query.casefold()
    return [
        story for story in STORIES
        if (category is None or story.category == category)
        and search in f"{story.title} {story.description}".casefold()
    ]
