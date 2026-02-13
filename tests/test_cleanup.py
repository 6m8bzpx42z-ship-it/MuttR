"""Tests for muttr.cleanup — proper nouns, lists, paragraphs, slider levels."""

import pytest
from muttr.cleanup import (
    clean_text,
    add_proper_nouns,
    CUSTOM_PROPER_NOUNS,
    _capitalize_proper_nouns,
    _process_paragraph_commands,
    _format_bullet_list,
    _format_numbered_list,
    _has_bullet_markers,
    _has_numbered_markers,
    _rebuild_proper_noun_map,
)


# ── helpers ──────────────────────────────────────────────────────────────────

class TestEmptyAndSafety:
    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none_input(self):
        assert clean_text(None) == ""

    def test_whitespace_only(self):
        assert clean_text("   ") == ""

    def test_safety_fallback_preserves_raw(self):
        """Cleaning should never produce empty output when raw has content."""
        result = clean_text("hello")
        assert result != ""

    def test_all_levels_accept_plain_text(self):
        for level in (0, 1, 2):
            result = clean_text("this is a test", level=level)
            assert "test" in result.lower()


# ── proper noun capitalization ───────────────────────────────────────────────

class TestProperNouns:
    def test_day_of_week(self):
        result = clean_text("i have a meeting on monday", level=0)
        assert "Monday" in result

    def test_month(self):
        result = clean_text("we are going in january", level=0)
        assert "January" in result

    def test_common_first_name(self):
        result = clean_text("i talked to sarah yesterday", level=0)
        assert "Sarah" in result

    def test_brand_iphone(self):
        result = clean_text("i just got a new iphone", level=0)
        assert "iPhone" in result

    def test_brand_macos(self):
        result = clean_text("i updated to the latest macos", level=0)
        assert "macOS" in result

    def test_brand_github(self):
        result = clean_text("push it to github", level=0)
        assert "GitHub" in result

    def test_brand_youtube(self):
        result = clean_text("i saw it on youtube", level=0)
        assert "YouTube" in result

    def test_country(self):
        result = clean_text("i traveled to japan last year", level=0)
        assert "Japan" in result

    def test_city(self):
        result = clean_text("we flew into tokyo", level=0)
        assert "Tokyo" in result

    def test_multi_word_place(self):
        result = clean_text("i live in new york", level=0)
        assert "New York" in result

    def test_multi_word_place_san_francisco(self):
        result = clean_text("the office is in san francisco", level=0)
        assert "San Francisco" in result

    def test_acronym_api(self):
        result = clean_text("we need to call the api", level=0)
        assert "API" in result

    def test_acronym_url(self):
        result = clean_text("send me the url", level=0)
        assert "URL" in result

    def test_tech_term_javascript(self):
        result = clean_text("it is written in javascript", level=0)
        assert "JavaScript" in result

    def test_wifi(self):
        result = clean_text("connect to the wifi", level=0)
        assert "Wi-Fi" in result

    def test_multiple_proper_nouns(self):
        result = clean_text("sarah went to london on monday", level=0)
        assert "Sarah" in result
        assert "London" in result
        assert "Monday" in result

    def test_proper_noun_at_sentence_start(self):
        result = clean_text("google announced a new product", level=0)
        assert "Google" in result

    def test_custom_proper_noun(self):
        add_proper_nouns({"muttr": "MuttR"})
        result = clean_text("i love using muttr", level=0)
        assert "MuttR" in result
        # Clean up
        CUSTOM_PROPER_NOUNS.clear()
        _rebuild_proper_noun_map()

    def test_preserves_already_correct_casing(self):
        result = clean_text("I love iPhone and macOS", level=0)
        assert "iPhone" in result
        assert "macOS" in result


# ── paragraph and line break commands ────────────────────────────────────────

class TestParagraphCommands:
    def test_new_paragraph(self):
        result = clean_text("first sentence new paragraph second sentence", level=0)
        assert "\n\n" in result
        assert "First sentence" in result

    def test_next_paragraph(self):
        result = clean_text("first part next paragraph second part", level=0)
        assert "\n\n" in result

    def test_new_line(self):
        result = clean_text("line one new line line two", level=0)
        assert "\n" in result

    def test_next_line(self):
        result = clean_text("line one next line line two", level=0)
        assert "\n" in result

    def test_period_new_paragraph(self):
        result = clean_text("end of sentence period new paragraph start of next", level=0)
        assert ".\n\n" in result

    def test_multiple_paragraph_breaks(self):
        result = clean_text(
            "paragraph one new paragraph paragraph two new paragraph paragraph three",
            level=0,
        )
        parts = result.split("\n\n")
        assert len(parts) >= 3


