"""See https://github.com/web-arena-x/webarena
"""
from __future__ import annotations

import re

from playwright.async_api import BrowserContext, Page


async def get_accessibility_tree(page: Page):
    cdp_session = await get_page_cdp_session(page)
    resp = await cdp_session.send("Accessibility.getFullAXTree")

    seen_ids = set()
    accessibility_tree = []
    for node in resp["nodes"]:
        if node["nodeId"] not in seen_ids:
            accessibility_tree.append(node)
            seen_ids.add(node["nodeId"])
    return accessibility_tree


async def execute_step(step: str, page: Page, browser_ctx: BrowserContext, accessibility_tree: list):
    step = step.strip()
    func = step.split("[")[0].strip() if "[" in step else step.split()[0].strip()
    if func == "None":
        return ""
    elif func == "click":
        match = re.search(r"click ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid click action {step}")
        element_id = match.group(1)
        await click_element(page, get_backend_node_id(element_id, accessibility_tree))
    elif func == "hover":
        match = re.search(r"hover ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid hover action {step}")
        element_id = match.group(1)
        await hover_element(page, get_backend_node_id(element_id, accessibility_tree))
    elif func == "type":
        # add default enter flag
        if not (step.endswith("[0]") or step.endswith("[1]")):
            step += " [1]"

        match = re.search(r"type ?\[(\d+)\] ?\[(.+)\] ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid type action {step}")
        element_id, text, enter_flag = (
            match.group(1),
            match.group(2),
            match.group(3),
        )
        if enter_flag == "1":
            text += "\n"
        await click_element(page, get_backend_node_id(element_id, accessibility_tree))
        await type_text(page, text)
    elif func == "press":
        match = re.search(r"press ?\[(.+)\]", step)
        if not match:
            raise ValueError(f"Invalid press action {step}")
        key = match.group(1)
        await key_press(page, key)
    elif func == "scroll":
        # up or down
        match = re.search(r"scroll ?\[?(up|down)\]?", step)
        if not match:
            raise ValueError(f"Invalid scroll action {step}")
        direction = match.group(1)
        await scroll_page(page, direction)
    elif func == "goto":
        match = re.search(r"goto ?\[(.+)\]", step)
        if not match:
            raise ValueError(f"Invalid goto action {step}")
        url = match.group(1)
        await page.goto(url)
    elif func == "new_tab":
        page = await browser_ctx.new_page()
    elif func == "go_back":
        await page.go_back()
    elif func == "go_forward":
        await page.go_forward()
    elif func == "tab_focus":
        match = re.search(r"tab_focus ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid tab_focus action {step}")
        page_number = int(match.group(1))
        page = browser_ctx.pages[page_number]
        await page.bring_to_front()
    elif func == "close_tab":
        await page.close()
        if len(browser_ctx.pages) > 0:
            page = browser_ctx.pages[-1]
        else:
            page = await browser_ctx.new_page()
    elif func == "stop":
        match = re.search(r'stop\(?"(.+)?"\)', step)
        answer = match.group(1) if match else ""
        return answer
    else:
        raise ValueError
    await page.wait_for_load_state("domcontentloaded")
    return page


async def type_text(page: Page, text: str):
    await page.keyboard.type(text)


async def click_element(page: Page, backend_node_id: int):
    cdp_session = await get_page_cdp_session(page)
    resp = await get_bounding_rect(cdp_session, backend_node_id)
    node_info = resp["result"]["value"]
    x, y = await get_element_center(node_info)
    # Move to the location of the element
    await page.evaluate(f"window.scrollTo({x}- window.innerWidth/2,{y} - window.innerHeight/2);")
    # Refresh the relative location of the element
    resp = await get_bounding_rect(cdp_session, backend_node_id)
    node_info = resp["result"]["value"]
    x, y = await get_element_center(node_info)
    await page.mouse.click(x, y)


async def hover_element(page: Page, backend_node_id: int) -> None:
    cdp_session = await get_page_cdp_session(page)
    resp = await get_bounding_rect(cdp_session, backend_node_id)
    node_info = resp["result"]["value"]
    x, y = await get_element_center(node_info)
    await page.mouse.move(x, y)


async def scroll_page(page: Page, direction: str) -> None:
    # perform the action
    # code from natbot
    if direction == "up":
        await page.evaluate(
            "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop - window.innerHeight;"
        )
    elif direction == "down":
        await page.evaluate(
            "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop + window.innerHeight;"
        )


async def key_press(page: Page, key: str) -> None:
    """Press a key."""
    if "Meta" in key and "Mac" not in await page.evaluate("navigator.platform"):
        key = key.replace("Meta", "Control")
    await page.keyboard.press(key)


