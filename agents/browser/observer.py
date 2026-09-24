"""
SHIVANI Page Observer
Gathers comprehensive, structured observations of the current browser page:
DOM layout, interactive elements, headings, visible text, and accessibility trees.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from playwright.async_api import Page


class PageState(str, Enum):
    LOADING = "LOADING"
    READY = "READY"
    NAVIGATING = "NAVIGATING"
    INTERACTING = "INTERACTING"
    WAITING = "WAITING"
    ERROR = "ERROR"


class PageElementInfo(BaseModel):
    element_type: str = Field(description="Type of control (e.g. 'button', 'input', 'link', 'select', 'heading')")
    element_id: Optional[str] = Field(default=None, description="HTML id attribute")
    text: str = Field(default="", description="Visible text or label")
    role: Optional[str] = Field(default=None, description="ARIA role if present")
    name: Optional[str] = Field(default=None, description="Name or identifier attribute")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text for inputs")
    input_type: Optional[str] = Field(default=None, description="HTML input type (e.g. 'text', 'password', 'search')")
    href: Optional[str] = Field(default=None, description="Target URL for hyperlinks")
    selector: Optional[str] = Field(default=None, description="Stable selector candidate")
    is_visible: bool = True
    is_enabled: bool = True


class PageObservation(BaseModel):
    url: str = Field(default="", description="Active page URL")
    title: str = Field(default="", description="Document title")
    state: PageState = PageState.READY
    headings: List[str] = Field(default_factory=list, description="List of h1, h2, h3 heading texts")
    visible_text: str = Field(default="", description="Cleaned visible textual content")
    elements: List[PageElementInfo] = Field(default_factory=list, description="Interactive UI elements")
    forms: List[Dict[str, Any]] = Field(default_factory=list, description="Detected web forms")
    meta_info: Dict[str, Any] = Field(default_factory=dict, description="Additional page metadata")


class PageObserver:
    """Inspects Playwright Page instances to extract structured observations."""

    async def observe(self, page: Page, max_elements: int = 50) -> PageObservation:
        """Collects structured observation data from active Playwright page."""
        try:
            url = page.url
            title = await page.title()
        except Exception:
            return PageObservation(state=PageState.ERROR)

        # Extract headings, clean text, and interactive elements using JavaScript in page context
        extraction_script = """() => {
            const result = {
                headings: [],
                visibleText: '',
                elements: [],
                forms: []
            };

            // Headings
            document.querySelectorAll('h1, h2, h3').forEach(h => {
                const txt = h.innerText?.trim();
                if (txt) result.headings.push(txt);
            });

            // Extract main text snippet
            const bodyClone = document.body.cloneNode(true);
            const scripts = bodyClone.querySelectorAll('script, style, noscript, nav, footer, header');
            scripts.forEach(s => s.remove());
            result.visibleText = (bodyClone.innerText || '').slice(0, 3000).replace(/\\s+/g, ' ').trim();

            // Interactive Buttons
            document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"], a.btn').forEach((btn, idx) => {
                if (idx < 25 && btn.offsetParent !== null) {
                    result.elements.push({
                        element_type: 'button',
                        element_id: btn.id || null,
                        text: btn.innerText?.trim() || btn.getAttribute('value') || btn.getAttribute('aria-label') || '',
                        role: btn.getAttribute('role') || 'button',
                        name: btn.getAttribute('name') || btn.id || null,
                        selector: btn.id ? '#' + btn.id : (btn.className ? '.' + btn.className.split(' ')[0] : null)
                    });
                }
            });

            // Inputs & Textareas
            document.querySelectorAll('input:not([type="hidden"]), textarea').forEach((inp, idx) => {
                if (idx < 20 && inp.offsetParent !== null) {
                    const labelElem = inp.labels && inp.labels[0];
                    result.elements.push({
                        element_type: 'input',
                        element_id: inp.id || null,
                        input_type: inp.getAttribute('type') || 'text',
                        placeholder: inp.getAttribute('placeholder') || null,
                        name: inp.getAttribute('name') || inp.id || null,
                        text: labelElem ? labelElem.innerText?.trim() : (inp.getAttribute('aria-label') || ''),
                        role: inp.getAttribute('role') || 'textbox',
                        selector: inp.id ? '#' + inp.id : (inp.name ? `input[name="${inp.name}"]` : null)
                    });
                }
            });

            // Prominent Links
            document.querySelectorAll('a[href]').forEach((link, idx) => {
                const txt = link.innerText?.trim();
                if (idx < 25 && link.offsetParent !== null && txt && txt.length > 2) {
                    result.elements.push({
                        element_type: 'link',
                        element_id: link.id || null,
                        text: txt,
                        href: link.getAttribute('href') || null,
                        role: 'link',
                        selector: link.id ? '#' + link.id : null
                    });
                }
            });

            return result;
        }"""

        raw_data = {"headings": [], "visibleText": "", "elements": [], "forms": []}
        try:
            raw_data = await page.evaluate(extraction_script)
        except Exception:
            pass

        parsed_elements = []
        for e in raw_data.get("elements", [])[:max_elements]:
            parsed_elements.append(PageElementInfo(
                element_type=e.get("element_type", "unknown"),
                text=e.get("text", ""),
                role=e.get("role"),
                name=e.get("name"),
                placeholder=e.get("placeholder"),
                input_type=e.get("input_type"),
                href=e.get("href"),
                selector=e.get("selector")
            ))

        return PageObservation(
            url=url,
            title=title,
            state=PageState.READY,
            headings=raw_data.get("headings", [])[:10],
            visible_text=raw_data.get("visibleText", ""),
            elements=parsed_elements,
            forms=raw_data.get("forms", []),
            meta_info={"element_count": len(parsed_elements)}
        )
