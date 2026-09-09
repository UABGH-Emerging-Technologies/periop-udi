import re
from pathlib import Path

import jinja2


_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def _render(smart, base_url="http://localhost:8090"):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["url_for"] = lambda *args, **kwargs: "/"
    return env.get_template("home.html").render(
        smart=smart, base_url=base_url
    )


def _hero_row(html):
    match = re.search(
        r'<div class="flex flex-wrap items-center gap-3">(.*?)</div>',
        html,
        re.DOTALL,
    )
    assert match, "hero button row not found in rendered template"
    return match.group(1)


def test_hero_launches_smart_when_no_session():
    html = _render(smart=None)
    row = _hero_row(html)

    launch_tag = re.search(r'<a [^>]*href="/launch/standalone"[^>]*>', row)
    assert launch_tag, "expected /launch/standalone anchor in the hero row"
    assert "btn btn-primary" in launch_tag.group(0)
    assert "Launch from SMART sandbox" in row

    assert "Opens the public SMART Health IT sandbox" in html
    assert re.search(
        r'<p class="text-\[13px\] mt-3"\s+style="color: var\(--ink-3\);">',
        html,
    )

    assert 'href="/patients"' not in row


def test_hero_scans_for_patient_when_ehr_session_active():
    html = _render(
        smart={"patient": "1602", "patient_name": "Amy Shaw"}
    )
    row = _hero_row(html)

    assert "Scan a device into Amy Shaw's chart" in row
    assert "/patient/1602/timeline" in row
    assert "Launch from SMART sandbox" not in row
