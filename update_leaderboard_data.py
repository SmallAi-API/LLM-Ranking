import argparse
import json
import re
import time
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ARENA_BASE_URL = "https://arena.ai"
CATALOG_BASE_URL = "https://raw.githubusercontent.com/lmarena/arena-catalog/main/data"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TEXT_CATEGORY_SLUGS = {
    "chinese": "chinese",
    "coding": "coding",
    "creative_writing": "creative-writing",
    "english": "english",
    "expert": "expert",
    "french": "french",
    "full": "overall",
    "german": "german",
    "hard_6": "hard-prompts",
    "hard_english_6": "hard-prompts-english",
    "if": "instruction-following",
    "industry_business_and_management_and_financial_operations": (
        "industry-business-and-management-and-financial-operations"
    ),
    "industry_entertainment_and_sports_and_media": "industry-entertainment-and-sports-and-media",
    "industry_legal_and_government": "industry-legal-and-government",
    "industry_life_and_physical_and_social_science": "industry-life-and-physical-and-social-science",
    "industry_mathematical": "industry-mathematical",
    "industry_medicine_and_healthcare": "industry-medicine-and-healthcare",
    "industry_software_and_it_services": "industry-software-and-it-services",
    "industry_writing_and_literature_and_language": "industry-writing-and-literature-and-language",
    "japanese": "japanese",
    "korean": "korean",
    "long_user": "longer-query",
    "math": "math",
    "multiturn": "multi-turn",
    "no_tie": "exclude-ties",
    "russian": "russian",
    "spanish": "spanish",
}

VISION_CATEGORY_SLUGS = {
    "captioning": "captioning",
    "chinese": "chinese",
    "creative_writing_vision": "creative-writing",
    "diagram": "diagram",
    "english": "english",
    "entity_recognition": "entity-recognition",
    "full": "overall",
    "homework": "homework",
    "humor": "humor",
    "ocr": "ocr",
}

IMAGE_CATEGORY_SLUGS = {"full": "overall"}

FILE_SPECS = {
    "leaderboard-text.json": ("text", TEXT_CATEGORY_SLUGS, False),
    "leaderboard-text-style-control.json": ("text", TEXT_CATEGORY_SLUGS, True),
    "leaderboard-vision.json": ("vision", VISION_CATEGORY_SLUGS, False),
    "leaderboard-vision-style-control.json": ("vision", VISION_CATEGORY_SLUGS, True),
    "leaderboard-image.json": ("text-to-image", IMAGE_CATEGORY_SLUGS, None),
}


def http_get_text(url, timeout=75, retries=3):
    last_error = None
    for attempt in range(retries):
        request = Request(url, headers=BROWSER_HEADERS)
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Request failed after {retries} retries: {url} ({last_error})")


def fetch_catalog_json(filename):
    text = http_get_text(f"{CATALOG_BASE_URL}/{filename}", timeout=60, retries=2)
    return json.loads(text)


def load_base_data(data_dir, filename):
    local_path = data_dir / filename
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return fetch_catalog_json(filename)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def strip_tags(text):
    without_tags = re.sub(r"<[^>]+>", " ", text, flags=re.S)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def parse_rating_cell(cell_text):
    numbers = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", cell_text)
    if not numbers:
        raise ValueError(f"No rating number parsed from: {cell_text!r}")

    rating = float(numbers[0].replace(",", ""))
    uncertainty = float(numbers[1].replace(",", "")) if len(numbers) > 1 else 0.0
    return rating, uncertainty


def parse_leaderboard_table(html):
    parsed = {}
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", html, flags=re.S | re.I)
    for row in rows:
        cells = re.findall(r"<td\b[^>]*>.*?</td>", row, flags=re.S | re.I)
        if len(cells) < 4:
            continue

        model_match = re.search(r"<a\b[^>]*\btitle=(['\"])(.*?)\1", row, flags=re.S | re.I)
        if not model_match:
            continue

        model_name = unescape(model_match.group(2)).strip()
        if not model_name:
            continue

        rating_text = strip_tags(cells[3])
        rating, uncertainty = parse_rating_cell(rating_text)
        parsed[model_name] = {
            "rating": rating,
            "rating_q975": rating + uncertainty,
            "rating_q025": rating - uncertainty,
        }

    if not parsed:
        raise RuntimeError("Parsed 0 models from leaderboard table.")
    return parsed


def build_leaderboard_path(modality, category_slug, style_control):
    if style_control is None:
        return f"/leaderboard/{modality}/{category_slug}"
    if style_control:
        return f"/leaderboard/{modality}/{category_slug}"
    return f"/leaderboard/{modality}/{category_slug}-no-style-control"


def refresh_categories(target_data, modality, category_map, style_control):
    updated = []
    skipped = []
    for output_key, category_slug in category_map.items():
        path = build_leaderboard_path(modality, category_slug, style_control)
        url = f"{ARENA_BASE_URL}{path}"
        try:
            html = http_get_text(url)
            if "<table" not in html.lower():
                raise RuntimeError("No table in response")
            target_data[output_key] = parse_leaderboard_table(html)
            updated.append(output_key)
        except Exception as exc:
            skipped.append((output_key, str(exc)))
    return updated, skipped


def update_all_files(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    all_skipped = []

    for filename, (modality, category_map, style_control) in FILE_SPECS.items():
        base_data = load_base_data(data_dir, filename)
        updated, skipped = refresh_categories(base_data, modality, category_map, style_control)
        write_json(data_dir / filename, base_data)
        print(f"{filename}: updated {len(updated)} categories")
        all_skipped.extend((filename, key, reason) for key, reason in skipped)

    if all_skipped:
        print("Skipped categories (kept existing values):")
        for filename, key, reason in all_skipped:
            print(f"- {filename} -> {key}: {reason}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Update leaderboard JSON files in data/ using live arena.ai pages."
    )
    parser.add_argument("--data-dir", default="data", help="Output directory (default: data)")
    return parser.parse_args()


def main():
    args = parse_args()
    update_all_files(Path(args.data_dir))
    print("Done. Source: arena.ai live pages.")


if __name__ == "__main__":
    main()