# ── bullet list formatting ───────────────────────────────────────────────────

class TestBulletLists:
    def test_bullet_point_pattern(self):
        text = "here are my items bullet point one apples bullet point two bananas bullet point three oranges"
        result = clean_text(text, level=1)
        assert "- Apples" in result
        assert "- Bananas" in result
        assert "- Oranges" in result

    def test_bullet_without_point(self):
        text = "my list bullet apples bullet bananas bullet oranges"
        result = clean_text(text, level=1)
        assert "- " in result

    def test_dash_pattern(self):
        text = "the items are dash apples dash bananas dash oranges"
        result = clean_text(text, level=1)
        assert "- " in result

    def test_next_item_pattern(self):
        text = "bullet apples bullet bananas next item oranges"
        result = clean_text(text, level=1)
        lines = [l for l in result.strip().split("\n") if l.strip()]
        assert len(lines) >= 2

    def test_bullet_list_not_at_light_level(self):
        text = "bullet point one apples bullet point two bananas"
        result_light = clean_text(text, level=0)
        # At light level, bullet markers are left as-is text
        assert "- Apples" not in result_light

    def test_single_bullet_not_formatted_as_list(self):
        text = "this is a bullet proof vest"
        result = clean_text(text, level=1)
        # Should not be turned into a list
        assert "- " not in result

    def test_has_bullet_markers_detection(self):
        assert _has_bullet_markers("bullet point one apples bullet point two bananas")
        assert not _has_bullet_markers("this is normal text")


# ── numbered list formatting ─────────────────────────────────────────────────

class TestNumberedLists:
    def test_number_word_pattern(self):
        text = "number one apples number two bananas number three oranges"
        result = clean_text(text, level=1)
        assert "1. Apples" in result
        assert "2. Bananas" in result
        assert "3. Oranges" in result

    def test_number_digit_pattern(self):
        text = "number 1 apples number 2 bananas number 3 oranges"
        result = clean_text(text, level=1)
        assert "1. Apples" in result
        assert "2. Bananas" in result

    def test_ordinal_pattern(self):
        text = "first go to the store second buy some milk third come home"
        result = clean_text(text, level=1)
        assert "1." in result
        assert "2." in result
        assert "3." in result

    def test_cardinal_paren_pattern(self):
        text = "one) go to the store two) buy some milk three) come home"
        result = clean_text(text, level=1)
        assert "1." in result
        assert "2." in result

    def test_digit_dot_pattern(self):
        text = "1. go to the store 2. buy some milk 3. come home"
        result = clean_text(text, level=1)
        assert "1." in result
        assert "2." in result
        assert "3." in result

    def test_numbered_list_not_at_light_level(self):
        text = "number one apples number two bananas"
        result = clean_text(text, level=0)
        # At light level, markers are left as text
        assert "1. Apples" not in result

    def test_has_numbered_markers_detection(self):
        assert _has_numbered_markers("number one apples number two bananas")
        assert _has_numbered_markers("first apples second bananas")
        assert not _has_numbered_markers("this is normal text")

    def test_numbered_list_with_preamble(self):
        text = "here are the steps number one apples number two bananas"
        result = clean_text(text, level=1)
        assert "1. Apples" in result
        assert "2. Bananas" in result


# ── slider levels ────────────────────────────────────────────────────────────

class TestSliderLevels:
    def test_level_0_light(self):
        text = "  the  the  cat sat  on   the mat  "
        result = clean_text(text, level=0)
        # Repeated words removed, whitespace normalized
        assert "the the" not in result.lower()
        assert "  " not in result  # no double spaces in non-newline context

    def test_level_0_keeps_fillers(self):
        text = "i was um thinking about it"
        result = clean_text(text, level=0)
        # Light level should keep fillers
        assert "um" in result.lower()

    def test_level_1_removes_fillers(self):
        text = "i was um thinking about it"
        result = clean_text(text, level=1)
        assert "um" not in result.lower()

    def test_level_1_removes_you_know(self):
        text = "it was you know really good"
        result = clean_text(text, level=1)
        assert "you know" not in result.lower()

    def test_level_2_removes_false_starts(self):
        text = "i was i was going to the store"
        result = clean_text(text, level=2)
        # Should only appear once
        count = result.lower().count("i was")
        assert count == 1

    def test_level_2_punctuation_smoothing(self):
        text = "hello..  world"
        result = clean_text(text, level=2)
        assert ".." not in result

    def test_level_clamp_negative(self):
        result = clean_text("hello world", level=-1)
        assert result  # Should not crash, treated as 0

    def test_level_clamp_high(self):
        result = clean_text("hello world", level=5)
        assert result  # Should not crash, treated as 2