async def get_element_outer_html(page: Page, backend_node_id: int):
    cdp_session = await get_page_cdp_session(page)
    try:
        outer_html = await cdp_session.send("DOM.getOuterHTML", {"backendNodeId": int(backend_node_id)})
        return outer_html["outerHTML"]
    except Exception as e:
        raise ValueError("Element not found") from e


async def get_element_center(node_info):
    x, y, width, height = node_info["x"], node_info["y"], node_info["width"], node_info["height"]
    center_x = x + width / 2
    center_y = y + height / 2
    return center_x, center_y


def extract_step(response: str, action_splitter: str = "```") -> str:
    # find the first occurence of action
    pattern = rf"{action_splitter}((.|\n)*?){action_splitter}"
    match = re.search(pattern, response)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError(f'Cannot find the answer phrase "{response}"')


async def get_bounding_rect(cdp_session, backend_node_id: str):
    try:
        remote_object = await cdp_session.send("DOM.resolveNode", {"backendNodeId": int(backend_node_id)})
        remote_object_id = remote_object["object"]["objectId"]
        response = await cdp_session.send(
            "Runtime.callFunctionOn",
            {
                "objectId": remote_object_id,
                "functionDeclaration": """
                    function() {
                        if (this.nodeType == 3) {
                            var range = document.createRange();
                            range.selectNode(this);
                            var rect = range.getBoundingClientRect().toJSON();
                            range.detach();
                            return rect;
                        } else {
                            return this.getBoundingClientRect().toJSON();
                        }
                    }
                """,
                "returnByValue": True,
            },
        )
        return response
    except Exception as e:
        raise ValueError("Element not found") from e


IGNORED_ACTREE_PROPERTIES = (
    "focusable",
    "editable",
    "readonly",
    "level",
    "settable",
    "multiline",
    "invalid",
)


def parse_accessibility_tree(accessibility_tree):
    """Parse the accessibility tree into a string text"""
    node_id_to_idx = {}
    for idx, node in enumerate(accessibility_tree):
        node_id_to_idx[node["nodeId"]] = idx

    obs_nodes_info = {}

    def dfs(idx: int, obs_node_id: str, depth: int) -> str:
        tree_str = ""
        node = accessibility_tree[idx]
        indent = "\t" * depth
        valid_node = True
        try:
            role = node["role"]["value"]
            name = node["name"]["value"]
            node_str = f"[{obs_node_id}] {role} {repr(name)}"
            properties = []
            for property in node.get("properties", []):
                try:
                    if property["name"] in IGNORED_ACTREE_PROPERTIES:
                        continue
                    properties.append(f'{property["name"]}: {property["value"]["value"]}')
                except KeyError:
                    pass

            if properties:
                node_str += " " + " ".join(properties)

            # check valid
            if not node_str.strip():
                valid_node = False

            # empty generic node
            if not name.strip():
                if not properties:
                    if role in [
                        "generic",
                        "img",
                        "list",
                        "strong",
                        "paragraph",
                        "banner",
                        "navigation",
                        "Section",
                        "LabelText",
                        "Legend",
                        "listitem",
                    ]:
                        valid_node = False
                elif role in ["listitem"]:
                    valid_node = False

            if valid_node:
                tree_str += f"{indent}{node_str}"
                obs_nodes_info[obs_node_id] = {
                    "backend_id": node["backendDOMNodeId"],
                    "union_bound": node["union_bound"],
                    "text": node_str,
                }

        except Exception:
            valid_node = False

        for _, child_node_id in enumerate(node["childIds"]):
            if child_node_id not in node_id_to_idx:
                continue
            # mark this to save some tokens
            child_depth = depth + 1 if valid_node else depth
            child_str = dfs(node_id_to_idx[child_node_id], child_node_id, child_depth)
            if child_str.strip():
                if tree_str.strip():
                    tree_str += "\n"
                tree_str += child_str

        return tree_str

    tree_str = dfs(0, accessibility_tree[0]["nodeId"], 0)
    return tree_str, obs_nodes_info


async def get_page_cdp_session(page):
    if hasattr(page, "cdp_session"):
        return page.cdp_session

    cdp_session = await page.context.new_cdp_session(page)
    page.cdp_session = cdp_session
    return cdp_session


def get_backend_node_id(element_id, accessibility_tree):
    element_id = str(element_id)
    for i in accessibility_tree:
        if i["nodeId"] == element_id:
            return i.get("backendDOMNodeId")
    raise ValueError(f"Element {element_id} not found")
