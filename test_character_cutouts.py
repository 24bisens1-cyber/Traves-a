from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "frontend" / "assets" / "character-scenes"
CHARACTERS = ("pikachu", "bulbasaur", "iron-man", "spider-man", "harry-potter", "hermione")


def test_uploaded_characters_keep_their_original_full_scene_backgrounds():
    for name in CHARACTERS:
        path = ASSET_DIR / f"{name}-scene.png"
        assert path.is_file(), f"missing original scene asset: {path}"
        image = Image.open(path).convert("RGBA")
        assert image.width >= 100 and image.height >= 100
        alpha = image.getchannel("A")
        assert alpha.getextrema() == (255, 255), f"{name} should keep its opaque original scene/background"


def test_friend_library_uses_full_scene_assets_not_transparent_cutouts():
    source = (ROOT / "frontend" / "friend-characters.js").read_text(encoding="utf-8")
    for name in CHARACTERS:
        assert f"{name}-scene.png" in source
        assert f"character-avatars/{name}.png" not in source


def test_character_scene_animation_preserves_full_image_with_contain_fit():
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    assert "--character-scene-image" in css
    assert "background-image:" in css and "var(--character-scene-image" in css
    assert "object-fit: contain !important" in css
    assert "cpFullSceneCamera" in css and "cpFullSceneBackdrop" in css and "cpFullSceneLightSweep" in css


def test_every_friend_and_picker_character_uses_one_uniform_square_stage():
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    assert "width: 104px !important" in css and "height: 104px !important" in css
    assert "width:92px !important" in css and "height:92px !important" in css
    assert ".split-person .split-avatar.has-character" in css
    assert ".friend-character-choice-art" in css


def test_all_thirteen_characters_have_individual_idle_animation_rules():
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    library = (ROOT / "frontend" / "friend-characters.js").read_text(encoding="utf-8")
    ids = ("pikachu", "bulbasaur", "iron-man", "spider-man", "harry-potter", "hermione", "bloop", "sprout", "pip", "roo", "mira", "orbit", "paws")
    for character_id in ids:
        assert f'id: "{character_id}"' in library
        assert f'data-character-id="{character_id}"' in css or f'[data-character-id="{character_id}"] img' in css
    for animation in ("cpScenePikachu", "cpSceneBulbasaur", "cpSceneIronMan", "cpSceneSpider", "cpSceneHarry", "cpSceneHermione", "cpSceneBloop", "cpSceneSprout", "cpScenePip", "cpSceneRoo", "cpSceneMira", "cpSceneOrbit", "cpScenePaws"):
        assert animation in css