# ── sentence casing and punctuation ──────────────────────────────────────────

class TestSentenceCasing:
    def test_first_letter_capitalized(self):
        result = clean_text("hello world", level=0)
        assert result[0] == "H"

    def test_terminal_punctuation_added(self):
        result = clean_text("hello world", level=0)
        assert result.endswith(".")

    def test_existing_punctuation_preserved(self):
        result = clean_text("is it working?", level=0)
        assert result.endswith("?")
        assert not result.endswith("?.")

    def test_exclamation_preserved(self):
        result = clean_text("wow that is great!", level=0)
        assert result.endswith("!")

    def test_sentence_case_after_period(self):
        result = clean_text("first sentence. second sentence", level=0)
        # After the period, 's' should be capitalized
        assert "Second" in result or "second" not in result.split(". ")[1][0]


# ── URL / email preservation ─────────────────────────────────────────────────

class TestPreservation:
    def test_url_preserved(self):
        text = "check out https://example.com/path for info"
        result = clean_text(text, level=2)
        assert "https://example.com/path" in result

    def test_email_preserved(self):
        text = "send it to user@example.com please"
        result = clean_text(text, level=2)
        assert "user@example.com" in result

    def test_backtick_code_preserved(self):
        text = "run the command `git push origin main` to deploy"
        result = clean_text(text, level=2)
        assert "`git push origin main`" in result


# ── mixed formatting scenarios ───────────────────────────────────────────────

class TestMixedFormatting:
    def test_proper_nouns_with_fillers_moderate(self):
        text = "um i talked to sarah about um the iphone on monday"
        result = clean_text(text, level=1)
        assert "Sarah" in result
        assert "iPhone" in result
        assert "Monday" in result
        assert "um" not in result.lower()

    def test_paragraph_with_proper_nouns(self):
        text = "i went to london new paragraph then i flew to tokyo"
        result = clean_text(text, level=0)
        assert "London" in result
        assert "\n\n" in result
        assert "Tokyo" in result

    def test_bullet_list_with_proper_nouns(self):
        text = "my destinations bullet point one london bullet point two tokyo bullet point three paris"
        result = clean_text(text, level=1)
        assert "London" in result
        assert "Tokyo" in result
        assert "Paris" in result

    def test_numbered_list_with_fillers(self):
        text = "number one um go to the store number two uh buy milk number three come home"
        result = clean_text(text, level=1)
        assert "1." in result
        assert "2." in result
        assert "3." in result
        assert "um" not in result.lower()
        assert "uh" not in result.lower()

    def test_aggressive_with_lists_and_proper_nouns(self):
        text = "i was i was saying number one go to google number two check github"
        result = clean_text(text, level=2)
        assert "Google" in result
        assert "GitHub" in result
        assert "1." in result

    def test_url_in_bullet_list(self):
        text = "bullet point one check https://example.com bullet point two check https://other.com"
        result = clean_text(text, level=1)
        assert "https://example.com" in result
        assert "https://other.com" in result

    def test_real_world_dictation(self):
        """Simulate a realistic dictation scenario."""
        text = (
            "um so basically i need to send an email to sarah about the meeting "
            "on monday new paragraph the agenda is number one discuss the iphone "
            "app number two review the github pull requests number three plan the "
            "trip to san francisco"
        )
        result = clean_text(text, level=2)
        assert "Sarah" in result
        assert "Monday" in result
        assert "\n\n" in result
        assert "iPhone" in result
        assert "GitHub" in result
        assert "San Francisco" in result
        assert "1." in result
        assert "um" not in result.lower()
        assert "basically" not in result.lower()


# ── edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_only_fillers(self):
        text = "um uh like you know"
        result = clean_text(text, level=1)
        # Safety fallback: should return something, not empty
        assert result != ""

    def test_single_word(self):
        result = clean_text("hello", level=1)
        assert result == "Hello."

    def test_already_clean_text(self):
        text = "This is already clean text."
        result = clean_text(text, level=1)
        assert result == "This is already clean text."

    def test_very_long_text(self):
        text = " ".join(["word"] * 500)
        result = clean_text(text, level=2)
        assert len(result) > 0

    def test_mixed_case_proper_nouns(self):
        result = clean_text("GOOGLE is big and so is APPLE", level=0)
        assert "Google" in result

    def test_numbers_in_text_not_confused_with_lists(self):
        text = "i have 3 cats and 2 dogs"
        result = clean_text(text, level=1)
        # Should not be formatted as a list
        assert "1." not in result
        assert "- " not in result

    def test_default_level_is_moderate(self):
        text = "um hello world"
        result = clean_text(text)  # No level specified
        # Default level 1 should remove fillers
        assert "um" not in result.lower()
